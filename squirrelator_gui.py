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
        self.root.geometry("900x700")
        self.root.minsize(700, 500)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 11), padding=6)
        style.configure("TCombobox", font=("Segoe UI", 11))

        # Header
        header = ttk.Frame(root)
        header.pack(fill="x", padx=16, pady=12)
        ttk.Label(header, text="squirrelator", font=("Segoe UI", 22, "bold")).pack()
        ttk.Label(header, text="Translate between human language, pseudocode, and code", foreground="gray").pack()

        # Language selectors
        lang_frame = ttk.Frame(root)
        lang_frame.pack(fill="x", padx=16, pady=6)

        ttk.Label(lang_frame, text="From:").pack(side="left")
        self.from_var = tk.StringVar(value="english")
        from_combo = ttk.Combobox(lang_frame, textvariable=self.from_var, values=LANGUAGES, state="readonly", width=16)
        from_combo.pack(side="left", padx=6)

        ttk.Label(lang_frame, text="To:").pack(side="left", padx=(20, 0))
        self.to_var = tk.StringVar(value="python")
        to_combo = ttk.Combobox(lang_frame, textvariable=self.to_var, values=LANGUAGES, state="readonly", width=16)
        to_combo.pack(side="left", padx=6)

        # Source
        ttk.Label(root, text="Source").pack(anchor="w", padx=16, pady=(10, 2))
        self.source = scrolledtext.ScrolledText(root, height=10, font=("Consolas", 11))
        self.source.pack(fill="both", expand=True, padx=16, pady=4)
        self.source.insert("1.0", "print hello")

        # Button
        btn_frame = ttk.Frame(root)
        btn_frame.pack(fill="x", padx=16, pady=6)
        ttk.Button(btn_frame, text="Translate", command=self.do_translate).pack(side="left")
        ttk.Button(btn_frame, text="Clear", command=self.clear).pack(side="left", padx=8)

        # Result
        ttk.Label(root, text="Result").pack(anchor="w", padx=16, pady=(10, 2))
        self.result = scrolledtext.ScrolledText(root, height=10, font=("Consolas", 11), state="disabled")
        self.result.pack(fill="both", expand=True, padx=16, pady=4)

        # Status
        self.status = ttk.Label(root, text="Ready", relief="sunken", anchor="w")
        self.status.pack(fill="x", side="bottom")

        # Bind Enter in source? optional
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
