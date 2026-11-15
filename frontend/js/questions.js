/* Question bank browsing and contribution. Owner: Member 3. */
const Questions = {
  meta: null,

  async loadMeta() {
    if (!this.meta) this.meta = await API.get("/api/questions/meta");
    return this.meta;
  },

  row(q, extra = "") {
    return `<div class="card">
      <div class="row" style="justify-content:space-between">
        <b>${esc(q.text)}</b>
        <div><span class="pill ${esc(q.difficulty)}">${esc(q.difficulty)}</span><span class="pill">${esc(q.topic)}</span></div>
      </div>
      <div class="muted" style="margin-top:6px">${q.company ? esc(q.company) + " · " : ""}${q.role_title ? esc(q.role_title) + " · " : ""}
        asked ${q.times_asked}× ${q.tags.map(t => `<span class="pill">#${esc(t)}</span>`).join("")}
        ${q.has_model_answer ? `· <a href="#" data-answer="${q.id}">Show key points</a>` : ""}</div>
      ${extra}<div class="answer-slot" id="ans-${q.id}"></div></div>`;
  },

  bindAnswers(root) {
    root.querySelectorAll("[data-answer]").forEach(a => a.onclick = async (e) => {
      e.preventDefault();
      const slot = document.getElementById(`ans-${a.dataset.answer}`);
      if (slot.innerHTML) { slot.innerHTML = ""; return; }
      const d = await API.get(`/api/questions/${a.dataset.answer}`);
      slot.innerHTML = `<div class="feedback">${esc(d.model_answer)}</div>`;
    });
  },

  async list(view, params = {}) {
    const meta = await this.loadMeta();
    const opt = (arr, sel) => arr.map(x => `<option ${sel === x ? "selected" : ""}>${x}</option>`).join("");
    view.innerHTML = `
      <div class="row" style="justify-content:space-between"><h2>Question bank</h2>
        <a href="#/questions/new"><button class="primary">+ Add a question</button></a></div>
      <form id="q-filter" class="card row">
        <input name="q" placeholder="Search">
        <select name="topic"><option value="">All topics</option>${opt(meta.topics, params.topic)}</select>
        <select name="difficulty"><option value="">Any difficulty</option>${opt(meta.difficulties)}</select>
        <input name="company" placeholder="Company" value="${esc(params.company)}">
        <button>Filter</button>
      </form>
      <div id="q-list"></div>`;
    const load = async (filters) => {
      const data = await API.get("/api/questions", { ...filters, size: 30 });
      const el = document.getElementById("q-list");
      el.innerHTML = `<p class="muted">${data.total} question(s)</p>` + data.items.map(q => this.row(q)).join("");
      this.bindAnswers(el);
    };
    document.getElementById("q-filter").onsubmit = (e) => { e.preventDefault(); load(formData(e.target)); };
    load(params);
  },

  async form(view) {
    if (!App.requireLogin()) return;
    const meta = await this.loadMeta();
    view.innerHTML = `
      <div class="card"><h2>Add a question</h2>
      <p class="muted">Near-duplicates are detected automatically and merged (their "asked" count goes up).</p>
      <form id="q-form">
        <label>Question</label><textarea name="text" required minlength="10"></textarea>
        <div class="form-grid">
          <div><label>Topic</label><select name="topic">${meta.topics.map(t => `<option>${t}</option>`).join("")}</select></div>
          <div><label>Difficulty</label><select name="difficulty">${meta.difficulties.map(t => `<option ${t === "medium" ? "selected" : ""}>${t}</option>`).join("")}</select></div>
          <div><label>Company (optional)</label><input name="company"></div>
          <div><label>Role (optional)</label><input name="role_title"></div>
          <div><label>Tags (comma separated)</label><input name="tags"></div>
        </div>
        <label>Key points of a good answer (used for auto-scoring)</label><textarea name="model_answer"></textarea>
        <p><button class="primary">Add</button></p>
      </form></div>`;
    document.getElementById("q-form").onsubmit = async (e) => {
      e.preventDefault();
      const d = formData(e.target);
      d.tags = (d.tags || "").split(",").map(t => t.trim()).filter(Boolean);
      ["company", "role_title", "model_answer"].forEach(k => { if (!d[k]) d[k] = null; });
      try {
        const q = await API.post("/api/questions", d);
        toast(q.times_asked > 1 ? "Similar question already existed — merged" : "Question added");
        location.hash = "#/questions";
      } catch (err) { toast(err.message, true); }
    };
  },
};
