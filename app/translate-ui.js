/** Mirror of squirrelator.translate_ui for the standalone web app. */

const CODE_LANGS = new Set([
  "python", "javascript", "quickbasic", "brainfood", "lolcode",
  "z80", "sql", "shell",
]);

const CODE_PICKER_GROUP = "Code";

/** Rules-engine language order (mirrors squirrelator.translate_ui.RULES_LANG_ORDER). */
const RULES_LANG_ORDER = [
  "english", "klingon", "latin", "pseudocode",
  "javascript", "python", "shell", "sql",
  "quickbasic", "z80",
  "brainfood", "lolcode",
];

const LANG_LABELS = {
  brainfood: "brainFOOD",
  javascript: "JavaScript",
  lolcode: "LOLCODE",
  pseudocode: "Pseudocode",
  quickbasic: "QuickBASIC",
  shell: "Shell",
  sql: "SQL",
  z80: "Z80 Assembly",
};

function isNaturalLanguage(langId) {
  if (!langId) return false;
  return !CODE_LANGS.has(String(langId).toLowerCase());
}

function partitionPickerLanguages(langs) {
  const human = [];
  const code = [];
  for (const lang of langs) {
    if (isNaturalLanguage(lang)) human.push(lang);
    else code.push(lang);
  }
  return [human, code];
}

function buildLanguagePickerEntries(langs) {
  const [human, code] = partitionPickerLanguages(langs);
  const entries = human.map((value) => ({ kind: "language", value }));
  if (code.length) {
    entries.push({ kind: "header", value: CODE_PICKER_GROUP });
    code.forEach((value) => entries.push({ kind: "language", value }));
  }
  return entries;
}

function languageLabel(langId) {
  if (!langId) return "";
  const key = String(langId).toLowerCase();
  return LANG_LABELS[key] || key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatAlternativesLines(alternatives) {
  if (!alternatives || !alternatives.length) return [];
  return alternatives.filter((line) => String(line).trim());
}

/** Plain-language breakdown rows: dictionary form, meaning unit, note. */
function formatBreakdownRows(breakdown) {
  if (!breakdown || !breakdown.length) return [];
  const rows = [];
  for (const step of breakdown) {
    const dictionaryForm = step.dictionaryForm ?? step.source ?? "";
    const meaningUnit = step.meaningUnit ?? step.result ?? "";
    const note = step.note ?? step.why ?? "";
    if (!dictionaryForm && !meaningUnit && !note) continue;
    const summary = dictionaryForm || meaningUnit || note;
    rows.push({ dictionaryForm, meaningUnit, note, summary });
  }
  return rows;
}

function mergeSpans(length, spans) {
  if (!spans.length) return [];
  const ordered = [...spans].sort((a, b) => a[0] - b[0]);
  const merged = [ordered[0]];
  for (let i = 1; i < ordered.length; i += 1) {
    const [start, end] = ordered[i];
    const [lastStart, lastEnd] = merged[merged.length - 1];
    if (start <= lastEnd) {
      merged[merged.length - 1] = [lastStart, Math.max(lastEnd, end)];
    } else {
      merged.push([start, end]);
    }
  }
  return merged.map(([a, b]) => [a, Math.min(b, length)]).filter(([a, b]) => a < length);
}

function spansToSegments(text, spans) {
  if (!text) return [];
  if (!spans.length) return [{ text, highlight: false }];
  const out = [];
  let pos = 0;
  for (const [start, end] of spans) {
    if (pos < start) out.push({ text: text.slice(pos, start), highlight: false });
    if (start < end) out.push({ text: text.slice(start, end), highlight: true });
    pos = end;
  }
  if (pos < text.length) out.push({ text: text.slice(pos), highlight: false });
  return out.length ? out : [{ text, highlight: false }];
}

function unknownWordSpans(text, unknown) {
  const words = [...new Set((unknown || []).filter(Boolean))].sort((a, b) => b.length - a.length);
  const spans = [];
  for (const word of words) {
    let start = 0;
    while (start < text.length) {
      const at = text.indexOf(word, start);
      if (at < 0) break;
      spans.push([at, at + word.length]);
      start = at + word.length;
    }
  }
  return spans;
}

function segmentResultText(body, unknown = []) {
  const text = body || "";
  const spans = [];
  const bracketRe = /\[[^\]]+\]/g;
  let m;
  while ((m = bracketRe.exec(text)) !== null) {
    spans.push([m.index, m.index + m[0].length]);
  }
  const occupied = [...spans];
  for (const [start, end] of unknownWordSpans(text, unknown)) {
    if (!occupied.some(([a, b]) => a <= start && end <= b)) spans.push([start, end]);
  }
  return spansToSegments(text, mergeSpans(text.length, spans));
}

function segmentSourceText(source, unknown) {
  if (!unknown || !unknown.length) return [{ text: source || "", highlight: false }];
  return spansToSegments(source || "", mergeSpans((source || "").length, unknownWordSpans(source || "", unknown)));
}

