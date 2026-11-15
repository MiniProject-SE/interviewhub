/* Login, registration and profile views. Owner: Member 1. */
const Auth = {
  renderUserArea() {
    const area = document.getElementById("user-area");
    const u = API.user();
    document.querySelectorAll(".mod-only").forEach(el =>
      el.classList.toggle("hidden", !(u && ["moderator", "admin"].includes(u.role))));
    if (!u) {
      area.innerHTML = `<a href="#/login">Log in</a><a href="#/register"><button class="primary">Sign up</button></a>`;
      return;
    }
    area.innerHTML = `<a href="#/profile">${esc(u.name)}</a> <span class="pill">${esc(u.role)}</span>
      <button id="logout-btn">Log out</button>`;
    document.getElementById("logout-btn").onclick = () => { API.clear(); Auth.renderUserArea(); location.hash = "#/login"; };
  },

  login(view) {
    view.innerHTML = `
      <div class="card auth-box">
        <h2>Log in</h2>
        <form id="login-form">
          <label>Email</label><input name="email" type="email" required style="width:100%">
          <label>Password</label><input name="password" type="password" required style="width:100%">
          <p><button class="primary" type="submit">Log in</button></p>
        </form>
        <p class="muted">Demo: student@interviewhub.dev / Demo@1234 · No account? <a href="#/register">Sign up</a></p>
      </div>`;
    document.getElementById("login-form").onsubmit = async (e) => {
      e.preventDefault();
      try {
        const res = await API.post("/api/auth/login", formData(e.target));
        API.setSession(res.access_token, res.user);
        Auth.renderUserArea();
        toast(`Welcome back, ${res.user.name}`);
        location.hash = "#/dashboard";
      } catch (err) { toast(err.message, true); }
    };
  },

  register(view) {
    view.innerHTML = `
      <div class="card auth-box">
        <h2>Create account</h2>
        <form id="reg-form">
          <label>Full name</label><input name="name" required style="width:100%">
          <label>Email</label><input name="email" type="email" required style="width:100%">
          <label>Password (8+ chars, letters and digits)</label><input name="password" type="password" minlength="8" required style="width:100%">
          <label>College</label><input name="college" style="width:100%">
          <label>Target role</label><input name="target_role" placeholder="e.g. Software Engineer" style="width:100%">
          <p><button class="primary" type="submit">Sign up</button></p>
        </form>
      </div>`;
    document.getElementById("reg-form").onsubmit = async (e) => {
      e.preventDefault();
      const data = formData(e.target);
      try {
        await API.post("/api/auth/register", data);
        const res = await API.post("/api/auth/login", { email: data.email, password: data.password });
        API.setSession(res.access_token, res.user);
        Auth.renderUserArea();
        toast("Account created");
        location.hash = "#/dashboard";
      } catch (err) { toast(err.message, true); }
    };
  },

  async profile(view) {
    if (!App.requireLogin()) return;
    const u = await API.get("/api/users/me");
    view.innerHTML = `
      <div class="card">
        <h2>My profile</h2>
        <form id="profile-form" class="form-grid">
          <div><label>Name</label><input name="name" value="${esc(u.name)}"></div>
          <div><label>College</label><input name="college" value="${esc(u.college)}"></div>
          <div><label>Graduation year</label><input name="graduation_year" type="number" value="${esc(u.graduation_year)}"></div>
          <div><label>Target role</label><input name="target_role" value="${esc(u.target_role)}"></div>
          <div><p><button class="primary">Save</button></p></div>
        </form>
      </div>
      <div class="card">
        <h3>Change password</h3>
        <form id="pw-form" class="row">
          <input name="old_password" type="password" placeholder="Current password" required>
          <input name="new_password" type="password" placeholder="New password" minlength="8" required>
          <button>Update</button>
        </form>
      </div>`;
    document.getElementById("profile-form").onsubmit = async (e) => {
      e.preventDefault();
      const d = formData(e.target);
      d.graduation_year = d.graduation_year ? Number(d.graduation_year) : null;
      try { const nu = await API.patch("/api/users/me", d); API.setSession(API.token(), nu); Auth.renderUserArea(); toast("Profile saved"); }
      catch (err) { toast(err.message, true); }
    };
    document.getElementById("pw-form").onsubmit = async (e) => {
      e.preventDefault();
      try { await API.post("/api/users/me/password", formData(e.target)); e.target.reset(); toast("Password changed"); }
      catch (err) { toast(err.message, true); }
    };
  },
};
