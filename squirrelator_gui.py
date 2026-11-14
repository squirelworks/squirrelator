#!/usr/bin/env python3
"""
squirrelator GUI — desktop translator
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from squirrelator.features import CUSTOM, Settings
from squirrelator.menus import AUTO, ENGINES, PIPELINE, languages_for, translate_view
from squirrelator.translate_ui import (
    format_alternatives_lines,
    format_breakdown_rows,
    language_label,
    swap_translate_state,
)


class SquirrelatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("squirrelator")
        self.root.geometry("1400x1000")
        self.root.minsize(1100, 800)
        self.settings = Settings.load_saved()

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", font=("Segoe UI", 12))
        style.configure("TButton", font=("Segoe UI", 12), padding=8)
        style.configure("TCombobox", font=("Segoe UI", 12))
        style.configure("Muted.TLabel", foreground="gray")

        # Header
        header = ttk.Frame(root)
        header.pack(fill="x", padx=20, pady=12)
        ttk.Label(header, text="squirrelator", font=("Segoe UI", 28, "bold")).pack(side="left")
        ttk.Button(header, text="Settings", command=self.open_settings).pack(side="right")
        ttk.Label(header, text="Translate between human language, pseudocode, and code",
                  foreground="gray").pack(side="left", padx=16)

        text = self.settings.data.text
        self.notice = ttk.Frame(root)
        if text.get("notice") and not self.settings.notice_dismissed:
            self.notice.pack(fill="x", padx=20, pady=(0, 4))
            ttk.Label(self.notice, text=text["notice"], style="Muted.TLabel").pack(side="left")
            ttk.Button(self.notice, text="Dismiss", command=self.dismiss_notice).pack(side="right")
            ttk.Button(self.notice, text="Open Settings", command=self.open_settings).pack(side="right", padx=6)

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
            from_row, textvariable=self.from_var, values=self._langs(), state="readonly", width=20,
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
        result_shell.rowconfigure(3, weight=0)
        result_shell.rowconfigure(4, weight=0)
        result_shell.columnconfigure(0, weight=1)

        to_row = ttk.Frame(result_shell)
        to_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(to_row, text="To:").pack(side="left")
        self.to_var = tk.StringVar(value="python")
        self.to_combo = ttk.Combobox(
            to_row, textvariable=self.to_var, values=self._langs(), state="readonly", width=20,
        )
        self.to_combo.pack(side="left", padx=6, fill="x", expand=True)

        self.result = scrolledtext.ScrolledText(result_shell, font=("Consolas", 13), wrap="word",
                                                state="disabled", height=12)
        self.result.grid(row=1, column=0, sticky="nsew")

        self.alt_frame = ttk.Frame(result_shell)
        self.alt_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.alt_frame.columnconfigure(0, weight=1)
        ttk.Label(self.alt_frame, text="Alternatives", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self.alt_list = tk.Listbox(
            self.alt_frame, font=("Consolas", 12), height=4, activestyle="none",
            exportselection=False, highlightthickness=0,
        )
        self.alt_list.grid(row=1, column=0, sticky="ew")
        self.alt_list.bind("<Double-Button-1>", self._copy_alternative)
        self.alt_frame.grid_remove()

        self.bd_frame = ttk.Frame(result_shell)
        self.bd_frame.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        self.bd_frame.columnconfigure(0, weight=1)
        ttk.Label(self.bd_frame, text="Breakdown", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        bd_body = ttk.Frame(self.bd_frame)
        bd_body.grid(row=1, column=0, sticky="ew")
        bd_body.columnconfigure(0, weight=1)
        bd_body.columnconfigure(1, weight=1)
        self.bd_list = tk.Listbox(
            bd_body, font=("Consolas", 11), height=4, activestyle="dotbox",
            exportselection=False, highlightthickness=0,
        )
        self.bd_list.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.bd_list.bind("<<ListboxSelect>>", self._show_breakdown_detail)
        self.bd_detail = ttk.LabelFrame(bd_body, text="Selected", padding=6)
        self.bd_detail.grid(row=0, column=1, sticky="nsew")
        self._bd_detail_vars = {
            "dictionary": tk.StringVar(value="—"),
            "meaning": tk.StringVar(value="—"),
            "note": tk.StringVar(value="—"),
        }
        for i, (key, label) in enumerate(
            (("dictionary", "Dictionary form"), ("meaning", "Meaning unit"), ("note", "Why it was placed"))
        ):
            ttk.Label(self.bd_detail, text=f"{label}:", style="Muted.TLabel").grid(row=i * 2, column=0, sticky="nw")
            ttk.Label(
                self.bd_detail, textvariable=self._bd_detail_vars[key], wraplength=280,
            ).grid(row=i * 2 + 1, column=0, sticky="w", pady=(0, 4))
        self._breakdown_rows = []
        self.bd_frame.grid_remove()

        self.status = ttk.Label(root, text="Ready", relief="sunken", anchor="w", font=("Segoe UI", 10))
        self.status.pack(fill="x", side="bottom")

        self.root.bind("<Control-Return>", lambda e: self.do_translate())
        self._settings_win = None
        self.settings.on_change(lambda _s: self.refresh_languages())

    def _langs(self):
        return languages_for(self.engine_var.get(), self.settings)

    def dismiss_notice(self):
        self.settings.notice_dismissed = True
        self.settings.save()
        self.notice.pack_forget()

    def refresh_languages(self):
        """Keep From/To in sync when Settings hide or show a language group."""
        langs = self._langs()
        for combo, var in ((self.from_combo, self.from_var), (self.to_combo, self.to_var)):
            combo.config(values=langs)
            if var.get() not in langs:
                var.set(langs[0] if langs else "")

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
        self._set_alternatives(())
        self._set_breakdown(())
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

    def _set_alternatives(self, alternatives):
        lines = format_alternatives_lines(alternatives)
        self.alt_list.delete(0, "end")
        if lines:
            self.alt_frame.grid()
            for line in lines:
                self.alt_list.insert("end", line)
        else:
            self.alt_frame.grid_remove()

    def _copy_alternative(self, _event=None):
        sel = self.alt_list.curselection()
        if not sel:
            return
        text = self.alt_list.get(sel[0])
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def _set_breakdown(self, breakdown):
        steps = breakdown if isinstance(breakdown, tuple) else tuple(breakdown or ())
        self._breakdown_rows = format_breakdown_rows(steps)
        self.bd_list.delete(0, "end")
        for key in self._bd_detail_vars:
            self._bd_detail_vars[key].set("—")
        if self._breakdown_rows:
            self.bd_frame.grid()
            for row in self._breakdown_rows:
                self.bd_list.insert("end", row.summary)
            self.bd_list.selection_set(0)
            self._show_breakdown_detail()
        else:
            self.bd_frame.grid_remove()

    def _show_breakdown_detail(self, _event=None):
        sel = self.bd_list.curselection()
        if not sel or not self._breakdown_rows:
            return
        row = self._breakdown_rows[sel[0]]
        self._bd_detail_vars["dictionary"].set(row.dictionary_form or "—")
        self._bd_detail_vars["meaning"].set(row.meaning_unit or "—")
        self._bd_detail_vars["note"].set(row.note or "—")

    def open_settings(self):
        """Simple / More / Everything, Customize and What's in the app — same
        feature ids and labels as LanguageStudentDesk, from features.json."""
        if self._settings_win is not None and self._settings_win.winfo_exists():
            self._settings_win.lift()
            return
        data = self.settings.data
        text = data.text
        win = tk.Toplevel(self.root)
        self._settings_win = win
        win.title("Settings")
        win.geometry("640x720")
        canvas = tk.Canvas(win, highlightthickness=0)
        bar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas, padding=16)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        level_var = tk.StringVar(value=self.settings.level if self.settings.level != CUSTOM else "")
        switch_vars = {}
        custom_lbl = None
        whats = ttk.Frame(inner)

        def redraw_whats():
            for w in whats.winfo_children():
                w.destroy()
            for f in sorted(data.features, key=lambda f: f.label):
                on = self.settings.is_on(f.id)
                state = "on" if on else f"off: turn on {f.label} in Customize"
                ttk.Label(whats, text=f"{f.label} ({state})", font=("Segoe UI", 11, "bold")).pack(anchor="w")
                ttk.Label(whats, text=f.description, style="Muted.TLabel", wraplength=560).pack(anchor="w", pady=(0, 6))

        def refresh():
            if self.settings.level == CUSTOM:
                level_var.set("")
                custom_lbl.config(text=text.get("custom", "Custom"))
            else:
                level_var.set(self.settings.level)
                custom_lbl.config(text="")
            for fid, var in switch_vars.items():
                var.set(self.settings.is_on(fid))
            redraw_whats()
            self.settings.save()
            self.refresh_languages()

        def pick_level():
            chosen = level_var.get()
            if chosen:
                self.settings.set_level(chosen)
                refresh()

        levels = ttk.LabelFrame(inner, text="Show", padding=10)
        levels.pack(fill="x", pady=(0, 10))
        for lv in data.levels:
            ttk.Radiobutton(levels, text=lv.label, value=lv.id, variable=level_var,
                            command=pick_level).pack(anchor="w")
            ttk.Label(levels, text=lv.description, style="Muted.TLabel", wraplength=560).pack(anchor="w", padx=(24, 0))
        custom_lbl = ttk.Label(levels, text=text.get("custom", "Custom") if self.settings.level == CUSTOM else "")
        custom_lbl.pack(anchor="w", pady=(4, 0))

        custom = ttk.LabelFrame(inner, text=text.get("customize", "Customize"), padding=10)
        custom.pack(fill="x", pady=(0, 10))
        for f in self.settings.customize_order():
            var = tk.BooleanVar(value=self.settings.is_on(f.id))
            switch_vars[f.id] = var

            def flip(fid=f.id, v=var):
                self.settings.set(fid, v.get())
                refresh()
            ttk.Checkbutton(custom, text=f.label, variable=var, command=flip).pack(anchor="w")
            ttk.Label(custom, text=f.description, style="Muted.TLabel", wraplength=560).pack(anchor="w", padx=(24, 0))

        ttk.Label(inner, text=text.get("whatsInApp", "What's in the app"),
                  font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(6, 4))
        whats.pack(fill="x")
        redraw_whats()

    def do_translate(self):
        src = self.source.get("1.0", "end").strip()
        if not src:
            self.status.config(text="Enter some source text")
            return
        try:
            engine = self.engine_var.get()
            frm, to = self.from_var.get(), self.to_var.get()
            view = translate_view(src, frm, to, engine)
            self._set_result(view.result)
            self._set_alternatives(view.alternatives)
            self._set_breakdown(view.breakdown)
            self.status.config(text=f"Translated {language_label(frm)} → {language_label(to)} with {view.engine}")
        except Exception as e:
            self.status.config(text=f"Error: {e}")

    def clear(self):
        self.source.delete("1.0", "end")
        self._set_result("")
        self._set_alternatives(())
        self._set_breakdown(())
        self.status.config(text="Cleared")


def main():
    root = tk.Tk()
    SquirrelatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
