/* Approval Workflow Improvement: interactive walk-through.
   Every number comes from data/site.json, built by analysis/04_site_data.py. */
(function () {
  "use strict";
  var REDUCED = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var GH = "https://github.com/VimleshSonawane/business-flow-improvement/blob/main/";
  var TABLEAU = "https://public.tableau.com/app/profile/vimlesh.vilas.sonawane/viz/ApprovalWorkflowBaselineBPI2020realdata/Baselinedashboard";
  var D, SC = {};

  /* ---------- helpers ---------- */
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function h(tag, attrs, kids) {
    var e = document.createElement(tag);
    for (var k in attrs || {}) {
      if (k === "text") e.textContent = attrs[k];
      else if (k === "html") e.innerHTML = attrs[k];
      else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), attrs[k]);
      else if (attrs[k] !== null && attrs[k] !== undefined && attrs[k] !== false) e.setAttribute(k, attrs[k]);
    }
    (kids || []).forEach(function (c) { if (c) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return e;
  }
  var SVGNS = "http://www.w3.org/2000/svg";
  function s(tag, attrs, kids) {
    var e = document.createElementNS(SVGNS, tag);
    for (var k in attrs || {}) {
      if (k === "text") e.textContent = attrs[k];
      else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), attrs[k]);
      else e.setAttribute(k, attrs[k]);
    }
    (kids || []).forEach(function (c) { if (c) e.appendChild(c); });
    return e;
  }
  function fmt(v, d) {
    if (v === null || v === undefined) return "–";
    return Number(v).toLocaleString("en-US", { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 });
  }
  function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function get(path) {
    return path.split(".").reduce(function (o, k) { return o == null ? o : o[k]; }, { baseline: D.baseline, scen: SC, raw: D.raw, targets: D.targets });
  }
  function day(iso) {
    var p = iso.split("-");
    return new Date(Date.UTC(+p[0], +p[1] - 1, +p[2])).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });
  }
  function shortDay(iso) {
    var p = iso.split("-");
    return new Date(Date.UTC(+p[0], +p[1] - 1, +p[2])).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
  }

  /* ---------- bound values and count-up ---------- */
  function bindValues() {
    $$("[data-v]").forEach(function (e) {
      var v = get(e.getAttribute("data-v")), f = e.getAttribute("data-f"), suf = e.getAttribute("data-suffix") || "";
      e.textContent = (f === null ? v : fmt(v, f === "int" ? 0 : +f)) + suf;
    });
    var tiles = $$("[data-count]");
    function show(e, t) {
      var v = get(e.getAttribute("data-count")), d = +e.getAttribute("data-d"), suf = e.getAttribute("data-suffix") || "";
      e.textContent = fmt(v * t, d) + suf;
    }
    tiles.forEach(function (e) { show(e, 1); });
    if (REDUCED || !("IntersectionObserver" in window)) return;
    tiles.forEach(function (e) { show(e, 0); });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        io.unobserve(en.target);
        var e = en.target, t0 = performance.now();
        (function step(now) {
          var t = Math.min(1, (now - t0) / 900);
          show(e, 1 - Math.pow(1 - t, 3));
          if (t < 1) requestAnimationFrame(step);
        })(t0);
      });
    }, { threshold: 0.4 });
    tiles.forEach(function (e) { io.observe(e); });
  }

  /* ---------- sticky nav highlight ---------- */
  function navHighlight() {
    var links = $$("#navlinks a"), bar = $("#navlinks");
    if (!("IntersectionObserver" in window)) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        links.forEach(function (a) {
          var on = a.getAttribute("href") === "#" + en.target.id;
          a.classList.toggle("active", on);
          if (on) { a.setAttribute("aria-current", "true"); bar.scrollLeft = a.offsetLeft - bar.clientWidth / 2 + a.clientWidth / 2; }
          else a.removeAttribute("aria-current");
        });
      });
    }, { rootMargin: "-40% 0px -55% 0px" });
    $$("main > .section[id]").forEach(function (sec) { io.observe(sec); });
  }

  /* ---------- tabs (keyboard: arrows, Home, End) ---------- */
  function tabs(list, names, render) {
    var btns = names.map(function (n, i) {
      return h("button", { type: "button", role: "tab", id: list.id + "-" + i, "aria-selected": i === 0 ? "true" : "false",
        tabindex: i === 0 ? "0" : "-1", text: n, onclick: function () { select(i); } });
    });
    btns.forEach(function (b) { list.appendChild(b); });
    function select(i, focus) {
      btns.forEach(function (b, j) { b.setAttribute("aria-selected", j === i ? "true" : "false"); b.tabIndex = j === i ? 0 : -1; });
      if (focus) btns[i].focus();
      render(i, btns[i].id);
    }
    list.addEventListener("keydown", function (ev) {
      var i = btns.indexOf(document.activeElement); if (i < 0) return;
      var n = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: btns.length - 1 }[ev.key];
      if (n === undefined) return;
      ev.preventDefault(); select((n + btns.length) % btns.length, true);
    });
    select(0);
  }

  /* ---------- screenshots and zoom dialog ---------- */
  var SHOTS = {
    "smartsheet-1-gantt": "Schedule (Gantt chart) with phases, dependencies and milestones",
    "smartsheet-2-raid": "RAID log: risks, assumptions, issues and decisions",
    "smartsheet-3-dashboard": "Project dashboard for the sponsor",
    "smartsheet-4-progress": "Progress by phase and task",
    "smartsheet-5-roadmap": "Implementation roadmap: Wave 1 and Wave 2 (D7)",
    "smartsheet-6-control-plan": "Control plan: measures, targets, alerts and owners (D7)",
    "asana-1-list": "Task list by phase, tagged with deliverables and evidence",
    "asana-2-board": "Board view of the same tasks",
    "asana-3-form": "Change request form",
    "asana-4-automation": "Automation rule for change requests",
    "asana-5-change-request": "A change request being handled",
    "asana-6-status": "Weekly status update",
    "asana-7-miro-done": "Task list with the Miro deliverables done",
    "miro-1-overview-stakeholders": "Board overview and stakeholder map (D2)",
    "miro-2-raci": "Who does what: the RACI chart (D2)",
    "miro-3-asis-map": "As-is process map (D4)",
    "miro-4-asis-loops": "As-is map with the rejection loops (D4)",
    "miro-5-fishbon": "Fishbone root-cause analysis (D5)",
    "miro-6-impact-effort": "Fixes scored for impact and effort (D6)",
    "miro-7-tobe": "To-be process with the three fixes (D6)",
    "tableau-6-dashboard": "Baseline dashboard (D3)",
    "tableau-1-cycle-time": "Days to payment",
    "tableau-2-wait-by-step": "Wait before each step",
    "tableau-3-rejections": "Rejections by role",
    "tableau-4-monthly": "Monthly volume",
    "tableau-5-kpis": "Baseline KPIs"
  };
  var zoomList = [], zoomAt = 0, zoomOpener = null;
  function shotFig(name, list) {
    var src = "files/screenshots/" + name;
    var btn = h("button", { type: "button", "aria-label": "Enlarge: " + SHOTS[name] }, [
      h("img", { src: src + "-thumb.webp", alt: SHOTS[name], loading: "lazy", decoding: "async", width: "640", height: "360" })
    ]);
    btn.addEventListener("click", function () { openZoom(list, list.indexOf(name), btn); });
    return h("figure", { class: "shot" }, [btn, h("figcaption", { text: SHOTS[name] })]);
  }
  function gallery(names, cls) {
    var g = h("div", { class: "grid " + (cls || "gallery") });
    names.forEach(function (n) { g.appendChild(shotFig(n, names)); });
    return g;
  }
  function showZoom() {
    var n = zoomList[zoomAt], src = "files/screenshots/" + n + ".webp";
    $("#zoom-img").src = src; $("#zoom-img").alt = SHOTS[n];
    $("#zoom-cap").textContent = SHOTS[n] + " (" + (zoomAt + 1) + " of " + zoomList.length + ")";
    $("#zoom-open").href = src;
  }
  function openZoom(list, i, opener) {
    zoomList = list; zoomAt = i; zoomOpener = opener; showZoom();
    var d = $("#zoom");
    if (d.showModal) d.showModal(); else window.open($("#zoom-open").href, "_blank");
  }
  function initZoom() {
    var d = $("#zoom");
    $("#zoom-prev").onclick = function () { zoomAt = (zoomAt - 1 + zoomList.length) % zoomList.length; showZoom(); };
    $("#zoom-next").onclick = function () { zoomAt = (zoomAt + 1) % zoomList.length; showZoom(); };
    $("#zoom-close").onclick = function () { d.close(); };
    d.addEventListener("close", function () { if (zoomOpener) zoomOpener.focus(); });
    d.addEventListener("click", function (ev) { if (ev.target === d) d.close(); });
    d.addEventListener("keydown", function (ev) {
      if (ev.key === "ArrowLeft") $("#zoom-prev").click();
      if (ev.key === "ArrowRight") $("#zoom-next").click();
    });
  }

  /* ---------- journey ---------- */
  function journey() {
    var ph = [
      { name: "Define", what: "Agree the problem, the goal, the scope and who is involved.",
        deliv: [["D1", "Project charter", GH + "docs/charter.md"], ["D2", "Stakeholder map and RACI", null]],
        tools: ["GitHub", "Miro", "Smartsheet", "Asana"], shots: ["miro-1-overview-stakeholders", "miro-2-raci"] },
      { name: "Measure", what: "Clean the real data and measure how the process performs today.",
        deliv: [["D3", "Baseline KPI report and Tableau dashboard", GH + "docs/baseline-kpi-report.md"]],
        tools: ["Python", "Tableau"], shots: ["tableau-6-dashboard", "tableau-1-cycle-time"] },
      { name: "Analyze", what: "Map the real flow, find the bottlenecks and their causes.",
        deliv: [["D4", "As-is process map", null], ["D5", "Root-cause analysis (fishbone)", null]],
        tools: ["Miro", "Python"], shots: ["miro-4-asis-loops", "miro-5-fishbon"] },
      { name: "Improve", what: "Choose fixes, draw the new process and estimate the effect.",
        deliv: [["D6", "To-be process and prioritized fixes", GH + "docs/findings-and-business-case.md"]],
        tools: ["Miro", "Python"], shots: ["miro-6-impact-effort", "miro-7-tobe"] },
      { name: "Control", what: "Plan the rollout and how the gains would be kept, then present.",
        deliv: [["D7", "Implementation roadmap and control plan", null], ["D8", "Final presentation", "files/approval-workflow-final-presentation.pdf"]],
        tools: ["Smartsheet", "PowerPoint"], shots: ["smartsheet-5-roadmap", "smartsheet-6-control-plan"] }
    ];
    var panel = $("#journey-panel");
    tabs($("#journey-tabs"), ph.map(function (p) { return p.name; }), function (i, id) {
      var p = ph[i]; panel.setAttribute("aria-labelledby", id); panel.innerHTML = "";
      var left = h("div", {}, [
        h("p", { text: p.what }),
        h("h3", { class: "h3", text: "Deliverables" }),
        h("ul", { class: "deliv" }, p.deliv.map(function (d) {
          return h("li", {}, [h("b", { text: d[0] }), d[2] ? h("a", { href: d[2], text: d[1] }) : document.createTextNode(d[1])]);
        })),
        h("h3", { class: "h3", text: "Tools" }),
        h("div", { class: "chips" }, p.tools.map(function (t) { return h("span", { class: "chip", text: t }); }))
      ]);
      panel.appendChild(h("div", { class: "phase-grid" }, [left, gallery(p.shots, "thumbs")]));
    });
  }

  /* ---------- data pipeline ---------- */
  function pipeline() {
    var box = $("#pipeline"), panel = $("#pipeline-panel"), btns = [];
    D.pipeline.forEach(function (p, i) {
      var b = h("button", { type: "button", "aria-pressed": i === 0 ? "true" : "false", "aria-controls": "pipeline-panel",
        onclick: function () { select(i); } }, [document.createTextNode(p.name), h("small", { text: p.file || "Tableau Public" })]);
      btns.push(b);
      box.appendChild(h("div", { class: "pipe" }, [b, i < D.pipeline.length - 1 ? h("span", { class: "arr", "aria-hidden": "true", text: "→" }) : null]));
    });
    function select(i) {
      btns.forEach(function (b, j) { b.setAttribute("aria-pressed", j === i ? "true" : "false"); });
      var p = D.pipeline[i]; panel.innerHTML = "";
      panel.appendChild(h("h3", { class: "h3", text: p.name }));
      panel.appendChild(h("p", { text: p.does }));
      var dl = h("dl", { class: "facts" });
      if (p.id === "checksum") {
        dl.appendChild(h("dt", { text: "Size" })); dl.appendChild(h("dd", { text: fmt(D.raw.size_bytes) + " bytes" }));
        dl.appendChild(h("dt", { text: "MD5" })); dl.appendChild(h("dd", {}, [h("code", { text: D.raw.md5 })]));
        dl.appendChild(h("dt", { text: "Result" })); dl.appendChild(h("dd", { text: D.raw.check }));
      }
      for (var k in p.rows || {}) { dl.appendChild(h("dt", { text: k.replace(/_/g, " ") })); dl.appendChild(h("dd", { text: fmt(p.rows[k]) })); }
      if (p.decision) {
        dl.appendChild(h("dt", { text: "Decision" }));
        dl.appendChild(h("dd", {}, [h("a", { href: GH + p.decision.source, text: p.decision.title }),
          document.createTextNode(" (" + p.decision.source.replace("docs/", "") + ", no. " + p.decision.id + ")")]));
      }
      if (dl.children.length) panel.appendChild(dl);
      if (p.excerpt) {
        panel.appendChild(h("p", { class: "note", text: "Excerpt, copied unchanged from " + p.excerpt.file + ", lines " + p.excerpt.start_line + "–" + p.excerpt.end_line + ":" }));
        panel.appendChild(h("pre", {}, [h("code", { text: p.excerpt.code })]));
      }
      panel.appendChild(h("p", { style: "margin-top:12px" }, [h("a", { class: "btn", href: p.excerpt ? p.excerpt.url : p.url,
        text: p.file ? "View on GitHub" : "Open the dashboard" })]));
    }
    select(0);
  }

  /* ---------- process map ---------- */
  var A = {
    SUB: "Declaration SUBMITTED by EMPLOYEE", ADM: "Declaration APPROVED by ADMINISTRATION",
    BO: "Declaration APPROVED by BUDGET OWNER", SUP: "Declaration FINAL_APPROVED by SUPERVISOR",
    REQ: "Request Payment", PAY: "Payment Handled", RA: "Declaration REJECTED by ADMINISTRATION",
    RB: "Declaration REJECTED by BUDGET OWNER", RS: "Declaration REJECTED by SUPERVISOR",
    RE: "Declaration REJECTED by EMPLOYEE", CL: "END"
  };
  function trans(a, b) { return D.transitions.filter(function (t) { return t.from === A[a] && t.to === A[b]; })[0]; }
  function processMap() {
    var svg = $("#pmap"), W = 1100, LH = 98, LT = [10, 118, 226, 334, 442];
    svg.setAttribute("viewBox", "0 0 " + W + " 548");
    var lanes = ["Employee", "Administration", "Budget owner", "Supervisor", "Payments"];
    function cy(l) { return LT[l] + LH / 2 + 4; }
    var N = {
      RE: { x: 230, y: cy(0), lane: 0, t: "Employee responds", w: 140, reject: true },
      SUB: { x: 450, y: cy(0), lane: 0, t: "Submit claim", w: 124 },
      RA: { x: 230, y: cy(1), lane: 1, t: "Rejected", w: 100, reject: true },
      ADM: { x: 610, y: cy(1), lane: 1, t: "Approve", w: 110 },
      RB: { x: 230, y: cy(2), lane: 2, t: "Rejected", w: 100, reject: true },
      BO: { x: 770, y: cy(2), lane: 2, t: "Approve", w: 110 },
      RS: { x: 230, y: cy(3), lane: 3, t: "Rejected", w: 100, reject: true },
      SUP: { x: 860, y: cy(3), lane: 3, t: "Final approval", w: 124 },
      REQ: { x: 860, y: cy(4), lane: 4, t: "Payment request", w: 136 },
      PAY: { x: 1040, y: cy(4), lane: 4, t: "Payment run", w: 104 }
    };
    // [from, to, loop, from side, to side] or a return channel at x for loops back to the employee
    var E = [["SUB", "ADM", 0, "r", "t"], ["ADM", "BO", 0, "r", "t"], ["ADM", "SUP", 0, "b", "l"], ["BO", "SUP", 0, "r", "t"],
      ["SUP", "REQ", 0, "b", "t"], ["REQ", "PAY", 0, "r", "l"],
      ["SUB", "RA", 1, "b", "r"], ["ADM", "RB", 1, "l", "r"], ["ADM", "RS", 1, "l", "r"], ["BO", "RS", 1, "l", "r"],
      ["RA", "RE", 1, "t", "b"], ["RB", "RE", 1, "ch", 140], ["RS", "RE", 1, "ch", 126], ["RE", "SUB", 1, "r", "l"]];
    var HOT = { "REQ>PAY": "B1", RA: "B2", RS: "B3" };
    function mk(id, col) { return s("marker", { id: id, viewBox: "0 0 10 10", refX: "9", refY: "5", markerWidth: "7", markerHeight: "7", orient: "auto-start-reverse" }, [s("path", { d: "M0,0 L10,5 L0,10 z", fill: col })]); }
    svg.appendChild(s("defs", {}, [mk("ah", "var(--accent)"), mk("ahl", "var(--loop)"), mk("ahh", "var(--bad)")]));
    lanes.forEach(function (l, i) {
      svg.appendChild(s("rect", { class: "lane", x: 0, y: LT[i], width: W, height: LH - 6, rx: 8 }));
      svg.appendChild(s("text", { class: "lane-label", x: 12, y: LT[i] + 20, text: l }));
    });
    function side(n, sd) {
      var hw = n.w / 2, hh = 17;
      return { r: [n.x + hw, n.y, 1, 0], l: [n.x - hw, n.y, -1, 0], t: [n.x, n.y - hh, 0, -1], b: [n.x, n.y + hh, 0, 1] }[sd];
    }
    var panel = $("#map-panel"), selected = null;
    function choose(g, html) {
      if (selected) selected.classList.remove("sel");
      selected = g; g.classList.add("sel"); panel.innerHTML = html;
    }
    function wait(step) { return D.waits.filter(function (w) { return w.step === step; })[0]; }
    function rej(role) { return D.rejections.filter(function (r) { return r.role === role; })[0]; }
    function activate(g, fn) {
      g.addEventListener("click", fn);
      g.addEventListener("keydown", function (ev) { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); fn(); } });
    }
    E.forEach(function (e) {
      var t = trans(e[0], e[1]); if (!t) return;
      var a = N[e[0]], b = N[e[1]], d, mx, my;
      if (e[3] === "ch") {
        var xc = e[4], p0 = side(a, "l"), q0 = side(b, "l");
        d = "M" + p0[0] + "," + p0[1] + " H" + xc + " V" + (q0[1] + 6) + " H" + (q0[0] - 1);
        mx = xc; my = (p0[1] + q0[1]) / 2 + (xc === 140 ? 30 : 80);
      } else {
        var p = side(a, e[3]), q = side(b, e[4]);
        var len = Math.max(30, Math.hypot(q[0] - p[0], q[1] - p[1]) * 0.35);
        var c1 = [p[0] + p[2] * len, p[1] + p[3] * len], c2 = [q[0] - q[2] * len, q[1] - q[3] * len];
        if (e[4] === "t" || e[4] === "b") c2 = [q[0], q[1] + (e[4] === "t" ? -len : len)];
        if (e[4] === "l" || e[4] === "r") c2 = [q[0] + (e[4] === "l" ? -len : len), q[1]];
        d = "M" + p[0] + "," + p[1] + " C" + c1 + " " + c2 + " " + q[0] + "," + q[1];
        mx = 0.125 * p[0] + 0.375 * c1[0] + 0.375 * c2[0] + 0.125 * q[0];
        my = 0.125 * p[1] + 0.375 * c1[1] + 0.375 * c2[1] + 0.125 * q[1];
      }
      var key = e[0] + ">" + e[1], hot = HOT[key], loop = !!e[2];
      var g = s("g", { class: "edge" + (loop ? " loop loopy" : "") + (hot ? " hot" : ""), tabindex: "0", role: "button",
        "aria-label": a.t + " (" + lanes[a.lane] + ") to " + b.t + " (" + lanes[b.lane] + "): " + fmt(t.cases) + " claims" }, [
        s("path", { class: "hit", d: d }),
        s("path", { class: "vis", d: d, "marker-end": "url(#" + (hot ? "ahh" : loop ? "ahl" : "ah") + ")" }),
        s("text", { x: mx + (e[3] === "ch" ? 4 : 0), y: my - (hot ? 24 : 5), "text-anchor": e[3] === "ch" ? "start" : "middle", text: fmt(t.cases) + (hot ? " · " + hot : "") })
      ]);
      activate(g, function () {
        choose(g, "<h3 class='h3'>" + esc(a.t) + " → " + esc(b.t) + "</h3><p class='muted'>" + lanes[a.lane] + " → " + lanes[b.lane] + "</p>" +
          "<dl class='facts'><dt>Claims</dt><dd>" + fmt(t.cases) + "</dd><dt>Times it happened</dt><dd>" + fmt(t.transitions) + "</dd>" +
          (t.median_days !== null ? "<dt>Typical wait (median)</dt><dd>" + fmt(t.median_days, 2) + " days</dd><dt>Slowest 10% (P90)</dt><dd>" + fmt(t.p90_days, 2) + " days</dd>" : "") +
          "</dl><p class='note'>Complete 2018 claims. Source: transitions.csv.</p>");
      });
      svg.appendChild(g);
    });
    var closed = trans("RE", "CL");
    svg.appendChild(s("text", { class: "lane-label loopy", x: 300, y: N.RE.y + 34, "font-weight": "400", text: "↳ " + fmt(closed.cases) + " closed without payment" }));
    var roleOf = { ADM: "ADMINISTRATION", BO: "BUDGET OWNER", SUP: "SUPERVISOR", REQ: "Request Payment", PAY: "Payment Handled" };
    var rejOf = { RA: "ADMINISTRATION", RB: "BUDGET OWNER", RS: "SUPERVISOR" };
    Object.keys(N).forEach(function (k) {
      var n = N[k], hot = HOT[k];
      var g = s("g", { class: "node" + (n.reject ? " reject loopy" : "") + (hot ? " hot" : ""), tabindex: "0", role: "button", "aria-label": n.t + " (" + lanes[n.lane] + ")" }, [
        s("rect", { x: n.x - n.w / 2, y: n.y - 17, width: n.w, height: 34, rx: 8 }),
        s("text", { x: n.x, y: n.y, text: n.t })
      ]);
      if (hot) g.appendChild(s("text", { class: "tag", x: n.x + n.w / 2 - 4, y: n.y - 22, "text-anchor": "end", text: hot }));
      var info = function () {
        var html = "<h3 class='h3'>" + esc(n.t) + " <span class='muted'>· " + lanes[n.lane] + "</span></h3><dl class='facts'>";
        var incoming = D.transitions.filter(function (t) { return t.to === A[k]; })
          .reduce(function (sum, t) { return sum + t.transitions; }, 0);
        if (!n.reject) html += "<dt>Times this step happened</dt><dd>" + fmt(incoming) + " (complete claims)</dd>";
        if (k === "RE") html += "<dt>Closed without payment</dt><dd>" + fmt(trans("RE", "CL").cases) + " claims</dd>";
        var w = roleOf[k] && wait(roleOf[k]);
        if (w) html += "<dt>Typical wait before it</dt><dd>" + fmt(w.median_days, 2) + " days</dd><dt>Slowest 10% (P90)</dt><dd>" + fmt(w.p90_days, 2) + " days</dd>";
        var r = rejOf[k] && rej(rejOf[k]);
        if (r) {
          html += "<dt>Rejections</dt><dd>" + fmt(r.rejections) + " in " + fmt(r.cases_with_rejection) + " claims</dd><dt>Rate</dt><dd>" + fmt(r.per_100, 2) + " per 100 claims reaching this role</dd>";
          var x = D.rework_extra[rejOf[k]];
          if (x) html += "<dt>Extra time to pay</dt><dd>+" + fmt(x.extra_days, 2) + " days (median, " + fmt(x.paid_cases) + " paid claims)</dd>";
        }
        html += "</dl>";
        if (k === "ADM") html += "<p class='note'>This step is recorded by the system a median of " + fmt(D.baseline.admin_median_seconds.value) + " seconds after submission, so it is not real review time (decision 5).</p>";
        choose(g, html);
      };
      activate(g, info);
      svg.appendChild(g);
    });
    $("#loops-toggle").addEventListener("change", function () { svg.classList.toggle("noloops", !this.checked); });

    var pw = wait("Payment Handled"), ra = rej("ADMINISTRATION"), rs = rej("SUPERVISOR");
    $("#bottlenecks").innerHTML = "<h3 class='h3'>The three bottlenecks</h3>" +
      "<div class='bn'><span class='badge bad'>B1</span><div><b>Payment run</b><br>Longest median wait, " + fmt(pw.median_days, 2) + " d; payments run in Monday/Thursday batches.</div></div>" +
      "<div class='bn'><span class='badge bad'>B2</span><div><b>Administration rejects</b><br>" + fmt(ra.rejections) + " rejections (" + fmt(ra.cases_with_rejection) + " claims); +" + fmt(D.rework_extra.ADMINISTRATION.extra_days, 2) + " d when it happens.</div></div>" +
      "<div class='bn'><span class='badge bad'>B3</span><div><b>Supervisor rejects</b><br>Only " + fmt(rs.rejections) + " (" + fmt(rs.cases_with_rejection) + " claims), but +" + fmt(D.rework_extra.SUPERVISOR.extra_days, 2) + " d each.</div></div>" +
      "<p class='note'>Administration's step is system-recorded (median " + fmt(D.baseline.admin_median_seconds.value) + " seconds after submission): a data limitation, not review speed (decision 5). Numbers on arrows are claims.</p>";
  }

  /* ---------- charts ---------- */
  var tip;
  function showTip(text, x, y) {
    tip.textContent = text; tip.hidden = false;
    var r = tip.getBoundingClientRect();
    tip.style.left = Math.max(8, Math.min(window.innerWidth - r.width - 8, x + 12)) + "px";
    tip.style.top = Math.max(8, y - r.height - 12) + "px";
  }
  function hideTip() { tip.hidden = true; }
  function hook(el, text, focusable) {
    if (focusable) { el.setAttribute("tabindex", "0"); el.setAttribute("role", "img"); el.setAttribute("aria-label", text); }
    el.addEventListener("pointermove", function (ev) { showTip(text, ev.clientX, ev.clientY); });
    el.addEventListener("pointerdown", function (ev) { showTip(text, ev.clientX, ev.clientY); });
    el.addEventListener("pointerleave", hideTip);
    el.addEventListener("focus", function () { var r = el.getBoundingClientRect(); showTip(text, r.left + r.width / 2, r.top); });
    el.addEventListener("blur", hideTip);
  }
  function legend(items) {
    return h("div", { class: "ch-legend" }, items.map(function (it) {
      return h("span", {}, [h("i", { style: "background:" + it[1] }), document.createTextNode(it[0])]);
    }));
  }
  /* Vertical bars: cats, series [{name, color, values}], stacked */
  function vbars(box, cats, series, o) {
    var W = o.w || 560, H = o.h || 240, L = 44, B = 28, T = 10, R = 8;
    var tot = cats.map(function (_, i) { return series.reduce(function (sm, se) { return sm + se.values[i]; }, 0); });
    var max = Math.max.apply(null, tot), step = Math.pow(10, Math.floor(Math.log10(max))), nice = Math.ceil(max / step) * step;
    if (nice / step < 4) step /= 2;
    var svg = s("svg", { viewBox: "0 0 " + W + " " + H, role: "group", "aria-label": o.label });
    for (var g = 0; g <= nice; g += step) {
      var gy = T + (H - T - B) * (1 - g / nice);
      svg.appendChild(s("line", { class: "grid-l", x1: L, x2: W - R, y1: gy, y2: gy }));
      svg.appendChild(s("text", { class: "axis", x: L - 6, y: gy + 4, "text-anchor": "end", text: fmt(g) }));
    }
    var bw = (W - L - R) / cats.length;
    cats.forEach(function (c, i) {
      var y0 = H - B;
      series.forEach(function (se) {
        var v = se.values[i], hh = (H - T - B) * v / nice;
        var r = s("rect", { class: "bar", x: L + i * bw + bw * 0.12, y: y0 - hh, width: Math.max(1, bw * 0.76), height: Math.max(0, hh), fill: se.color, rx: bw > 14 ? 3 : 1 });
        hook(r, o.tip(c, se, v, i), cats.length <= 14);
        svg.appendChild(r); y0 -= hh;
      });
      if (!o.every || i % o.every === 0 || i === cats.length - 1)
        svg.appendChild(s("text", { class: "axis", x: L + i * bw + bw / 2, y: H - B + 16, "text-anchor": "middle", text: o.catLabel ? o.catLabel(c, i) : c }));
    });
    if (o.xTitle) svg.appendChild(s("text", { class: "axis", x: W - R, y: H - 2, "text-anchor": "end", text: o.xTitle }));
    box.appendChild(svg);
    if (series.length > 1) box.appendChild(legend(series.map(function (se) { return [se.name, se.color]; })));
  }
  /* Horizontal grouped bars */
  function hbars(box, cats, series, o) {
    var W = 560, rowH = 46, L = 132, R = 56, T = 6, H = T + cats.length * rowH + 22;
    var max = Math.max.apply(null, series.map(function (se) { return Math.max.apply(null, se.values); }));
    var svg = s("svg", { viewBox: "0 0 " + W + " " + H, role: "group", "aria-label": o.label });
    var bh = (rowH - 12) / series.length;
    cats.forEach(function (c, i) {
      var y = T + i * rowH;
      svg.appendChild(s("text", { class: "lbl", x: L - 8, y: y + rowH / 2, "text-anchor": "end", "dominant-baseline": "middle", text: c }));
      series.forEach(function (se, j) {
        var v = se.values[i], w = (W - L - R) * v / max;
        var r = s("rect", { class: "bar", x: L, y: y + 4 + j * bh, width: Math.max(1, w), height: bh - 2, fill: se.color, rx: 3 });
        hook(r, c + " — " + se.name + ": " + fmt(v, 2) + " days", true);
        svg.appendChild(r);
        svg.appendChild(s("text", { class: "val", x: L + w + 4, y: y + 4 + j * bh + bh / 2, "dominant-baseline": "middle", text: fmt(v, 2) }));
      });
    });
    box.appendChild(svg);
    box.appendChild(legend(series.map(function (se) { return [se.name, se.color]; })));
  }
  function charts() {
    tip = $("#tip");
    document.addEventListener("scroll", hideTip, { passive: true });
    var css = getComputedStyle(document.documentElement);
    var c1 = css.getPropertyValue("--s1").trim(), c2 = css.getPropertyValue("--s2").trim(), bad = css.getPropertyValue("--bad").trim(), loop = css.getPropertyValue("--loop").trim();
    var cd = D.cycle_distribution;
    vbars($("#ch-dist"), cd.labels, [
      { name: "Never rejected", color: c1, values: cd.never_rejected },
      { name: "Rejected at least once", color: bad, values: cd.rejected }
    ], { label: "Paid claims by days to payment", every: 10, xTitle: "days to payment",
      tip: function (c, se, v) { return (c === "60+" ? "60 days or more" : c + "–" + (+c + 1) + " days") + " · " + se.name + ": " + fmt(v) + " claims"; } });
    var nameOf = { "ADMINISTRATION": "Administration", "BUDGET OWNER": "Budget owner", "SUPERVISOR": "Supervisor", "Request Payment": "Payment request", "Payment Handled": "Payment run" };
    hbars($("#ch-wait"), D.waits.map(function (w) { return nameOf[w.step]; }), [
      { name: "Median", color: c1, values: D.waits.map(function (w) { return w.median_days; }) },
      { name: "Slowest 10% (P90)", color: c2, values: D.waits.map(function (w) { return w.p90_days; }) }
    ], { label: "Wait before each step" });
    vbars($("#ch-rej"), D.rejections.map(function (r) { return nameOf[r.role]; }), [{ name: "Rejections", color: bad, values: D.rejections.map(function (r) { return r.rejections; }) }],
      { label: "Rejections by role", tip: function (c, se, v, i) { var r = D.rejections[i]; return c + ": " + fmt(v) + " rejections in " + fmt(r.cases_with_rejection) + " claims · " + fmt(r.per_100, 2) + " per 100 claims reaching this role"; } });
    vbars($("#ch-week"), D.weekdays.map(function (w) { return w.day.slice(0, 3); }), [{ name: "Payments", color: c1, values: D.weekdays.map(function (w) { return w.payments; }) }],
      { label: "Payments by weekday", tip: function (c, se, v, i) { return D.weekdays[i].day + ": " + fmt(v) + " payments"; } });
    vbars($("#ch-month"), D.monthly.map(function (m) { return m.month; }), [
      { name: "First submissions", color: c1, values: D.monthly.map(function (m) { return m.first; }) },
      { name: "Resubmissions", color: loop, values: D.monthly.map(function (m) { return m.resubmissions; }) }
    ], { label: "Claims submitted each month", w: window.innerWidth < 700 ? 560 : 1100, h: 260,
      catLabel: function (c) { return new Date(c + "-01T00:00:00Z").toLocaleDateString("en-US", { month: "short", timeZone: "UTC" }); },
      tip: function (c, se, v, i) { var m = D.monthly[i]; return c + " · " + se.name + ": " + fmt(v) + " (total " + fmt(m.submissions) + ")"; } });
  }

  /* ---------- scenario explorer ---------- */
  function scenarios() {
    var map = { "": "Baseline", F1: "S1", F3: "S2", "F1+F3": "S3", F2: "S5", "F1+F2+F3": "S6" };
    var out = $("#scen-out"), base = SC.Baseline, tg = D.targets;
    var K = [
      { k: "p90_days", name: "Slowest 1 in 10 (P90)", unit: " days", d: 2, target: tg.p90_days, tl: "≤ " + fmt(tg.p90_days) + " days" },
      { k: "rejection_pct", name: "Claims rejected", unit: "%", d: 2, target: tg.rejection_pct, tl: "≤ " + fmt(tg.rejection_pct) + "%" },
      { k: "payment_wait_days", name: "Wait for the payment run", unit: " days", d: 2, target: tg.payment_wait_days, tl: "≤ " + fmt(tg.payment_wait_days) + " day" }
    ];
    function render() {
      var on = $$(".fixes input:checked").map(function (i) { return i.value; }).sort();
      var id = map[on.join("+")];
      out.innerHTML = "";
      if (!id) {
        out.appendChild(h("div", { class: "unmodelled" }, [h("b", { text: "This combination wasn't modelled." }),
          h("p", { class: "muted", style: "margin:6px 0 0", text: "Modelled combinations: none, F1, F2, F3, F1 + F3, and all three." })]));
        return;
      }
      var sc = SC[id], met = K.filter(function (k) { return sc[k.k] <= k.target; }).length;
      out.appendChild(h("div", { class: "scen-head" }, [
        h("b", { text: id === "Baseline" ? "Baseline: 2018 as measured" : "Scenario " + id }),
        h("span", { class: "badge " + (met === 3 ? "good" : met ? "info" : "bad"), text: met + " of 3 targets met" }),
        id !== "Baseline" ? h("span", { class: "badge warn", text: "What-if estimate" }) : null
      ]));
      K.forEach(function (k) {
        var max = Math.max(base[k.k], k.target) * 1.08, v = sc[k.k], ok = v <= k.target;
        out.appendChild(h("div", { class: "kbar" }, [
          h("div", { class: "lab" }, [h("b", { text: k.name }), h("span", { text: "Target " + k.tl })]),
          h("div", { class: "ktrack", role: "img", "aria-label": k.name + ": baseline " + fmt(base[k.k], k.d) + k.unit + ", this scenario " + fmt(v, k.d) + k.unit + ", target " + k.tl }, [
            h("div", { class: "b base", style: "width:" + (100 * base[k.k] / max) + "%" }),
            h("div", { class: "b now", style: "width:" + (100 * v / max) + "%;background:" + (ok ? "var(--good)" : "var(--accent)") }),
            h("div", { class: "tgt", style: "left:" + (100 * k.target / max) + "%" })
          ]),
          h("div", { class: "num" }, [document.createTextNode(fmt(base[k.k], k.d) + k.unit + " → "), h("b", { text: fmt(v, k.d) + k.unit }), document.createTextNode(" "),
            h("span", { class: "badge " + (ok ? "good" : "bad"), text: ok ? "met" : "not met" })])
        ]));
      });
      if (sc.rejection_pct !== sc.rejection_pct_all_submitted)
        out.appendChild(h("p", { class: "note", text: "Rejections over the " + fmt(sc.submitted_base) + " claims left after zero-amount claims are blocked (" + fmt(sc.rejection_pct_all_submitted, 2) + "% of all " + fmt(sc.submitted_all) + "). Grey bar = baseline; dashed line = target." }));
      else out.appendChild(h("p", { class: "note", text: "Rejections over " + fmt(sc.submitted_base) + " submitted claims. Grey bar = baseline; dashed line = target." }));
    }
    $$(".fixes input").forEach(function (i) { i.addEventListener("change", render); });
    render();
  }

  /* ---------- root causes (fishbone, docs/Screenshots/miro-5-fishbon.png) ---------- */
  function causes() {
    var w = function (st) { return D.waits.filter(function (x) { return x.step === st; })[0]; };
    var r = function (ro) { return D.rejections.filter(function (x) { return x.role === ro; })[0]; };
    var resub = trans("RE", "SUB");
    var C = [
      ["Approval chain", [
        ["proven", "An extra budget-owner approval on " + fmt(r("BUDGET OWNER").cases_reaching_role) + " of " + fmt(D.baseline.rejected_pct.denominator) + " claims"],
        ["proven", "Slow approvals: the slowest 10% wait " + fmt(w("BUDGET OWNER").p90_days, 2) + " days (budget owner) and " + fmt(w("SUPERVISOR").p90_days, 2) + " days (supervisor)"],
        ["hypothesis", "No approval limit below which a step could be skipped?"]]],
      ["Rejections", [
        ["proven", "Administration made " + fmt(r("ADMINISTRATION").rejections) + " rejections"],
        ["proven", "A supervisor rejection adds " + fmt(D.rework_extra.SUPERVISOR.extra_days, 2) + " days"],
        ["hypothesis", "Missing receipts?"]]],
      ["Payment timing", [
        ["proven", "Payments run in batches: " + fmt(D.baseline.mon_thu_pct.value, 2) + "% on a Monday or Thursday"],
        ["proven", "A median wait of " + fmt(w("Payment Handled").median_days, 2) + " days for the payment run"]]],
      ["Employees", [
        ["proven", "Resubmitting after a rejection: the slowest 10% take " + fmt(resub.p90_days, 2) + " days"],
        ["hypothesis", "Unclear claim rules?"]]],
      ["Approvers", [
        ["hypothesis", "No backup approver during absences?"],
        ["hypothesis", "Claims reviewed in batches?"]]],
      ["Data and controls", [
        ["proven", "Administration review time is hidden: the step is recorded by the system"],
        ["proven", fmt(D.exceptions.paid_without_final_approval.length) + " claims paid without final approval"]]]
    ];
    var box = $("#cause-cards");
    C.forEach(function (c) {
      box.appendChild(h("div", { class: "card cause" }, [h("h3", { text: c[0] }), h("ul", {}, c[1].map(function (it) {
        return h("li", { "data-kind": it[0] }, [h("span", { class: "badge " + (it[0] === "proven" ? "info" : "warn"), text: it[0] === "proven" ? "Data" : "Hypothesis" }), h("span", { text: it[1] })]);
      }))]));
    });
    var seg = $$("#cause-filter button");
    function apply(f) {
      seg.forEach(function (b) { b.setAttribute("aria-checked", b.getAttribute("data-filter") === f ? "true" : "false"); b.tabIndex = b.getAttribute("data-filter") === f ? 0 : -1; });
      $$(".cause").forEach(function (card) {
        var any = false;
        $$("li", card).forEach(function (li) { var show = f === "all" || li.getAttribute("data-kind") === f; li.hidden = !show; any = any || show; });
        card.hidden = !any;
      });
    }
    seg.forEach(function (b, i) {
      b.addEventListener("click", function () { apply(b.getAttribute("data-filter")); });
      b.addEventListener("keydown", function (ev) {
        var n = { ArrowRight: i + 1, ArrowLeft: i - 1 }[ev.key]; if (n === undefined) return;
        ev.preventDefault(); var t = seg[(n + seg.length) % seg.length]; t.focus(); apply(t.getAttribute("data-filter"));
      });
    });
    apply("all");
  }

  /* ---------- tools, milestones, roadmap, control plan, documents ---------- */
  function managed() {
    var T = [
      ["Smartsheet", "The schedule, the RAID log (risks, assumptions, issues, decisions), the sponsor dashboard, the roadmap and the control plan.", ["smartsheet-1-gantt", "smartsheet-2-raid", "smartsheet-3-dashboard", "smartsheet-4-progress", "smartsheet-5-roadmap", "smartsheet-6-control-plan"]],
      ["Asana", "Day-to-day tasks, change requests with a form and an automation rule, and weekly status updates.", ["asana-1-list", "asana-2-board", "asana-3-form", "asana-4-automation", "asana-5-change-request", "asana-6-status", "asana-7-miro-done"]],
      ["Miro", "The stakeholder map, the RACI, the as-is and to-be process maps, the fishbone and the impact/effort matrix.", ["miro-1-overview-stakeholders", "miro-2-raci", "miro-3-asis-map", "miro-4-asis-loops", "miro-5-fishbon", "miro-6-impact-effort", "miro-7-tobe"]],
      ["Tableau", "The interactive baseline dashboard built from the KPI files.", ["tableau-6-dashboard", "tableau-1-cycle-time", "tableau-2-wait-by-step", "tableau-3-rejections", "tableau-4-monthly", "tableau-5-kpis"]]
    ];
    var panel = $("#tools-panel");
    tabs($("#tools-tabs"), T.map(function (t) { return t[0]; }), function (i, id) {
      panel.setAttribute("aria-labelledby", id); panel.innerHTML = "";
      panel.appendChild(h("p", { class: "muted", text: T[i][1] }));
      if (T[i][0] === "Tableau") panel.appendChild(h("p", {}, [h("a", { class: "btn", href: TABLEAU, text: "Open the live dashboard" })]));
      panel.appendChild(gallery(T[i][2]));
    });
    var ms = $("#milestones");
    D.milestones.forEach(function (m) {
      ms.appendChild(h("li", {}, [h("b", { text: m.id + " · " + m.name }), h("span", { text: day(m.date) })]));
    });
    ms.insertAdjacentElement("afterend", h("p", { class: "note", text: "Dates from the project charter." }));

    var t0 = Date.UTC(2027, 0, 1), t1 = Date.UTC(2027, 3, 1);
    function pos(iso) { var p = iso.split("-"); return 100 * (Date.UTC(+p[0], +p[1] - 1, +p[2]) - t0) / (t1 - t0); }
    var wv = $("#waves"), waves = h("div", { class: "waves" });
    var axis = h("div", { class: "wave-axis", "aria-hidden": "true" }, ["2027-01-01", "2027-02-01", "2027-03-01", "2027-04-01"].map(function (d, i) {
      return h("span", { style: "left:" + pos(d) + "%" + (i === 0 ? ";transform:none" : i === 3 ? ";transform:translateX(-100%)" : ""), text: shortDay(d) });
    }));
    waves.appendChild(h("div", { class: "wave-row" }, [h("span"), axis]));
    D.waves.forEach(function (w, i) {
      var track = h("div", { class: "wave-track", role: "img", "aria-label": w.wave + ": " + day(w.start) + " to " + day(w.end) }, [
        h("div", { class: "wave-bar" + (i ? " w2" : ""), style: "left:" + pos(w.start) + "%;width:" + (pos(w.end) - pos(w.start)) + "%" })
      ]);
      waves.appendChild(h("div", { class: "wave-row" }, [h("div", {}, [h("b", { text: w.wave }), h("div", { class: "note", style: "margin:0", text: shortDay(w.start) + " – " + shortDay(w.end) })]), track]));
      waves.appendChild(h("div", { class: "wave-row" }, [h("span"), h("ul", { class: "wave-items" }, w.items.map(function (it) { return h("li", { text: it }); }))]));
    });
    var msTrack = h("div", { class: "wave-track", style: "background:transparent;height:14px" });
    D.wave_milestones.forEach(function (m) { msTrack.appendChild(h("div", { class: "wave-ms", style: "left:" + pos(m.date) + "%", title: m.id + " " + m.name })); });
    waves.appendChild(h("div", { class: "wave-row" }, [h("b", { text: "Milestones" }), msTrack]));
    wv.appendChild(waves);
    wv.appendChild(h("div", { class: "ms-list" }, D.wave_milestones.map(function (m) {
      return h("span", {}, [h("i", { "aria-hidden": "true" }), h("b", { text: m.id + " " }), document.createTextNode(m.name + " · " + day(m.date))]);
    })));
    wv.appendChild(h("p", { class: "note", text: "Proposed dates, from the Smartsheet roadmap. Nothing has been implemented." }));

    var tb = $("#control tbody");
    D.control_plan.forEach(function (c) {
      tb.appendChild(h("tr", {}, [h("th", { scope: "row", text: c.kpi }), h("td", { text: c.now }), h("td", { text: c.target }), h("td", { text: c.alert }), h("td", { text: c.owner })]));
    });

    var docs = [
      ["Final presentation (PDF)", "The full project story, from problem to control plan.", "files/approval-workflow-final-presentation.pdf", "Open PDF", "primary"],
      ["Final presentation (PowerPoint)", "The same deck as an editable .pptx file.", "files/approval-workflow-final-presentation.pptx", "Download", "", true],
      ["Findings and business case", "The findings, the case for each fix, and the what-if scenarios.", GH + "docs/findings-and-business-case.md", "View on GitHub"],
      ["Project charter", "Problem, goal, targets, scope, deliverables, milestones and risks.", GH + "docs/charter.md", "View on GitHub"],
      ["Baseline KPI report", "Every 2018 baseline number with its definition and base.", GH + "docs/baseline-kpi-report.md", "View on GitHub"],
      ["Decisions log", "Every analysis decision, numbered and dated.", GH + "docs/decisions.md", "View on GitHub"],
      ["Data cleaning log", "Every data check, what was found and what was decided.", GH + "docs/data-cleaning-log.md", "View on GitHub"],
      ["Retrospective", "What went well, what didn't, and what I'd do differently.", GH + "docs/retrospective.md", "View on GitHub"],
      ["Tableau dashboard", "The live, interactive 2018 baseline dashboard.", TABLEAU, "Open dashboard"]
    ];
    var dl = $("#doc-list");
    docs.forEach(function (d) {
      dl.appendChild(h("div", { class: "doc" }, [h("div", {}, [h("b", { text: d[0] }), h("span", { text: d[1] })]),
        h("a", { class: "btn" + (d[4] ? " " + d[4] : ""), href: d[2], download: d[5] ? "" : null, text: d[3] })]));
    });
  }

  /* ---------- start ---------- */
  fetch("data/site.json").then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }).then(function (data) {
    D = data; D.scenarios.forEach(function (x) { SC[x.id] = x; });
    bindValues(); navHighlight(); initZoom();
    journey(); pipeline(); processMap(); charts(); scenarios(); causes(); managed();
  }).catch(function (e) {
    var m = h("p", { class: "card", text: "The site's data file could not be loaded (" + e.message + "). Please reload the page." });
    $("main").insertBefore(m, $("main").firstChild);
  });
})();
