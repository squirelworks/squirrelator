"""Klingon and Latin through the pipeline from their inflection tables:
verbs that show their subject and object in their own form (Klingon
jI-, vI-, lu-), nouns that show their number (puqpu'), words only the
tables have (Latin nāvis), and reading the person a verb's form says
back as a pronoun (vIlegh is I see)."""

import pytest

from squirrelator import data
from squirrelator.inflections import inflections
from squirrelator.lexicon import lexicon
from squirrelator.pipeline import run

try:
    data.data_dir()
except data.DataNotFound:
    pytest.skip("squirrel-lang-data not checked out", allow_module_level=True)


@pytest.fixture
def klingon(root):
    if not inflections("klingon", root):
        pytest.skip("Klingon affix tables arrive in squirrel-lang-data v0.1.4")
    return root


@pytest.fixture
def latin_words(root):
    if not any(w.meaning == "ship" for w in inflections("latin", root)):
        pytest.skip("The new Latin words arrive in squirrel-lang-data v0.1.4")
    return root


def to_klingon(text, root):
    return run(text, "english", "klingon", root=root).text


@pytest.mark.parametrize("english, klingon_text", [
    ("We sleep.", "maQong"),                                     # ma-: we, no object
    ("You see the captain.", "HoD Dalegh"),                      # Da-: you, him; OVS
    ("They drink water.", "bIQ lutlhutlh"),                      # lu-: they, it
    ("The officers see the ships.", "Dujmey lulegh yaSpu'"),     # -mey, -pu'
    ("The children eat.", "Sop puqpu'"),                         # subject last
    ("We ate food.", "Soj wISoppu'"),                            # -pu' for the past
])
def test_klingon_verbs_take_their_subject_and_object(klingon, english, klingon_text):
    assert to_klingon(english, klingon) == klingon_text


def test_klingon_subject_pronoun_is_left_to_the_prefix(klingon):
    out = to_klingon("We sleep.", klingon)
    assert "maH" not in out and out == "maQong"


def test_klingon_place_is_a_noun_form(klingon):
    out = to_klingon("The child sleeps in the ship.", klingon)
    assert "DujDaq" in out.split()


def test_english_not_finds_the_klingon_suffix(klingon):
    # English "not" is none or not; Klingon has a word only for not.
    assert to_klingon("I do not understand.", klingon).endswith("be'")


def test_bare_klingon_jatlh_is_third_person_in_latin(klingon):
    # The word list writes jatlh with no person. Every table form spelled
    # that way is third person, so Latin is loquitur, not the dictionary loquor.
    assert run('jatlh "nuqneH"', "klingon", "latin", root=klingon).text == "Loquitur salvē."
    assert run("jatlh", "klingon", "latin", root=klingon).text == "Loquitur."
    assert run("jIjatlh", "klingon", "latin", root=klingon).text == "Loquor."


@pytest.mark.parametrize("klingon_text, english", [
    ("Duj vIlegh", "I see the ship."),
    ("maSuv", "We fight."),
    ("Dujmey legh yaSpu'", "Officers see ships."),
])
def test_reading_klingon_finds_the_subject_in_the_verb(klingon, klingon_text, english):
    assert run(klingon_text, "klingon", "english", root=klingon).text == english


def test_klingon_perfective_is_read_as_the_past(klingon):
    r = run("jIQongpu'", "klingon", "english", root=klingon)
    # The matrix row is present tense, so the note says so and the past
    # wording is the next candidate.
    assert "@past" in r.breakdown[0].why and "I slept." in r.alternatives


def test_person_is_agreement_not_a_grammar_mismatch(klingon):
    r = run("Duj vIlegh", "klingon", "english", root=klingon)
    assert r.breakdown[0].why == "A sentence from the meaning matrix."


@pytest.mark.parametrize("english, latin", [
    ("I see the ship.", "Videō nāvem."),
    ("The officers see the ships.", "Praefectī vident nāvēs."),
    ("I eat food.", "Comedō cibum."),
    ("The officer saw the child.", "Puerum praefectus vīdit."),
])
def test_latin_words_only_the_tables_have(latin_words, english, latin):
    r = run(english, "english", "latin", root=latin_words)
    assert r.text == latin and not r.unknown


def test_latin_verb_form_gives_its_pronoun_back(latin_words):
    assert run("Nāvem vīdī.", "latin", "english", root=latin_words).text == "I see the ship."
    assert run("Locūtus sum.", "latin", "english", root=latin_words).text == "I spoke."


def test_english_past_forms_keep_their_tense(root):
    if not inflections("english", root):
        pytest.skip("English inflection tables arrive in squirrel-lang-data v0.1.4")
    entries = lexicon("english", root).lookup("saw")
    assert entries[0].meaning == "see+@past"
    # A past spelled like the lemma stays the lemma: read is read.
    assert lexicon("english", root).lookup("read")[0].meaning == "read"
