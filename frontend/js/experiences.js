/* Browse, share, vote on and moderate interview experiences. Owner: Member 2. */
const Experiences = {
  state: { page: 1, filters: {} },

  card(e, opts = {}) {
    const rounds = e.rounds.map(r => `<li><b>${esc(r.name)}</b> — ${esc(r.description)}</li>`).join("");
    return `<div class="card">
      <div class="row" style="justify-content:space-between">
        <h3>${esc(e.company)} · ${esc(e.role_title)} <span class="muted">(${e.year})</span></h3>
        <div><span class="pill ${esc(e.outcome)}">${esc(e.outcome)}</span><span class="pill">${esc(e.mode)}</span>
             <span class="pill">difficulty ${e.difficulty}/5</span>${e.status !== "approved" ? `<span class="pill pending">${esc(e.status)}</span>` : ""}</div>
      </div>
      <p>${esc(e.summary)}</p>
      ${rounds ? `<ol>${rounds}</ol>` : ""}
      ${e.tips ? `<div class="feedback"><b>Tips:</b> ${esc(e.tips)}</div>` : ""}
      <div class="row muted" style="margin-top:10px">by ${esc(e.author)} ·
        ${e.question_ids.length} question(s) added to bank ·
        <button data-vote="${e.id}">▲ ${e.upvotes}</button>
        <a href="#/companies/${encodeURIComponent(e.company)}">Company insights</a>
        ${opts.moderate ? `<button class="primary" data-mod="${e.id}" data-approve="1">Approve</button>
                           <button data-mod="${e.id}" data-approve="0">Reject</button>` : ""}
      </div></div>`;
  },

  bindCardActions(root, reload) {
    root.querySelectorAll("[data-vote]").forEach(b => b.onclick = async () => {
      if (!App.requireLogin()) return;
      try { const r = await API.post(`/api/experiences/${b.dataset.vote}/vote`); b.textContent = `▲ ${r.upvotes}`; }
      catch (err) { toast(err.message, true); }
    });
    root.querySelectorAll("[data-mod]").forEach(b => b.onclick = async () => {
      try { await API.post(`/api/experiences/${b.dataset.mod}/moderate`, { approve: b.dataset.approve === "1" }); toast("Done"); reload(); }
      catch (err) { toast(err.message, true); }
    });
  },

  async list(view) {
    const f = this.state.filters;
    view.innerHTML = `
      <div class="row" style="justify-content:space-between"><h2>Interview experiences</h2>
        <a href="#/experiences/new"><button class="primary">+ Share your experience</button></a></div>
      <form id="exp-filter" class="card row">
        <input name="q" placeholder="Search text" value="${esc(f.q)}">
        <input name="company" placeholder="Company" value="${esc(f.company)}">
        <input name="role" placeholder="Role" value="${esc(f.role)}">
        <select name="outcome"><option value="">Any outcome</option>
          ${["selected", "rejected", "pending", "withdrew"].map(o => `<option ${f.outcome === o ? "selected" : ""}>${o}</option>`).join("")}</select>
        <select name="sort"><option value="recent">Most recent</option><option value="top" ${f.sort === "top" ? "selected" : ""}>Most helpful</option></select>
        <button>Filter</button>
      </form>
      <div id="exp-list"></div><div class="row" id="exp-pager"></div>`;
    document.getElementById("exp-filter").onsubmit = (e) => { e.preventDefault(); this.state.filters = formData(e.target); this.state.page = 1; this.list(view); };
    try {
      const data = await API.get("/api/experiences", { ...f, page: this.state.page, size: 10 });
      const list = document.getElementById("exp-list");
      list.innerHTML = data.items.map(e => this.card(e)).join("") || `<p class="muted">No experiences match.</p>`;
      this.bindCardActions(list, () => this.list(view));
      const pages = Math.max(1, Math.ceil(data.total / data.size));
      const pager = document.getElementById("exp-pager");
      pager.innerHTML = `<button id="pg-prev" ${this.state.page <= 1 ? "disabled" : ""}>Prev</button>
        <span class="muted">Page ${this.state.page} of ${pages} · ${data.total} total</span>
        <button id="pg-next" ${this.state.page >= pages ? "disabled" : ""}>Next</button>`;
      document.getElementById("pg-prev").onclick = () => { this.state.page--; this.list(view); };
      document.getElementById("pg-next").onclick = () => { this.state.page++; this.list(view); };
    } catch (err) { toast(err.message, true); }
  },

  form(view) {
    if (!App.requireLogin()) return;
    view.innerHTML = `
      <div class="card"><h2>Share an interview experience</h2>
      <form id="exp-form">
        <div class="form-grid">
          <div><label>Company</label><input name="company" required></div>
          <div><label>Role</label><input name="role_title" required></div>
          <div><label>Year</label><input name="year" type="number" value="${new Date().getFullYear()}" required></div>
          <div><label>Mode</label><select name="mode"><option>on-campus</option><option>off-campus</option><option>referral</option><option>internship</option></select></div>
          <div><label>Outcome</label><select name="outcome"><option>selected</option><option>rejected</option><option>pending</option><option>withdrew</option></select></div>
          <div><label>Difficulty (1–5)</label><input name="difficulty" type="number" min="1" max="5" value="3"></div>
        </div>
        <label>Summary (at least 30 characters)</label><textarea name="summary" required minlength="30"></textarea>
        <label>Tips for others</label><textarea name="tips" style="min-height:60px"></textarea>
        <label>Rounds — one per line as "Round name: what happened"</label><textarea name="rounds" style="min-height:70px"></textarea>
        <label>Questions you were asked — one per line as "topic | question" (topics: dsa, dbms, os, networks, oop, system-design, ml, web, behavioral, hr, aptitude)</label>
        <textarea name="questions" style="min-height:70px"></textarea>
        <label><input type="checkbox" name="anonymous"> Post anonymously</label>
        <p><button class="primary">Submit for review</button></p>
      </form></div>`;
    document.getElementById("exp-form").onsubmit = async (e) => {
      e.preventDefault();
      const d = formData(e.target);
      const lines = s => (s || "").split("\n").map(x => x.trim()).filter(Boolean);
      const payload = {
        company: d.company, role_title: d.role_title, year: Number(d.year), mode: d.mode, outcome: d.outcome,
        difficulty: Number(d.difficulty), summary: d.summary, tips: d.tips || null, anonymous: !!d.anonymous,
        rounds: lines(d.rounds).map(l => { const [n, ...rest] = l.split(":"); return { name: n.trim(), description: (rest.join(":") || n).trim() }; }),
        questions: lines(d.questions).map(l => { const [t, ...rest] = l.split("|"); return rest.length ? { topic: t.trim().toLowerCase(), text: rest.join("|").trim() } : { topic: "other", text: t.trim() }; }),
      };
      try {
        const res = await API.post("/api/experiences", payload);
        toast(res.status === "approved" ? "Published!" : "Submitted — a moderator will review it");
        location.hash = "#/experiences";
      } catch (err) { toast(err.message, true); }
    };
  },

  async company(view, name) {
    try {
      const s = await API.get(`/api/companies/${encodeURIComponent(name)}/stats`);
      const exps = await API.get("/api/experiences", { company: name, size: 20 });
      view.innerHTML = `<h2>${esc(s.company)} — insights</h2>
        <div class="grid">
          <div class="card stat"><div class="num">${s.experiences}</div><div class="lbl">experiences</div></div>
          <div class="card stat"><div class="num">${Math.round(s.selection_rate * 100)}%</div><div class="lbl">selection rate</div></div>
          <div class="card stat"><div class="num">${s.avg_difficulty}</div><div class="lbl">avg difficulty /5</div></div>
          <div class="card stat"><div class="num">${s.question_count}</div><div class="lbl">questions in bank</div></div>
        </div>
        <p class="muted">Top roles: ${s.top_roles.map(esc).join(", ") || "—"} ·
          <a href="#/questions?company=${encodeURIComponent(s.company)}">See questions</a> ·
          <a href="#/practice?company=${encodeURIComponent(s.company)}">Practice for ${esc(s.company)}</a></p>
        <div id="c-list">${exps.items.map(e => this.card(e)).join("")}</div>`;
      this.bindCardActions(document.getElementById("c-list"), () => this.company(view, name));
    } catch (err) { view.innerHTML = `<p class="muted">${esc(err.message)}</p>`; }
  },

  async moderation(view) {
    if (!App.requireLogin()) return;
    try {
      const items = await API.get("/api/experiences/pending");
      view.innerHTML = `<h2>Moderation queue (${items.length})</h2><div id="mod-list">${items.map(e => this.card(e, { moderate: true })).join("") || `<p class="muted">Nothing to review.</p>`}</div>`;
      this.bindCardActions(document.getElementById("mod-list"), () => this.moderation(view));
    } catch (err) { view.innerHTML = `<p class="muted">${esc(err.message)}</p>`; }
  },
};
