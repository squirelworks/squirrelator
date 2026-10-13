#!/usr/bin/env python3
"""
squirrelator GUI — desktop translator
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from squirrelator import translate

LANGUAGES = [
    "english", "pseudocode", "python", "javascript", "quickbasic",
    "brainfood", "lolcode", "z80", "shell", "sql"
]

class SquirrelatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("squirrelator")
        self.root.geometry("1400x1000")
        self.root.minsize(1100, 800)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", font=("Segoe UI", 12))
        style.configure("TButton", font=("Segoe UI", 12), padding=8)
        style.configure("TCombobox", font=("Segoe UI", 12))

        # Header
        header = ttk.Frame(root)
        header.pack(fill="x", padx=20, pady=16)
        ttk.Label(header, text="squirrelator", font=("Segoe UI", 28, "bold")).pack()
        ttk.Label(header, text="Translate between human language, pseudocode, and code", foreground="gray").pack()

        # Language selectors
        lang_frame = ttk.Frame(root)
        lang_frame.pack(fill="x", padx=20, pady=8)

        ttk.Label(lang_frame, text="From:").pack(side="left")
        self.from_var = tk.StringVar(value="english")
        from_combo = ttk.Combobox(lang_frame, textvariable=self.from_var, values=LANGUAGES, state="readonly", width=18)
        from_combo.pack(side="left", padx=8)

        ttk.Label(lang_frame, text="To:").pack(side="left", padx=(24, 0))
        self.to_var = tk.StringVar(value="python")
        to_combo = ttk.Combobox(lang_frame, textvariable=self.to_var, values=LANGUAGES, state="readonly", width=18)
        to_combo.pack(side="left", padx=8)

        # Main panes — source and result side by side for visibility
        panes = ttk.PanedWindow(root, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=20, pady=8)

        # Source side
        source_frame = ttk.LabelFrame(panes, text="Source", padding=8)
        self.source = scrolledtext.ScrolledText(source_frame, font=("Consolas", 13), wrap="word")
        self.source.pack(fill="both", expand=True)
        self.source.insert("1.0", "print hello")
        panes.add(source_frame, weight=1)

        # Result side
        result_frame = ttk.LabelFrame(panes, text="Result", padding=8)
        self.result = scrolledtext.ScrolledText(result_frame, font=("Consolas", 13), wrap="word", state="disabled")
        self.result.pack(fill="both", expand=True)
        panes.add(result_frame, weight=1)

        # Buttons
        btn_frame = ttk.Frame(root)
        btn_frame.pack(fill="x", padx=20, pady=10)
        ttk.Button(btn_frame, text="Translate", command=self.do_translate).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Clear", command=self.clear).pack(side="left", padx=4)

        # Status
        self.status = ttk.Label(root, text="Ready — Source on left, Result on right", relief="sunken", anchor="w", font=("Segoe UI", 10))
        self.status.pack(fill="x", side="bottom")

        self.root.bind("<Control-Return>", lambda e: self.do_translate())

    def do_translate(self):
        src = self.source.get("1.0", "end").strip()
        if not src:
            self.status.config(text="Enter some source text")
            return
        try:
            out = translate(src, self.from_var.get(), self.to_var.get())
            self.result.config(state="normal")
            self.result.delete("1.0", "end")
            self.result.insert("1.0", out)
            self.result.config(state="disabled")
            self.status.config(text=f"Translated {self.from_var.get()} → {self.to_var.get()}")
        except Exception as e:
            self.status.config(text=f"Error: {e}")

    def clear(self):
        self.source.delete("1.0", "end")
        self.result.config(state="normal")
        self.result.delete("1.0", "end")
        self.result.config(state="disabled")
        self.status.config(text="Cleared")

def main():
    root = tk.Tk()
    app = SquirrelatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
