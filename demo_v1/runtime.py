"""Bounded AVP teaching subset. No eval, host execution, I/O, or model execution."""

import hashlib
import json
import operator

from antlr4 import CommonTokenStream, InputStream

from PseudocodeLexer import PseudocodeLexer
from PseudocodeParser import PseudocodeParser
from tutor.models import ExecutionContext, ExecutionEvent
from tutor.validation import validate_avp


class DemoRuntimeError(ValueError):
    pass


class Returned(Exception):
    def __init__(self, value):
        self.value = value


class Runtime:
    """Execute one solution(array, target) function using the repository parser."""

    def __init__(self, code, values, target):
        self.code = code
        self.env = {}
        self.frames = []
        self.operations = 0
        self.array_reads = []
        self.loop_depth = 0
        self.values = values.copy()
        self.target = target
        self.digest = hashlib.sha256(code.encode()).hexdigest()
        self.run_digest = hashlib.sha256(
            json.dumps([self.digest, values, target]).encode()
        ).hexdigest()[:12]

    def tick(self):
        self.operations += 1
        if self.operations > 2000 or len(self.frames) >= 256:
            raise DemoRuntimeError(
                "Execution limit reached. Check that the loop makes progress."
            )

    def frame(self, ctx, kind, value=None, reads=None):
        line = ctx.start.line
        details = {"value": value} if value is not None else {}
        if reads is not None:
            details["array_reads"] = reads
        if kind == "return":
            details["loop_depth"] = self.loop_depth
        event = ExecutionEvent(
            kind=kind,
            line=line,
            description=f"Line {line}: {kind}."
            + (f" Value: {value}." if value is not None else ""),
            details=details,
        )
        self.frames.append(
            ExecutionContext(
                algorithm="linear_search",
                language_version="avp-demo-subset-v1",
                code_version=self.digest,
                code=self.code,
                current_line=line,
                phase="after",
                run_id=f"demo-{self.run_digest}",
                step=len(self.frames),
                variables={
                    k: v for k, v in self.env.items() if not isinstance(v, list)
                },
                arrays={
                    k: v.copy() for k, v in self.env.items() if isinstance(v, list)
                },
                recent_events=[event],
            )
        )

    def expression(self, ctx):
        self.tick()
        name = type(ctx).__name__.removesuffix("Context")
        if name in {
            "Expression",
            "OrPass",
            "AndPass",
            "ComparisonPass",
            "AdditivePass",
            "MultiplicativePass",
            "PowerPass",
            "UnaryPass",
            "AtomExpression",
        }:
            return self.expression(ctx.getChild(0))
        if name == "ParenExpression":
            return self.expression(ctx.expression())
        if name == "Atom":
            if ctx.INT():
                value = int(ctx.INT().getText())
                if abs(value) > 1_000_000:
                    raise DemoRuntimeError("Use integers between -1000000 and 1000000.")
                return value
            if ctx.ID():
                key = ctx.ID().getText()
                if key not in self.env:
                    raise DemoRuntimeError(f"Variable {key} has no value.")
                return self.env[key]
            if ctx.TRUE() or ctx.FALSE():
                return bool(ctx.TRUE())
            raise DemoRuntimeError(
                "This demo supports integer and Boolean literals only."
            )
        if name == "UnaryMinusExpr":
            return -self.scalar(self.expression(ctx.unaryExpression()))
        if name == "FunctionCallExpression":
            args = ctx.expressionList()
            if (
                ctx.ID().getText() != "length"
                or not args
                or len(args.expression()) != 1
            ):
                raise DemoRuntimeError("Only length(array) is available in this demo.")
            array = self.expression(args.expression(0))
            if not isinstance(array, list):
                raise DemoRuntimeError("length requires an array.")
            return len(array)
        if name == "ArrayAccessExpression":
            array = self.env.get(ctx.ID().getText())
            index = self.expression(ctx.expression())
            if (
                not isinstance(array, list)
                or type(index) is not int
                or not 0 <= index < len(array)
            ):
                raise DemoRuntimeError("Array index is outside the input bounds.")
            self.array_reads.append(
                {"array": ctx.ID().getText(), "index": index, "value": array[index]}
            )
            return array[index]
        if name in {"AndExpr", "OrExpr"}:
            parts = [ctx.getChild(i) for i in range(0, ctx.getChildCount(), 2)]
            return (
                all(bool(self.expression(p)) for p in parts)
                if name == "AndExpr"
                else any(bool(self.expression(p)) for p in parts)
            )
        if name in {"CompareExpr", "AddExpr"}:
            ops = {
                "==": operator.eq,
                "<": operator.lt,
                ">": operator.gt,
                "<=": operator.le,
                ">=": operator.ge,
                "+": operator.add,
                "-": operator.sub,
            }
            value = self.scalar(self.expression(ctx.getChild(0)))
            for i in range(1, ctx.getChildCount(), 2):
                op = ctx.getChild(i).getText()
                value = ops[op](
                    value, self.scalar(self.expression(ctx.getChild(i + 1)))
                )
                self.scalar(value)
            return value
        raise DemoRuntimeError(f"This expression is outside the demo subset: {name}.")

    @staticmethod
    def scalar(value):
        if type(value) not in {int, bool} or abs(value) > 1_000_000:
            raise DemoRuntimeError("Use bounded integer or Boolean values.")
        return value

    def statements(self, statements):
        for statement in statements:
            self.tick()
            if statement.annotation():
                raise DemoRuntimeError("Annotations are outside the demo subset.")
            if ctx := statement.assignment():
                if (
                    type(ctx.lvalue()).__name__ != "SimpleLvalueContext"
                    or ctx.arrayInitialization()
                ):
                    raise DemoRuntimeError("The input array is read-only in this demo.")
                self.env[ctx.lvalue().ID().getText()] = self.scalar(
                    self.expression(ctx.expression())
                )
                self.frame(ctx, "assignment")
            elif ctx := statement.compoundAssignment():
                name = ctx.lvalue().ID().getText()
                if (
                    type(ctx.lvalue()).__name__ != "SimpleLvalueContext"
                    or name not in self.env
                ):
                    raise DemoRuntimeError("Update an existing scalar variable.")
                op = ctx.getChild(1).getText()
                if op not in {"+=", "-="}:
                    raise DemoRuntimeError("Only += and -= updates are available.")
                value = self.expression(ctx.expression())
                self.env[name] = self.scalar(
                    self.scalar(self.env[name]) + (value if op == "+=" else -value)
                )
                self.frame(ctx, "update")
            elif ctx := statement.ifStatement():
                conditions, blocks = ctx.expression(), ctx.block()
                for i, condition in enumerate(conditions):
                    self.array_reads = []
                    result = bool(self.expression(condition))
                    self.frame(condition, "condition", result, self.array_reads.copy())
                    if result:
                        self.statements(blocks[i].statement())
                        break
                else:
                    if len(blocks) > len(conditions):
                        self.statements(blocks[-1].statement())
            elif ctx := statement.whileLoop():
                while True:
                    self.array_reads = []
                    result = bool(self.expression(ctx.expression()))
                    self.frame(ctx, "condition", result, self.array_reads.copy())
                    if not result:
                        break
                    self.loop_depth += 1
                    try:
                        self.statements(ctx.statement())
                    finally:
                        self.loop_depth -= 1
            elif ctx := statement.returnStatement():
                self.array_reads = []
                value = self.expression(ctx.expression())
                if type(value) is not int:
                    raise DemoRuntimeError("solution must return an integer index.")
                self.frame(ctx, "return", value, self.array_reads.copy())
                raise Returned(value)
            else:
                raise DemoRuntimeError(
                    "Use scalar assignments, while, if, return, and length in this demo."
                )

    def run(self):
        validation = validate_avp(self.code)
        if not validation.syntax_valid or any(
            d.severity == "error" for d in validation.diagnostics
        ):
            raise DemoRuntimeError(
                "AVP syntax error. "
                + "; ".join(
                    f"Line {d.line}: {d.message}" for d in validation.diagnostics[:3]
                )
            )
        lexer = PseudocodeLexer(InputStream(self.code))
        parser = PseudocodeParser(CommonTokenStream(lexer))
        tree = parser.program()
        statements = tree.statement()
        if len(statements) != 1 or not statements[0].functionDecl():
            raise DemoRuntimeError(
                "Provide one function: fun solution(values, target)."
            )
        fun = statements[0].functionDecl()
        params = fun.paramList().annotatedParam() if fun.paramList() else []
        if (
            fun.ID().getText() != "solution"
            or len(params) != 2
            or any(p.annotation() for p in params)
        ):
            raise DemoRuntimeError(
                "Provide one function: fun solution(values, target)."
            )
        names = [p.ID().getText() for p in params]
        if len(set(names)) != 2:
            raise DemoRuntimeError("Function parameters must have different names.")
        self.env = {names[0]: self.values, names[1]: self.target}
        try:
            self.statements(fun.statement())
        except Returned as result:
            return {
                "actual": result.value,
                "frames": [f.model_dump() for f in self.frames],
                "error": None,
            }
        raise DemoRuntimeError("solution finished without returning an index.")


def execute(code, values, target):
    runtime = Runtime(code, values, target)
    try:
        return runtime.run()
    except (DemoRuntimeError, RecursionError) as exc:
        return {
            "actual": None,
            "frames": [f.model_dump() for f in runtime.frames],
            "error": str(exc)
            if isinstance(exc, DemoRuntimeError)
            else "Code nesting is too deep.",
        }
