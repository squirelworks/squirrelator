#!/usr/bin/env python3
"""
squirrelator GUI — desktop translator
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from squirrelator.menus import AUTO, ENGINES, PIPELINE, display, languages_for
from squirrelator.translate_ui import language_label, swap_translate_state


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
        header.pack(fill="x", padx=20, pady=12)
        ttk.Label(header, text="squirrelator", font=("Segoe UI", 28, "bold")).pack()
        ttk.Label(header, text="Translate between human language, pseudocode, and code",
                  foreground="gray").pack()

        # Engine + actions (languages live on each pane)
        top = ttk.Frame(root)
        top.pack(fill="x", padx=20, pady=6)

        ttk.Label(top, text="Engine:").pack(side="left")
        self.engine_var = tk.StringVar(value=AUTO)
        engine_combo = ttk.Combobox(top, textvariable=self.engine_var, values=ENGINES, state="readonly", width=16)
        engine_combo.pack(side="left", padx=(6, 16))
        engine_combo.bind("<<ComboboxSelected>>", lambda e: self.engine_changed())

        ttk.Button(top, text="Translate", command=self.do_translate).pack(side="left", padx=(8, 4))
        ttk.Button(top, text="Clear", command=self.clear).pack(side="left", padx=4)

        # Two panes with a swap control between them
        body = ttk.Frame(root)
        body.pack(fill="both", expand=True, padx=20, pady=8)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(2, weight=1)
        body.rowconfigure(0, weight=1)

        source_shell = ttk.LabelFrame(body, text="Source", padding=8)
        source_shell.grid(row=0, column=0, sticky="nsew")
        source_shell.rowconfigure(1, weight=1)
        source_shell.columnconfigure(0, weight=1)

        from_row = ttk.Frame(source_shell)
        from_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(from_row, text="From:").pack(side="left")
        self.from_var = tk.StringVar(value="english")
        self.from_combo = ttk.Combobox(
            from_row, textvariable=self.from_var, values=languages_for(AUTO), state="readonly", width=20,
        )
        self.from_combo.pack(side="left", padx=6, fill="x", expand=True)

        self.source = scrolledtext.ScrolledText(source_shell, font=("Consolas", 13), wrap="word", height=12)
        self.source.grid(row=1, column=0, sticky="nsew")
        self.source.insert("1.0", "print hello")

        swap_col = ttk.Frame(body)
        swap_col.grid(row=0, column=1, sticky="ns", padx=6)
        ttk.Button(swap_col, text="⇄\nSwap", command=self.do_swap).pack(expand=True)

        result_shell = ttk.LabelFrame(body, text="Result", padding=8)
        result_shell.grid(row=0, column=2, sticky="nsew")
        result_shell.rowconfigure(1, weight=1)
        result_shell.columnconfigure(0, weight=1)

        to_row = ttk.Frame(result_shell)
        to_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(to_row, text="To:").pack(side="left")
        self.to_var = tk.StringVar(value="python")
        self.to_combo = ttk.Combobox(
            to_row, textvariable=self.to_var, values=languages_for(AUTO), state="readonly", width=20,
        )
        self.to_combo.pack(side="left", padx=6, fill="x", expand=True)

        self.result = scrolledtext.ScrolledText(result_shell, font=("Consolas", 13), wrap="word",
                                                state="disabled", height=12)
        self.result.grid(row=1, column=0, sticky="nsew")

        self.status = ttk.Label(root, text="Ready", relief="sunken", anchor="w", font=("Segoe UI", 10))
        self.status.pack(fill="x", side="bottom")

        self.root.bind("<Control-Return>", lambda e: self.do_translate())

    def _langs(self):
        return languages_for(self.engine_var.get())

    def engine_changed(self):
        """Fill From and To with the chosen engine's languages and pick a
        pair that shows what the engine does."""
        engine = self.engine_var.get()
        langs = self._langs()
        defaults = ("japanese", "english") if engine == PIPELINE else ("english", "python")
        for combo, var, default in ((self.from_combo, self.from_var, defaults[0]),
                                    (self.to_combo, self.to_var, defaults[1])):
            combo.config(values=langs)
            var.set(default if default in langs else (langs[0] if langs else ""))
        if engine == PIPELINE and not langs:
            self.status.config(text="Pipeline has no languages: the language data is missing.")
        else:
            self.status.config(text=f"Engine: {engine}")

    def do_swap(self):
        frm, to, src, res = swap_translate_state(
            self.from_var.get(),
            self.to_var.get(),
            self.source.get("1.0", "end").rstrip("\n"),
            self._result_text(),
        )
        langs = self._langs()
        self.from_var.set(frm if frm in langs else (langs[0] if langs else frm))
        self.to_var.set(to if to in langs else (langs[1] if len(langs) > 1 else to))
        self.source.delete("1.0", "end")
        self.source.insert("1.0", src)
        self._set_result(res)
        self.status.config(
            text=f"Swapped — {language_label(self.from_var.get())} → {language_label(self.to_var.get())}"
        )

    def _result_text(self) -> str:
        return self.result.get("1.0", "end").rstrip("\n")

    def _set_result(self, text: str):
        self.result.config(state="normal")
        self.result.delete("1.0", "end")
        if text:
            self.result.insert("1.0", text)
        self.result.config(state="disabled")

    def do_translate(self):
        src = self.source.get("1.0", "end").strip()
        if not src:
            self.status.config(text="Enter some source text")
            return
        try:
            engine = self.engine_var.get()
            frm, to = self.from_var.get(), self.to_var.get()
            out, used = display(src, frm, to, engine)
            self._set_result(out)
            self.status.config(text=f"Translated {language_label(frm)} → {language_label(to)} with {used}")
        except Exception as e:
            self.status.config(text=f"Error: {e}")

    def clear(self):
        self.source.delete("1.0", "end")
        self._set_result("")
        self.status.config(text="Cleared")


def main():
    root = tk.Tk()
    SquirrelatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()