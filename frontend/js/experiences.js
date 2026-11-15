/* Browse and share interview experiences. Owner: Member 2. */
const Experiences = {
  state: { page: 1, filters: {} },

  card(e) {
    const rounds = e.rounds.map(r => `<li><b>${esc(r.name)}</b> — ${esc(r.description)}</li>`).join("");
    return `<div class="card">
      <div class="row" style="justify-content:space-between">
        <h3>${esc(e.company)} · ${esc(e.role_title)} <span class="muted">(${e.year})</span></h3>
        <div><span class="pill ${esc(e.outcome)}">${esc(e.outcome)}</span><span class="pill">${esc(e.mode)}</span>
             <span class="pill">difficulty ${e.difficulty}/5</span></div>
      </div>
      <p>${esc(e.summary)}</p>
      ${rounds ? `<ol>${rounds}</ol>` : ""}
      ${e.tips ? `<div class="feedback"><b>Tips:</b> ${esc(e.tips)}</div>` : ""}
      <div class="row muted" style="margin-top:10px">by ${esc(e.author)} ·
        ${e.question_ids.length} question(s) added to bank
      </div></div>`;
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
        <button>Filter</button>
      </form>
      <div id="exp-list"></div><div class="row" id="exp-pager"></div>`;
    document.getElementById("exp-filter").onsubmit = (e) => { e.preventDefault(); this.state.filters = formData(e.target); this.state.page = 1; this.list(view); };
    try {
      const data = await API.get("/api/experiences", { ...f, page: this.state.page, size: 10 });
      const list = document.getElementById("exp-list");
      list.innerHTML = data.items.map(e => this.card(e)).join("") || `<p class="muted">No experiences match.</p>`;
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
        <p><button class="primary">Publish</button></p>
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
        toast(`Published! ${res.question_ids.length} question(s) added to the bank`);
        location.hash = "#/experiences";
      } catch (err) { toast(err.message, true); }
    };
  },
};
