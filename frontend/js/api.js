/* Shared HTTP client + helpers. Owner: Member 1 (auth owns token handling). */
const API = (() => {
  const TOKEN_KEY = "ih_token";
  const USER_KEY = "ih_user";

  function token() { try { return localStorage.getItem(TOKEN_KEY); } catch { return null; } }
  function user() { try { return JSON.parse(localStorage.getItem(USER_KEY) || "null"); } catch { return null; } }
  function setSession(t, u) {
    try { localStorage.setItem(TOKEN_KEY, t); localStorage.setItem(USER_KEY, JSON.stringify(u)); } catch {}
  }
  function clear() { try { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(USER_KEY); } catch {} }

  async function request(method, path, body, query) {
    const url = new URL(path, window.location.origin);
    Object.entries(query || {}).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v); });
    const headers = { "Content-Type": "application/json" };
    if (token()) headers.Authorization = `Bearer ${token()}`;
    const res = await fetch(url, { method, headers, body: body ? JSON.stringify(body) : undefined });
    if (res.status === 204) return null;
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      if (res.status === 401) clear();
      const d = data.detail;
      throw new Error(Array.isArray(d) ? d.map(e => `${e.loc.slice(-1)}: ${e.msg}`).join("; ") : (d || res.statusText));
    }
    return data;
  }

  return {
    token, user, setSession, clear,
    get: (p, q) => request("GET", p, null, q),
    post: (p, b, q) => request("POST", p, b, q),
    patch: (p, b, q) => request("PATCH", p, b, q),
    del: (p) => request("DELETE", p),
  };
})();

/* Escape user content before inserting into HTML (XSS protection). */
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function toast(msg, isError = false) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = "toast" + (isError ? " error" : "");
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.add("hidden"), 3000);
}

function formData(form) {
  return Object.fromEntries(new FormData(form).entries());
}
