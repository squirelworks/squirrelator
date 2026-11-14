/** Mirror of squirrelator.prose for the standalone web app. */

const PROSE_SKIP = new Set(["pseudocode"]);
const SENTENCE_END = ".!?。！？";

function isProseLanguagePair(fromLang, toLang) {
  if (!fromLang || !toLang) return false;
  const from = String(fromLang).toLowerCase();
  const to = String(toLang).toLowerCase();
  if (PROSE_SKIP.has(from) || PROSE_SKIP.has(to)) return false;
  return isNaturalLanguage(from) && isNaturalLanguage(to);
}

function splitProseParagraphs(text) {
  if (!text) return [];
  const paragraphs = [];
  let current = [];
  for (const line of String(text).split("\n")) {
    if (line.trim() === "") {
      if (current.length) {
        paragraphs.push(current.join("\n"));
        current = [];
      }
    } else {
      current.push(line);
    }
  }
  if (current.length) paragraphs.push(current.join("\n"));
  return paragraphs;
}

function splitSentences(paragraph) {
  const collapsed = String(paragraph).replace(/\n/g, " ").trim().split(/\s+/).filter(Boolean).join(" ");
  if (!collapsed) return [];
  const sentences = [];
  let start = 0;
  for (let i = 0; i < collapsed.length; i += 1) {
    if (!SENTENCE_END.includes(collapsed[i])) continue;
    let j = i + 1;
    while (j < collapsed.length && /\s/.test(collapsed[j])) j += 1;
    const piece = collapsed.slice(start, j).trim();
    if (piece) sentences.push(piece);
    start = j;
  }
  if (start < collapsed.length) {
    const tail = collapsed.slice(start).trim();
    if (tail) sentences.push(tail);
  }
  return sentences.length ? sentences : [collapsed];
}

function proseNeedsSplitting(text) {
  const paragraphs = splitProseParagraphs(text);
  if (paragraphs.length > 1) return true;
  if (paragraphs.length === 1 && splitSentences(paragraphs[0]).length > 1) return true;
  return false;
}

function shouldTranslateProse(text, fromLang, toLang) {
  return isProseLanguagePair(fromLang, toLang) && proseNeedsSplitting(text);
}

function joinTranslatedParagraphs(paragraphTexts) {
  const blocks = paragraphTexts
    .map((sentences) => sentences.join(" ").trim())
    .filter(Boolean);
  return blocks.join("\n\n");
}

function mergeTranslateParts(parts) {
  const unknown = [];
  const alternatives = [];
  const breakdown = [];
  let alpha = false;
  let confidence = 1;
  for (const part of parts) {
    for (const w of part.unknown || []) {
      if (!unknown.includes(w)) unknown.push(w);
    }
    for (const a of part.alternatives || []) {
      if (a && !alternatives.includes(a)) alternatives.push(a);
    }
    if (part.breakdown && part.breakdown.length) breakdown.push(...part.breakdown);
    if (part.alpha) alpha = true;
    if (part.confidence != null) confidence = Math.min(confidence, part.confidence);
  }
  return { unknown, alternatives, breakdown, alpha, confidence };
}