#!/usr/bin/env python3
"""
squirrelator — launch the GUI (default) or CLI with --cli
"""

import sys

def main():
    if "--cli" in sys.argv:
        from squirrelator import translate
        args = [a for a in sys.argv[1:] if a != "--cli"]
        if len(args) < 3:
            print("Usage: python3 squirrelator.py --cli <from> <to> <text...>")
            print("Example: python3 squirrelator.py --cli english python 'print hello'")
            sys.exit(1)
        from_lang, to_lang = args[0], args[1]
        source = " ".join(args[2:])
        print(translate(source, from_lang, to_lang))
        return

    from squirrelator_gui import main as gui_main
    gui_main()

if __name__ == "__main__":
    main()
