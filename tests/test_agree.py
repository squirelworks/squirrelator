import pytest

from squirrelator import data
from squirrelator.inflections import Form, Word, inflections
from squirrelator.lexicon import language_meta
from squirrelator.pipeline import run
from squirrelator.pipeline.agree import agree, pick_form
from squirrelator.pipeline.interlingua import Interlingua, Unit

try:
    data.data_dir()
except data.DataNotFound:
    pytest.skip("squirrel-lang-data not checked out", allow_module_level=True)


@pytest.fixture
def latin(root):
    if not language_meta("latin", root).get("cases") or not inflections("latin", root):
        pytest.skip("Latin case tables arrive in squirrel-lang-data v0.1.4")
    return root


def form(name, text, *features):
    return Form(name, text, "", frozenset(features))


AQUA = Word("aqua", "", "water", (
    form("dictionary", "aqua", "@nominative", "@feminine"),
    form("accusative", "aquam", "@accusative", "@feminine"),
    form("accusative-plural", "aquās", "@accusative", "@plural", "@feminine"),
))


def test_pick_form_takes_the_wanted_case_and_ignores_a_nouns_own_gender():
    assert pick_form(AQUA, {"@accusative"}).text == "aquam"
    assert pick_form(AQUA, {"@accusative", "@plural"}).text == "aquās"
    assert pick_form(AQUA, set()).text == "aqua"


def test_a_target_without_cases_is_left_alone(root):
    il = Interlingua((Unit("water", "水", ("@object",)),), (), (), (), "japanese")
    plan = agree(il, "english", ["water"], root=root)
    assert plan.wanted == [{"@object"}] and plan.words == [None]


def test_marked_roles_take_their_case_and_the_verb_its_subjects_person(latin):
    # が marks the subject, を the object: nominative, accusative, third person.
    assert run("子供が水を飲みます。", "japanese", "latin", root=latin).text == "Puer aquam bibit."


def test_a_possessor_takes_the_genitive(latin):
    assert "amīcī" in run("友達の本を読みます。", "japanese", "latin", root=latin).text


def test_an_unsaid_subject_keeps_the_dictionary_person_and_a_pronoun_the_verb_says_is_dropped(latin):
    out = run("私は水を飲みました。", "japanese", "latin", root=latin)
    assert out.text == "Aquam bibī."     # perfect, first person; ego left out


def test_an_adjective_after_a_copula_agrees_with_the_subject(latin):
    # fēlēs is feminine, so big is magna, not magnus.
    assert run("猫は大きいです。", "japanese", "latin", root=latin).text == "Fēlēs est magna."


def test_a_place_takes_the_ablative_and_its_adjective_agrees(latin):
    out = run("友達は大きい家に住んでいます。", "japanese", "latin", root=latin).text
    assert "domō magnā" in out.casefold() and "habitat" in out


def test_english_word_order_tells_subject_from_object_but_not_after_a_copula(latin):
    out = run("This is a book.", "english", "latin", root=latin)
    assert all("librum" not in t for t in (out.text, *out.alternatives))
