from squirrelator import translate

def test_english_to_python():
    r = translate("print hello", "english", "python")
    assert "print" in r.lower()

def test_quickbasic_to_english():
    src = 'PRINT "Hi"'
    r = translate(src, "quickbasic", "english")
    assert "Print" in r

def test_unsupported():
    r = translate("hello", "klingon", "python")
    assert "Unsupported" in r

def test_loop():
    r = translate("count from 1 to 3", "english", "quickbasic")
    assert "FOR" in r
