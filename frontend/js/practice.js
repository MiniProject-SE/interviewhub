/* Mock interview sessions. Owner: Member 4. */
const Practice = {
  timer: null,

  async setup(view, params = {}) {
    if (!App.requireLogin()) return;
    const meta = await Questions.loadMeta();
    view.innerHTML = `
      <h2>Mock interview</h2>
      <div class="card">
        <p class="muted">We pick questions you haven't answered yet for the topic and company you choose.</p>
        <form id="start-form" class="form-grid">
          <div><label>Role</label><input name="role_title" placeholder="e.g. SDE Intern"></div>
          <div><label>Company</label><input name="company" value="${esc(params.company)}"></div>
          <div><label>Topic</label><select name="topic"><option value="">Mixed</option>${meta.topics.map(t => `<option>${t}</option>`).join("")}</select></div>
          <div><label>Questions</label><input name="num_questions" type="number" min="1" max="15" value="5"></div>
          <div><label>Time limit (minutes)</label><input name="duration_minutes" type="number" min="5" max="180" value="20"></div>
          <div><p><button class="primary">Start interview</button></p></div>
        </form>
      </div>
      <h3>Past sessions</h3><div id="history"></div>`;
    document.getElementById("start-form").onsubmit = async (e) => {
      e.preventDefault();
      const d = formData(e.target);
      const payload = {
        role_title: d.role_title || null, company: d.company || null, topic: d.topic || null,
        num_questions: Number(d.num_questions), duration_minutes: Number(d.duration_minutes),
      };
      try { const s = await API.post("/api/practice/sessions", payload); location.hash = `#/practice/${s.id}`; }
      catch (err) { toast(err.message, true); }
    };
    const hist = await API.get("/api/practice/sessions");
    document.getElementById("history").innerHTML = hist.map(s => `
      <div class="card row" style="justify-content:space-between">
        <span>#${s.id} · ${new Date(s.started_at).toLocaleString()} · ${s.questions} questions ${s.topic ? "· " + esc(s.topic) : ""} ${s.company ? "· " + esc(s.company) : ""}</span>
        <span><span class="pill">${esc(s.state)}</span>
        <a href="#/practice/${s.id}">${s.state === "in_progress" ? "Resume" : "Review"}</a></span>
      </div>`).join("") || `<p class="muted">No sessions yet.</p>`;
  },

  async session(view, id) {
    if (!App.requireLogin()) return;
    clearInterval(this.timer);
    let s;
    try { s = await API.get(`/api/practice/sessions/${id}`); } catch (err) { view.innerHTML = esc(err.message); return; }
    const live = s.state === "in_progress";
    view.innerHTML = `
      <div class="row" style="justify-content:space-between">
        <h2>Session #${s.id} ${live ? "" : `— ${esc(s.state)}`}</h2>
        ${live ? `<div class="row"><span class="timer" id="timer"></span><button class="primary" id="finish-btn">Finish</button></div>`
               : ""}
      </div>
      ${s.items.map(i => this.itemCard(i, live)).join("")}`;
    if (live) {
      let left = s.seconds_remaining;
      const tick = () => {
        const el = document.getElementById("timer");
        if (!el) { clearInterval(this.timer); return; }
        el.textContent = `${String(Math.floor(left / 60)).padStart(2, "0")}:${String(left % 60).padStart(2, "0")}`;
        if (left-- <= 0) { clearInterval(this.timer); this.session(view, id); }
      };
      tick(); this.timer = setInterval(tick, 1000);
      document.getElementById("finish-btn").onclick = async () => {
        try { await API.post(`/api/practice/sessions/${id}/finish`); this.session(view, id); } catch (err) { toast(err.message, true); }
      };
      view.querySelectorAll("form[data-item]").forEach(f => {
        const started = Date.now();
        f.onsubmit = async (e) => {
          e.preventDefault();
          const d = formData(f);
          try {
            const r = await API.post(`/api/practice/sessions/${id}/items/${f.dataset.item}/answer`, {
              answer_text: d.answer_text, self_rating: d.self_rating ? Number(d.self_rating) : null,
              time_taken_sec: Math.round((Date.now() - started) / 1000),
            });
            f.querySelector(".result").innerHTML = this.result(r);
            toast("Answer saved");
          } catch (err) { toast(err.message, true); }
        };
      });
    }
  },

  result(i) {
    return `<div class="feedback">Answer saved${i.self_rating ? ` · self rating ${i.self_rating}/5` : ""}</div>`;
  },

  itemCard(i, live) {
    return `<div class="card">
      <div class="row" style="justify-content:space-between"><b>Q${i.position}. ${esc(i.question)}</b>
        <div><span class="pill ${esc(i.difficulty)}">${esc(i.difficulty)}</span><span class="pill">${esc(i.topic)}</span></div></div>
      ${live ? `<form data-item="${i.item_id}">
          <textarea name="answer_text" placeholder="Type your answer as you would say it in the interview…">${esc(i.answer_text)}</textarea>
          <div class="row"><label style="margin:0">Self rating</label>
            <select name="self_rating"><option value="">—</option>${[1, 2, 3, 4, 5].map(n => `<option ${i.self_rating === n ? "selected" : ""}>${n}</option>`).join("")}</select>
            <button>${i.answered ? "Resubmit" : "Submit answer"}</button></div>
          <div class="result">${i.answered ? this.result(i) : ""}</div></form>`
        : `<p><i>${i.answer_text ? esc(i.answer_text) : "Not answered"}</i></p>
           ${i.answered ? this.result(i) : ""}
           ${i.model_answer ? `<div class="feedback"><b>Key points:</b> ${esc(i.model_answer)}</div>` : ""}`}
    </div>`;
  },
};
