/* Hash router wiring all module views together. Shared file (all members). */
const App = {
  requireLogin() {
    if (API.token()) return true;
    toast("Please log in first", true);
    location.hash = "#/login";
    return false;
  },

  parse() {
    const [path, qs] = (location.hash.slice(2) || "experiences").split("?");
    return { parts: path.split("/"), params: Object.fromEntries(new URLSearchParams(qs || "")) };
  },

  async route() {
    const view = document.getElementById("view");
    const { parts, params } = App.parse();
    const [page, sub] = parts;
    document.querySelectorAll("nav a").forEach(a => a.classList.toggle("active", a.dataset.route === page));
    try {
      switch (page) {
        case "login": return Auth.login(view);
        case "register": return Auth.register(view);
        case "profile": return Auth.profile(view);
        case "experiences": return sub === "new" ? Experiences.form(view) : Experiences.list(view);
        case "companies": return Experiences.company(view, decodeURIComponent(sub));
        case "moderation": return Experiences.moderation(view);
        case "questions": return sub === "new" ? Questions.form(view) : Questions.list(view, params);
        case "practice": return sub ? Practice.session(view, sub) : Practice.setup(view, params);
        case "dashboard": return Practice.dashboard(view);
        default: return Experiences.list(view);
      }
    } catch (err) { toast(err.message, true); }
  },
};

window.addEventListener("hashchange", App.route);
window.addEventListener("DOMContentLoaded", () => { Auth.renderUserArea(); App.route(); });
