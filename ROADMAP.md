# squirrelator roadmap

Each phase is a series of one-seam PRs. Phases can overlap once the previous
phase's foundations have merged. Tick a box when the PR that finishes it
merges, and name the PR on the line. Status as of 2026-11-14, with `data/`
at squirrel-lang-data **v0.1.5** (#49). Every unticked box is open for the
next agent (Cursor or Codex). The platform handoff brief is LanguageStudentDesk's
[`docs/HANDOFF.md`](https://github.com/squirelworks/LanguageStudentDesk/blob/main/docs/HANDOFF.md),
and the suggested order, risks and working lessons are in its
[`docs/FUTURE-WORK.md`](https://github.com/squirelworks/LanguageStudentDesk/blob/main/docs/FUTURE-WORK.md).
Open issues: #25 (phone app) and #26 (Pipeline vs Rules coverage).

How to work, learned the hard way: open **few, sizeable PRs here, one theme
each, and merge them one after another**. A data change goes to
squirrel-lang-data first; `data/` moves only to a published data tag, in its
own PR, after LanguageStudentDesk's pin bump.

## Phase 0: Bootstrap the repo so it's safe to work in

- [x] `AGENTS.md` and `.github/MERGING.md` (#2)
- [x] CI: `pytest`, ruff and a syntax check for the web app (#3)
- [x] PR guard script and workflow with the sticky "Merge verdict" comment, plus the PR conflicts workflow (#4)
- [x] README's "Supported languages" no longer lists the languages by hand (#5)
- [x] Golden tests for every behavior `translate()` had (#6)

## Phase 1: Engine architecture

- [x] **Analyze:** tokenize and segment with squirrel-lang-data's word lists (#13), reading inflection tables (#21)
- [x] **Parse:** group tokens into clauses and phrases (#14), with fixes for the code-pack columns (#35)
- [x] **Interlingua:** clauses to matrix meanings (#15)
- [x] **Transfer and generate:** meaning units to target sentences (#18), with Latin declension and conjugation from the data's tables (#36) and agreement in prepositional phrases (#37)
- [x] **Rank:** score candidates with a note (#19, #23, #28)
- [x] `Translation(text, alternatives, breakdown, unknown, confidence, alpha)` and `translate_full()`; `translate()` still returns the text (#12)
- [x] `translate(engine="pipeline")` (#22), then `engine="auto"` as the default: code pairs stay on Rules, human-language pairs go to the Pipeline (#27)
- [x] The `squirrel-lang-data` submodule at `data/` (#9), found through `SQUIRREL_LANG_DATA` or `data/`; CI fails unless it's pinned to a tagged data release on `main` (#11); pinned to v0.1.3 (#38), v0.1.4 (#41) and v0.1.5 (#49)

## Phase 2: Human-language translation

- [ ] Pairs with the most data first. Status per pair is in #26:
  - [ ] English↔Japanese (full column; above the 90% bar since #28, #47; alpha label still on)
  - [ ] English↔Chinese (101 of 103 rows to English; open: 吃饭 and 几点了)
  - [ ] English↔Korean (103 of 103 both ways on the matrix rows; alpha label still on)
  - [ ] English↔Latin (declension and conjugation from the data, #36; full column since data v0.1.5, #49)
  - [ ] English↔Klingon (15 of 17 rows right; open: jIyajbe' and Dajatlh'a')
  - [ ] English↔French, German, Italian, Greek and Russian (full columns since data v0.1.5; at the bar on the matrix rows per #26, alpha label still on)
  - [ ] English↔Taiwanese (no matrix column yet)
  - [ ] The rest of the languages, as their matrix columns arrive in squirrel-lang-data
- [ ] Language-to-language pairs go through the interlingua, not through English strings
- [ ] For each pair: dropped subjects and objects, tense and aspect, particles and case, counters and measure words, politeness level, word order
- [ ] **Test sets for each pair:** every accepted translation and some rejected ones, from the matrix plus Tatoeba (CC BY 2.0 FR) with attribution. A pair's alpha label comes off only when its set passes (bar proposed in #26: 90% of column rows both ways).
- [x] English as the source: a word with several meanings reads as the one the row has (love, house, have), contractions in a row's wording count as its pieces, and English contractions come from the data (data #105)
- [x] Spaced languages: a prefix with a content meaning heads its own phrase (French j', d', t'), a prefix may glue to a phrase (J'ai mal), and a phrase or vocab card with only a gloss doesn't swallow words that have meanings (το τσάι, l'eau)
- [ ] Detect the source language from its script and word list, with a user override
- [x] english↔latin and english↔klingon sentences move from Rules to the Pipeline under Auto (the owner's call, #26); a code instruction keeps Rules first, and the other engine's answer shows as a second opinion (#32)

## Phase 2b: Varieties and character forms (follows LanguageStudentDesk#200)

- [ ] Traditional↔simplified Chinese and shinjitai↔kyūjitai conversion as its own mode, resolving one-to-many mappings (发 to 發 and 髮) by context and the word list, with alternatives shown and tests
- [ ] Each variety as a translation target (Cantonese, Hokkien, Hakka, the Ryukyuan languages, Ainu, Classical Chinese, Classical Japanese, Middle English, Ancient Greek, Classical Latin), alpha until its test set passes
- [ ] Variety ↔ parent works like any other pair (Middle English to modern English)
- [ ] Varieties, historical stages and pronunciation choices appear only when the matching `features.json` switch is on, with the same Simple, More and Everything levels as LSD
- [ ] Handwriting input (Phase 3b) can search one character form or several

## Phase 3: A translator UI that works like Google Translate (GUI and web as twins)

- [x] Auto as the default engine in the GUI, with the Pipeline offered as an alpha engine (#24, #30)
- [ ] Two panes with the source and the result, a language picker on each side, and a swap button
- [ ] An **Alternatives** list under the result
- [ ] A **Breakdown** view: click a word to see its meaning unit, dictionary form and the rule that placed it
- [ ] Unknown words highlighted, and an alpha badge for each pair
- [ ] Pasted prose translated sentence by sentence, keeping paragraphs
- [ ] A "Code" target group in the target picker (Phase 4)

## Phase 3a: Native apps (#25)

- [x] `native/`: one Compose translate screen for Android and desktop, with the Python engine via Chaquopy (#31)
- [x] Hand-started test APK workflow (#33)
- [x] The phone screen shows the Auto engine and the second opinion (#34)
- [ ] The rest of the checklist in #25 (size, desktop Python, parity, signing, first release; the Tk window is replaced only after the owner signs off)

## Phase 3b: Handwriting input from the stroke data

Depends on LanguageStudentDesk#188: only scripts whose stroke data passes the final-frame and stroke-count checks are offered.

- [ ] A shared matcher (the writing pad's `judge`/`compare` from `strokes.js`, moved into one module) with a Python version and the JS version agreeing on the same tests
- [ ] Ranking by stroke count (±1–2), stroke order as a bonus, then shape distance, with a pick list of top candidates
- [ ] Script scope picked by the user; CJK filtered by tradition
- [ ] Whole words: characters written one after another, one pick list per character
- [ ] Tests from synthetic handwriting plus consented real samples; top-1 and top-5 accuracy per script generated by the tests, never written in the docs by hand
- [ ] Deterministic and offline; any trained model is built from squirrel-lang-data by a checked-in tool and released through GitHub Releases
- [ ] Twins: the pad works the same in the GUI, the web app, and later the LSD and SquirrelGo pads

## Phase 4: Prose to code

- [ ] An **intent grammar** from English (and later other languages through the interlingua): output, variables, arithmetic and comparison, if/else, loops, functions, lists and maps, input, files
- [ ] Generators in LSD's order: modern (Python, C, C++, C#, JavaScript, Rust, Go, BASIC and Visual Basic, modern Delphi and Pascal, SQL, shell), then older (QuickBASIC, COBOL, Fortran, Z80), then joke (brainFOOD, LOLCODE). Keyword maps live as data in squirrel-lang-data.
- [ ] Code back to prose, and code to code through the intent graph, replacing today's regex mapping
- [x] **Code explained in your language:** Rules explains code in English, the Pipeline takes it into any language with a column, using the code pack's English rows (#46, closes squirrel-lang-data#56). Klingon has no code-pack column yet (#26).
- [ ] Every generated program CI can run is run in the tests, with its output checked
- [ ] A sentence it can't map becomes a comment saying it wasn't understood

## Phase 5: Evaluation and integration with LSD

- [ ] A regression report from every pair's test set and every code target's tests, generated in CI. **Do this first in Phase 5:** a per-column table (rows back to English as the top result, each direction) written as a CI artifact, and the alpha labels driven by it (#26).
- [ ] LSD's translation learner and meaning network call squirrelator for checking and alternatives (LanguageStudentDesk#193, #194), with a PR in each repo naming the other
- [x] Package releases (wheel) go to GitHub Releases (the hand-started Draft release workflow, #1)
