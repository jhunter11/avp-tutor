"""ANTLR diagnostics only. This module never executes submitted code."""

from antlr4 import CommonTokenStream, InputStream, ParseTreeWalker
from antlr4.error.ErrorListener import ErrorListener

from PseudocodeLexer import PseudocodeLexer
from PseudocodeListener import PseudocodeListener
from PseudocodeParser import PseudocodeParser
from tutor.models import Diagnostic, ValidationResult


class Errors(ErrorListener):
    def __init__(self):
        self.items = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.items.append(Diagnostic(line=line, column=column + 1, message=msg))


class ScopeChecks(PseudocodeListener):
    def __init__(self):
        self.depth = 0
        self.names = set()
        self.items = []

    def enterFunctionDecl(self, ctx):
        name = ctx.ID().getText()
        parent = ctx.parentCtx
        grandparent = parent.parentCtx if parent is not None else None
        if self.depth or not isinstance(grandparent, PseudocodeParser.ProgramContext):
            self.items.append(
                Diagnostic(
                    line=ctx.start.line,
                    column=1,
                    code="nested-function",
                    message="The documented AVP language permits functions only at top level.",
                )
            )
        if name in self.names:
            self.items.append(
                Diagnostic(
                    line=ctx.start.line,
                    column=1,
                    code="duplicate-function",
                    message=f"Function {name} is defined more than once.",
                )
            )
        self.names.add(name)
        self.depth += 1

    def exitFunctionDecl(self, ctx):
        self.depth -= 1


def validate_avp(code: str) -> ValidationResult:
    errors = Errors()
    lexer = PseudocodeLexer(InputStream(code))
    lexer.removeErrorListeners()
    lexer.addErrorListener(errors)
    parser = PseudocodeParser(CommonTokenStream(lexer))
    parser.removeErrorListeners()
    parser.addErrorListener(errors)
    try:
        tree = parser.program()
    except RecursionError:
        errors.items.append(
            Diagnostic(
                line=1, column=1, message="Code nesting is too deep to validate."
            )
        )
        return ValidationResult(syntax_valid=False, diagnostics=errors.items)
    syntax_valid = not errors.items
    if syntax_valid:
        checks = ScopeChecks()
        try:
            ParseTreeWalker().walk(checks, tree)
            errors.items.extend(checks.items)
        except RecursionError:
            errors.items.append(
                Diagnostic(
                    line=1,
                    column=1,
                    code="nesting",
                    message="Code nesting is too deep to validate.",
                )
            )
    for line, text in enumerate(code.splitlines(), 1):
        prefix = text[: len(text) - len(text.lstrip())]
        if text.strip() and ("\t" in prefix or len(prefix) % 4):
            errors.items.append(
                Diagnostic(
                    line=line,
                    column=1,
                    code="indentation",
                    severity="warning",
                    message="Use spaces in multiples of four. The bundled grammar does not enforce indentation.",
                )
            )
    return ValidationResult(syntax_valid=syntax_valid, diagnostics=errors.items)
