// Shared helpers for every Researchly page.
// Change this to your deployed FastAPI URL (or set window.RESEARCHLY_API before this script).
const API_BASE_URL = window.RESEARCHLY_API || "https://multi-agent-chat-assistant.onrender.com";
const TOKEN_KEY = "researchly_access_token";
const NAV = [["workspace.html", "Research"], ["reports.html", "Saved reports"], ["account.html", "Account"]];
const $ = (id) => document.getElementById(id);
const token = () => localStorage.getItem(TOKEN_KEY);

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined) n.textContent = text;
  return n;
}
function showMessage(id, msg, type = "error") { const e = $(id); e.textContent = msg; e.className = `message show ${type}`; }
function clearMessage(id) { const e = $(id); e.textContent = ""; e.className = "message"; }

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (token()) headers.set("Authorization", `Bearer ${token()}`);
  if (options.body && !(options.body instanceof URLSearchParams) && !headers.has("Content-Type"))
    headers.set("Content-Type", "application/json");
  let res;
  try { res = await fetch(API_BASE_URL + path, { ...options, headers }); }
  catch { throw new Error("Cannot reach the server. Check that the backend is running and CORS allows this site."); }
  const raw = await res.text();
  let data = {};
  if (raw) { try { data = JSON.parse(raw); } catch { data = { detail: raw }; } }
  if (!res.ok) {
    if (res.status === 401 && token()) { localStorage.removeItem(TOKEN_KEY); location.replace("login.html?expired=1"); }
    const d = data.detail || data.message || `Request failed (${res.status})`;
    throw new Error(typeof d === "string" ? d : JSON.stringify(d));
  }
  return data;
}

function requireAuth() {
  if (!token()) {
    const next = location.pathname.split("/").pop() + location.search;
    location.replace("login.html?next=" + encodeURIComponent(next));
  }
}
function logout() { localStorage.removeItem(TOKEN_KEY); location.href = "login.html?out=1"; }

async function checkApi() {
  const s = $("apiStatus"); if (!s) return;
  s.className = "status"; ;
  try { await api("/health"); s.className = "status ok"; s.textContent = "API connected"; }
  catch { s.className = "status bad";  }
}

function mountShell(active) {
  requireAuth();
  $("side").innerHTML = `<a class="brand" href="index.html">research<span>ly</span></a>` +
    NAV.map(([h, t]) => `<a class="nav${h === active ? " active" : ""}" href="${h}"${h === active ? ' aria-current="page"' : ""}>${t}</a>`).join("") +
    `<p class="side-note">Generate a report, then come back to it any time.</p>`;
  $("top").innerHTML = `<strong>${NAV.find((n) => n[0] === active)[1]}</strong>` +
    `<div class="row"><span class="status" id="apiStatus"></span><button class="btn ghost" id="logoutBtn">Log out</button></div>`;
  $("logoutBtn").onclick = logout;
  checkApi();
}

function getReportText(d) {
  if (typeof d === "string") return d;
  const f = [d.report, d.result, d.output, d.content, d.final_report, d.markdown].find((v) => typeof v === "string" && v.trim());
  if (!f) throw new Error("The server returned no report text. Check the response schema of the API.");
  return f;
}
function renderMd(node, md) { node.innerHTML = DOMPurify.sanitize(marked.parse(md)); }
function normalizeReports(d) { return Array.isArray(d) ? d : Array.isArray(d.reports) ? d.reports : []; }
function fmtDate(v) { return v ? new Date(v).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "Saved report"; }

async function copyText(btn, text) {
  try { await navigator.clipboard.writeText(text); const o = btn.textContent; btn.textContent = "Copied"; setTimeout(() => (btn.textContent = o), 1500); }
  catch { alert("Clipboard access failed. Select the text and copy it manually."); }
}
function downloadMd(title, md) {
  const a = document.createElement("a");
  const url = URL.createObjectURL(new Blob([md], { type: "text/markdown;charset=utf-8" }));
  a.href = url; a.download = (title || "research-report").toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 60) + ".md";
  a.click(); URL.revokeObjectURL(url);
}
