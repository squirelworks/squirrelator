from squirrelator import translate

def test_unsupported():
    result = translate("hello", "klingon", "python")
    assert "Unsupported" in result

def test_scaffold_runs():
    result = translate("print hello", "english", "python")
    assert "squirrelator translation scaffold" in result
    assert "english" in result
    assert "python" in result
