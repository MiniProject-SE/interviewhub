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
        default: return API.token() ? Auth.profile(view) : Auth.login(view);
      }
    } catch (err) { toast(err.message, true); }
  },
};

window.addEventListener("hashchange", App.route);
window.addEventListener("DOMContentLoaded", () => { Auth.renderUserArea(); App.route(); });
