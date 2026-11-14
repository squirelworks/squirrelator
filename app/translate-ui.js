/** Mirror of squirrelator.translate_ui for the standalone web app. */

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