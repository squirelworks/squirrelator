// Feature switches and Settings levels for the squirrelator web twin.
// Switches come from squirrel-lang-data features.json via app/features.js
// (window.LSD_FEATURES). Same ids/labels and Simple / More / Everything
// rules as LanguageStudentDesk. Settings are kept in localStorage.
//
//   SquirrelFeatures.isOn("historical")
//   SquirrelFeatures.allows(meta)
//   SquirrelFeatures.renderSettings(el)
//   SquirrelFeatures.onChange(fn)
(function () {
  "use strict";

  const DATA = window.LSD_FEATURES || { levels: [], features: [], featured: [], text: {}, defaultLevel: "simple" };
  const KEY = "squirrelator-settings";
  const LEVELS = DATA.levels.map((l) => l.id);
  const FEATURES = DATA.features.slice();
  const TEXT = Object.assign(
    { notice: "", welcomeTitle: "Welcome", welcomeBody: "", whatsInApp: "What's in the app", customize: "Customize", custom: "Custom" },
    DATA.text || {}
  );
  // Same programming groups as squirrelator.features.LANGUAGE_REQUIRES.
  const LANGUAGE_REQUIRES = {
    quickbasic: "programming-older",
    z80: "programming-older",
    brainfood: "programming-joke",
    lolcode: "programming-joke",
  };
  const listeners = [];

  function rank(level) {
    const i = LEVELS.indexOf(level);
    return i < 0 ? 0 : i;
  }

  function onAtLevel(feature, level) {
    return rank(feature.level) <= rank(level);
  }

  function blank() {
    return { level: DATA.defaultLevel || LEVELS[0] || "simple", switches: {}, noticeDismissed: false, welcomeDone: false };
  }

  function clean(s) {
    const out = blank();
    if (s && typeof s === "object") {
      if (s.level === "custom" || LEVELS.includes(s.level)) out.level = s.level;
      if (s.switches && typeof s.switches === "object") {
        for (const f of FEATURES) if (typeof s.switches[f.id] === "boolean") out.switches[f.id] = s.switches[f.id];
      }
      out.noticeDismissed = !!s.noticeDismissed;
      out.welcomeDone = !!s.welcomeDone;
    }
    return out;
  }

  function loadLocal() {
    try {
      return JSON.parse(localStorage.getItem(KEY));
    } catch (e) {
      return null;
    }
  }

  let state = clean(loadLocal());

  function save() {
    try {
      localStorage.setItem(KEY, JSON.stringify(state));
    } catch (e) {}
    listeners.forEach((fn) => {
      try {
        fn(state);
      } catch (e) {}
    });
  }

  function isOn(id) {
    const f = FEATURES.find((x) => x.id === id);
    if (!f) return false;
    if (state.level === "custom") return state.switches[id] === true;
    return onAtLevel(f, state.level);
  }

  function allows(item) {
    const req = item && item.requires;
    if (!req) return true;
    return (Array.isArray(req) ? req : [req]).every(isOn);
  }

  function allowsLanguage(lang) {
    const req = LANGUAGE_REQUIRES[lang];
    return allows(req ? { requires: req } : {});
  }

  function level() {
    return state.level;
  }

  function setLevel(id) {
    if (!LEVELS.includes(id)) return;
    state.level = id;
    state.switches = {};
    save();
  }

  function set(id, on) {
    const now = {};
    for (const f of FEATURES) now[f.id] = isOn(f.id);
    now[id] = !!on;
    const match = LEVELS.find((l) => FEATURES.every((f) => now[f.id] === onAtLevel(f, l)));
    if (match) {
      state.level = match;
      state.switches = {};
    } else {
      state.level = "custom";
      state.switches = now;
    }
    save();
  }

  function onChange(fn) {
    listeners.push(fn);
  }

  function el(tag, attrs, children) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (k === "text") node.textContent = v;
      else if (k === "class") node.className = v;
      else if (k.startsWith("on")) node[k] = v;
      else node.setAttribute(k, v);
    }
    (children || []).forEach((c) => c && node.appendChild(c));
    return node;
  }

  function customizeOrder() {
    return FEATURES.slice().sort((a, b) => String(b.added).localeCompare(String(a.added)) || a.label.localeCompare(b.label));
  }

  function renderNotice(container, openSettings) {
    container.innerHTML = "";
    if (state.noticeDismissed || !TEXT.notice) {
      container.hidden = true;
      return;
    }
    container.hidden = false;
    container.appendChild(
      el("div", { class: "sqf-notice", role: "note" }, [
        el("span", { text: TEXT.notice + " " }),
        openSettings ? el("button", { type: "button", class: "sqf-link", text: "Open Settings", onclick: openSettings }) : null,
        el("button", {
          type: "button",
          class: "sqf-close",
          "aria-label": "Dismiss",
          text: "×",
          onclick: () => {
            state.noticeDismissed = true;
            save();
            renderNotice(container, openSettings);
          },
        }),
      ])
    );
  }

  function renderSettings(container) {
    const draw = () => {
      container.innerHTML = "";
      const levels = el("fieldset", { class: "sqf-levels" }, [el("legend", { text: "Show" })]);
      DATA.levels.forEach((l) => {
        const input = el("input", { type: "radio", name: "sqf-level", value: l.id });
        input.checked = state.level === l.id;
        input.onchange = () => setLevel(l.id);
        levels.appendChild(el("label", { class: "sqf-row" }, [input, el("span", {}, [el("strong", { text: l.label }), el("small", { text: l.description })])]));
      });
      if (state.level === "custom") levels.appendChild(el("p", { class: "sqf-custom", text: TEXT.custom }));
      container.appendChild(levels);

      const custom = el("fieldset", { class: "sqf-switches" }, [el("legend", { text: TEXT.customize })]);
      customizeOrder().forEach((f) => {
        const input = el("input", { type: "checkbox" });
        input.checked = isOn(f.id);
        input.onchange = () => set(f.id, input.checked);
        custom.appendChild(el("label", { class: "sqf-row" }, [input, el("span", {}, [el("strong", { text: f.label }), el("small", { text: f.description })])]));
      });
      container.appendChild(custom);

      const box = el("section", { class: "sqf-whats" }, [el("h2", { text: TEXT.whatsInApp })]);
      const list = el("ul", {});
      FEATURES.slice()
        .sort((a, b) => a.label.localeCompare(b.label))
        .forEach((f) => {
          const off = !isOn(f.id);
          list.appendChild(
            el("li", {}, [
              el("strong", { text: f.label }),
              el("span", { class: off ? "sqf-off" : "sqf-on", text: off ? " (off: turn on " + f.label + " in Customize)" : " (on)" }),
              el("small", { text: f.description }),
            ])
          );
        });
      box.appendChild(list);
      container.appendChild(box);
    };
    draw();
    onChange(draw);
  }

  window.SquirrelFeatures = {
    data: DATA,
    isOn,
    allows,
    allowsLanguage,
    level,
    setLevel,
    set,
    onChange,
    renderNotice,
    renderSettings,
  };
})();
