"""
Main translation interface.

This is a scaffold. Real translation logic (rule-based, LLM-assisted, or hybrid)
will live here and in the languages/ package.
"""

from typing import Optional

# Placeholder language registry
SUPPORTED = {
    "english", "pseudocode", "python", "javascript", "quickbasic",
    "brainfood", "lolcode", "sql", "shell"
}

def translate(
    source: str,
    from_lang: str,
    to_lang: str,
    *,
    style: Optional[str] = None,
) -> str:
    """
    Translate source text from one language to another.

    Parameters
    ----------
    source : str
        Input text (pseudocode, code, or natural language).
    from_lang : str
        Source language id (e.g. "english", "python", "pseudocode").
    to_lang : str
        Target language id.
    style : str, optional
        Hint for output style ("beginner", "concise", "commented", etc.).

    Returns
    -------
    str
        Translated result. Currently a scaffold message.
    """
    from_lang = from_lang.lower().strip()
    to_lang = to_lang.lower().strip()

    if from_lang not in SUPPORTED or to_lang not in SUPPORTED:
        return (
            f"[squirrelator] Unsupported language pair: {from_lang} → {to_lang}\n"
            f"Supported: {', '.join(sorted(SUPPORTED))}"
        )

    # Scaffold response — replace with real translation logic
    return (
        f"# squirrelator translation scaffold\n"
        f"# from: {from_lang}\n"
        f"# to:   {to_lang}\n"
        f"# style: {style or 'default'}\n\n"
        f"# Source:\n# {source}\n\n"
        f"# TODO: implement real translation for {from_lang} → {to_lang}"
    )