function resultFooterText(fullResult, body) {
  if (!fullResult || !body || fullResult === body) return "";
  if (fullResult.startsWith(body)) return fullResult.slice(body.length).replace(/^\n+/, "");
  return "";
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function segmentsToHtml(segments) {
  return segments
    .map((seg) => (seg.highlight
      ? `<span class="unknown-token">${escapeHtml(seg.text)}</span>`
      : escapeHtml(seg.text)))
    .join("");
}

/** Render the main result body, optional footer, and alpha badge for the pair. */
function renderResultPane(outEl, footerEl, badgeEl, view) {
  const body = view.body != null && view.body !== "" ? view.body : view.result;
  const footer = view.footer != null ? view.footer : resultFooterText(view.result || "", body);
  outEl.innerHTML = segmentsToHtml(segmentResultText(body, view.unknown || []));
  if (footerEl) {
    footerEl.textContent = footer || "";
    footerEl.hidden = !footer;
  }
  if (badgeEl) {
    badgeEl.hidden = !view.alpha;
  }
}

/** Highlight unknown tokens in the source field when From is a natural language. */
function renderSourceHighlight(sourceEl, sourceText, fromLang, unknown) {
  if (!sourceEl) return;
  sourceEl.classList.remove("source-highlighted");
  if (!isNaturalLanguage(fromLang) || !unknown || !unknown.length) {
    sourceEl.textContent = sourceText;
    return;
  }
  sourceEl.classList.add("source-highlighted");
  sourceEl.innerHTML = segmentsToHtml(segmentSourceText(sourceText, unknown));
}

function sourcePlainText(sourceEl) {
  return sourceEl ? sourceEl.textContent : "";
}

/** Show or hide the Alternatives block under the result pane. */
function renderAlternatives(container, heading, alternatives) {
  const lines = formatAlternativesLines(alternatives);
  container.replaceChildren();
  if (!lines.length) {
    container.hidden = true;
    return;
  }
  container.hidden = false;
  const title = document.createElement("div");
  title.className = "alt-heading";
  title.textContent = heading || "Alternatives";
  container.appendChild(title);
  const list = document.createElement("ul");
  list.className = "alt-list";
  lines.forEach((line) => {
    const li = document.createElement("li");
    li.textContent = line;
    list.appendChild(li);
  });
  container.appendChild(list);
}

/** Show or hide the Breakdown block; selecting a row fills the detail pane. */
function renderBreakdown(container, heading, breakdown, onSelect) {
  const rows = formatBreakdownRows(breakdown);
  container.replaceChildren();
  if (!rows.length) {
    container.hidden = true;
    if (onSelect) onSelect(null);
    return;
  }
  container.hidden = false;
  const title = document.createElement("div");
  title.className = "bd-heading";
  title.textContent = heading || "Breakdown";
  container.appendChild(title);
  const body = document.createElement("div");
  body.className = "bd-body";
  const list = document.createElement("ul");
  list.className = "bd-list";
  list.setAttribute("role", "listbox");
  rows.forEach((row, idx) => {
    const li = document.createElement("li");
    li.textContent = row.summary;
    li.tabIndex = 0;
    li.setAttribute("role", "option");
    li.addEventListener("click", () => selectRow(idx));
    li.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        selectRow(idx);
      }
    });
    list.appendChild(li);
  });
  const detail = document.createElement("div");
  detail.className = "bd-detail";
  const fields = [
    ["Dictionary form", "bd-dict"],
    ["Meaning unit", "bd-meaning"],
    ["Why it was placed", "bd-note"],
  ];
  const valueEls = {};
  fields.forEach(([label, key]) => {
    const row = document.createElement("div");
    row.className = "bd-field";
    const lab = document.createElement("span");
    lab.className = "bd-label";
    lab.textContent = label;
    row.appendChild(lab);
    const val = document.createElement("div");
    val.className = "bd-value";
    val.dataset.bdKey = key;
    val.textContent = "—";
    valueEls[key] = val;
    row.appendChild(val);
    detail.appendChild(row);
  });
  function selectRow(idx) {
    list.querySelectorAll("li").forEach((el, i) => {
      el.classList.toggle("bd-selected", i === idx);
      if (i === idx) el.setAttribute("aria-selected", "true");
      else el.removeAttribute("aria-selected");
    });
    const row = rows[idx];
    valueEls["bd-dict"].textContent = row.dictionaryForm || "—";
    valueEls["bd-meaning"].textContent = row.meaningUnit || "—";
    valueEls["bd-note"].textContent = row.note || "—";
    if (onSelect) onSelect(row);
  }
  body.appendChild(list);
  body.appendChild(detail);
  container.appendChild(body);
  selectRow(0);
}

function swapTranslateState(fromLang, toLang, source, result) {
  const newFrom = toLang;
  const newTo = fromLang;
  const src = source || "";
  const res = result || "";
  if (res.trim()) {
    return [newFrom, newTo, res, src.trim() ? src : ""];
  }
  return [newFrom, newTo, src, res];
}

/** Rules-only web mirror: every pair is alpha except same-language. */
function pairShowsAlpha(fromLang, toLang) {
  return String(fromLang).toLowerCase() !== String(toLang).toLowerCase();
}