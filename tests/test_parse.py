import json

import pytest

from squirrelator import data
from squirrelator.pipeline.analyze import analyze
from squirrelator.pipeline.parse import parse

from conftest import MARKERS  # noqa: E402

try:
    data.data_dir()
except data.DataNotFound:
    pytest.skip("squirrel-lang-data not checked out", allow_module_level=True)


def shape(clause):
    """Each phrase as (head, [markers]) by text, plus the clause features."""
    return [(p.head.text, [m.text for m in p.markers]) for p in clause.phrases], list(clause.features)


def run(text, language, root):
    from squirrelator.lexicon import lexicon
    return parse(analyze(text, language, lex=lexicon(language, root)), language, root=root)


def test_japanese_particles_follow_their_word(root):
    [clause] = run("バスで学校に行きます。", "japanese", root)
    assert shape(clause) == ([("バス", ["で"]), ("学校", ["に"]), ("行きます", [])], [])
    assert [p.meaning for p in clause.phrases] == ["bus", "school", "go"]
    bus, school, go = (p.roles for p in clause.phrases)
    assert len(bus) == 1 and "@means" in bus[0]   # で can also be @place
    assert "@place" in school[0] and go == ()


def test_english_prepositions_and_articles_precede_their_word(root):
    [clause] = run("I take the bus to school.", "english", root)
    assert shape(clause) == ([("I", []), ("take", []), ("bus", ["the"]), ("school", ["to"])], [])


def test_affixes_join_their_stem(root):
    [clause] = run("저는 커피를 좋아해요.", "hangul", root)
    assert shape(clause) == ([("저", ["는"]), ("커피", ["를"]), ("좋아해요", [])], [])
    assert [p.roles for p in clause.phrases][:2] == [(("@topic",),), (("@object",),)]


def test_chinese_possessive_follows_but_prepositions_precede(root):
    [clause] = run("我的名字", "chinese", root)
    assert shape(clause)[0][0] == ("我", ["的"])


def test_a_marker_with_no_word_to_join_is_a_clause_feature(root):
    [clause] = run("学生ですか", "japanese", root)
    # です and か both follow 学生, so they join it: the data puts every
    # Japanese marker after its word.
    assert shape(clause) == ([("学生", ["です", "か"])], [])
    [clause] = run("Salve, quid agis?", "latin", root)
    assert "@question" in clause.features


def test_pinned_data_attaches_markers_to_phrases():
    # data v0.1.1 ships "markers" in meta.json, so に is no clause feature.
    [clause] = parse(analyze("学校に行きます", "japanese"), "japanese")
    assert [p.head.text for p in clause.phrases] == ["学校", "行きます"]
    assert [t.text for t in clause.phrases[0].markers] == ["に"]
    assert "@place" not in clause.features


def test_clauses_split_at_sentence_punctuation(root):
    clauses = run("私は学生です。バスで学校に行きます！", "japanese", root)
    assert len(clauses) == 2
    assert "".join(t.text for c in clauses for t in c.tokens) == "私は学生です。バスで学校に行きます！"


def test_unknown_words_stay_heads_and_are_listed(root):
    [clause] = run("I like xyzzy.", "english", root)
    assert [p.head.text for p in clause.phrases] == ["I", "like", "xyzzy"]
    assert [t.text for t in clause.unknown] == ["xyzzy"]


def test_every_matrix_sentence_has_one_phrase_per_content_meaning(root):
    """Every meaning-matrix sentence in the tested languages parses into one
    phrase per content token the data lists, headed by a word carrying that
    meaning. The one exception is a longer dictionary word that covers
    several listed tokens (今日は, ありがとうございます), which becomes one
    phrase."""
    from squirrelator.lexicon import lexicon
    from squirrelator.pipeline.parse import meanings_of
    problems = []
    for lang in MARKERS:
        path = root / "meaning" / "columns" / f"{lang}.jsonl"
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        sep = json.loads(lines[0]).get("sep", " ")
        for line in lines[1:]:
            row = json.loads(line)
            text, spans = "", []          # each listed token's (start, end, meaning)
            for word, _, meaning in row["t"]:
                glue = not text or word.startswith("-") or text.endswith("-")
                word = word.strip("-") if len(word) > 1 else word
                text = text.rstrip("-") + ("" if glue else sep)
                spans.append((len(text), len(text) + len(word), meaning))
                text += word
            clauses = parse(analyze(text, lang, lex=lexicon(lang, root)), lang, root=root)
            content = [(a, b, m) for a, b, m in spans if not m.startswith("@")]
            heads = [p.head for c in clauses for p in c.phrases]
            for head in heads:
                covered = [m for a, b, m in content if head.start <= a and b <= head.end]
                if len(covered) == 1 and covered[0] in meanings_of(head):
                    continue
                if len([1 for a, b, _ in spans if head.start <= a and b <= head.end]) > 1:
                    continue  # a longer dictionary word
                problems.append((lang, row["sentence"], head.text))
            merged = sum(1 for h in heads if len([1 for a, b, _ in spans if h.start <= a and b <= h.end]) > 1)
            if not merged and len(heads) != len(content):
                problems.append((lang, row["sentence"], [h.text for h in heads]))
    assert problems == []
