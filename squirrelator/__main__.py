"""Default entry point: GUI unless --cli is given."""

import sys

def main():
    if "--cli" in sys.argv:
        # Minimal CLI for scripting
        from squirrelator import translate
        args = [a for a in sys.argv[1:] if a != "--cli"]
        if len(args) < 3:
            print("Usage: python3 -m squirrelator --cli <from> <to> <text...>")
            print("Example: python3 -m squirrelator --cli english python 'print hello'")
            sys.exit(1)
        from_lang, to_lang = args[0], args[1]
        source = " ".join(args[2:])
        print(translate(source, from_lang, to_lang))
        return

    # Default: GUI
    try:
        from squirrelator_gui import main as gui_main
        gui_main()
    except ImportError:
        # Fallback if run as module and gui is sibling
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from squirrelator_gui import main as gui_main
        gui_main()

if __name__ == "__main__":
    main()
