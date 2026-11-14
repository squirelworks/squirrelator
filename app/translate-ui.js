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