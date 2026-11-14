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