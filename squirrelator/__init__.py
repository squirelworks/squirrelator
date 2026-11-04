"""squirrelator — core language translation engine."""

from .result import Step, Translation, UnsupportedLanguage
from .translator import translate, translate_full

__all__ = ["Step", "Translation", "UnsupportedLanguage", "translate", "translate_full"]
__version__ = "0.1.0"
