"""squirrelator — core language translation engine."""

from .features import Settings, load as load_features
from .result import Step, Translation, UnsupportedLanguage
from .translator import translate, translate_full

__all__ = [
    "Step",
    "Translation",
    "UnsupportedLanguage",
    "Settings",
    "load_features",
    "translate",
    "translate_full",
]
__version__ = "0.1.1"
