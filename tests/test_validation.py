from tutor.validation import validate_avp


def test_valid_code():
    result = validate_avp("fun f(a):\n    return a + 1\nend fun\nx = f(2)")
    assert result.syntax_valid
    assert not result.execution_verified


def test_lexer_errors_are_not_silently_recovered():
    result = validate_avp("x = 4 % 2")
    assert not result.syntax_valid
    assert any(d.line == 1 for d in result.diagnostics)


def test_missing_terminator_and_nested_functions():
    assert not validate_avp("fun f():\n    return 1").syntax_valid
    result = validate_avp(
        "fun f():\n    fun g():\n        return 1\n    end fun\nend fun"
    )
    assert any(d.code == "nested-function" for d in result.diagnostics)


def test_tabs_are_reported_as_style_not_grammar_failure():
    result = validate_avp("fun f():\n\treturn 1\nend fun")
    assert result.syntax_valid
    assert any(d.code == "indentation" for d in result.diagnostics)


def test_function_inside_top_level_conditional_is_not_main_scope():
    result = validate_avp(
        "if (True):\n    fun inner():\n        return 1\n    end fun\nend if"
    )
    assert result.syntax_valid
    assert any(d.code == "nested-function" for d in result.diagnostics)
