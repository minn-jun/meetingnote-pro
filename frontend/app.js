// MeetingNote Pro 화면 공통 - 토큰 · API 호출 · 헤더 · 시각 · 기한
// 색과 클래스는 theme.js 의 이름만 쓴다
window.App = (() => {
  const UI = window.UI;
  const KEY = { token: "mn_token", teamId: "mn_team_id", teamName: "mn_team_name" };
  const $ = (id) => document.getElementById(id);

  const esc = (s) => String(s ?? "").replace(/[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  // ── 토큰 · 현재 팀 (localStorage) ─────────────────────
  const token = () => localStorage.getItem(KEY.token);
  const setToken = (t) => localStorage.setItem(KEY.token, t);
  const setTeam = (id, name) => {
    if (id == null) { localStorage.removeItem(KEY.teamId); localStorage.removeItem(KEY.teamName); return; }
    localStorage.setItem(KEY.teamId, String(id));
    if (name != null) localStorage.setItem(KEY.teamName, name);
  };
  const teamId = () => { const v = localStorage.getItem(KEY.teamId); return v ? +v : null; };
  const teamName = () => localStorage.getItem(KEY.teamName) || "";
  const clearSession = () => Object.values(KEY).forEach((k) => localStorage.removeItem(k));

  // 내 id 는 토큰의 sub 에서 읽는다. 버튼을 보일지 정하는 데만 쓰고 권한은 서버가 판정한다
  const myId = () => {
    try {
      const part = token().split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
      return +JSON.parse(atob(part)).sub;
    } catch (e) { return null; }
  };

  const go = (path) => { location.href = path; };
  const stop = () => new Promise(() => {});   // 화면을 옮기는 중 - 뒤 처리를 멈춘다

  // ── 오류 코드 → 사람이 읽는 문장 (스토리보드 문장) ──────
  const MSG = {
    INVALID_CREDENTIALS: "이메일 또는 비밀번호가 올바르지 않습니다",
    EMAIL_INVALID: "올바른 이메일 형식이 아닙니다",
    EMAIL_DUPLICATED: "이미 가입된 이메일입니다",
    PASSWORD_TOO_WEAK: "8자 이상 입력해 주세요",
    INVITE_NOT_FOUND: "초대코드를 찾을 수 없습니다",
    TEAM_FULL: "팀 정원(6명)이 찼습니다",
    MEETING_NOT_FOUND: "회의록을 찾을 수 없습니다",
    OWNER_ONLY: "팀 owner 만 할 수 있습니다",
    FORBIDDEN: "권한이 없습니다",
    NETWORK: "서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요"
  };
  const message = (e) => (e && (MSG[e.code] || e.msg)) || MSG.NETWORK;

  // ── API 호출 ───────────────────────────────────────
  // 성공하면 본문(204 는 null), 실패하면 {status, code, msg} 를 던진다
  async function api(method, path, body) {
    const opt = { method, headers: {} };
    if (token()) opt.headers.Authorization = "Bearer " + token();
    if (body instanceof FormData) opt.body = body;
    else if (body !== undefined) { opt.headers["Content-Type"] = "application/json"; opt.body = JSON.stringify(body); }
    let res;
    try { res = await fetch(path, opt); }
    catch (e) { throw { status: 0, code: "NETWORK", msg: MSG.NETWORK }; }
    if (res.status === 204) return null;
    let data = null;
    try { data = await res.json(); } catch (e) { /* 본문 없음 */ }
    if (res.ok) return data;
    const err = { status: res.status, code: (data && data.code) || "NETWORK", msg: (data && data.msg) || MSG.NETWORK };
    if (err.status === 401 && err.code === "TOKEN_EXPIRED") {
      clearSession();
      go("/login.html?expired=1");
      return stop();
    }
    throw err;
  }

  // 녹취 올리기 - 진행률을 받으려고 XHR 을 쓴다
  function upload(file, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const form = new FormData();
      form.append("file", file);
      xhr.open("POST", "/api/upload");
      xhr.setRequestHeader("Authorization", "Bearer " + token());
      xhr.upload.onprogress = (e) => { if (e.lengthComputable) onProgress(Math.round(e.loaded / e.total * 100)); };
      xhr.onerror = () => reject({ status: 0, code: "NETWORK", msg: MSG.NETWORK });
      xhr.onload = () => {
        let data = null;
        try { data = JSON.parse(xhr.responseText); } catch (e) { /* 본문 없음 */ }
        if (xhr.status >= 200 && xhr.status < 300) return resolve(data);
        const err = { status: xhr.status, code: (data && data.code) || "NETWORK", msg: (data && data.msg) || MSG.NETWORK };
        if (err.status === 401) { clearSession(); go("/login.html?expired=1"); return; }
        reject(err);
      };
      xhr.send(form);
    });
  }

  // ── 진입 확인 ──────────────────────────────────────
  function requireLogin() {
    if (token()) return true;
    go("/login.html");
    return false;
  }
  // 팀이 없으면 팀 화면으로. 있으면 팀 id 를 돌려준다
  function requireTeam() {
    const id = teamId();
    if (id == null) { go("/team.html"); return null; }
    return id;
  }
  // 저장해 둔 팀이 더 맞지 않을 때 (403 · 404) 팀 화면에서 다시 확인한다
  function teamGone(e) {
    if (e && (e.status === 403 || e.status === 404) && e.code !== "MEETING_NOT_FOUND" && e.code !== "OWNER_ONLY") {
      setTeam(null);
      go("/team.html");
      return true;
    }
    return false;
  }

  // ── 공통 헤더 ──────────────────────────────────────
  const NAV = [["meetings", "회의록"], ["todos", "할 일"], ["team", "팀"], ["profile", "내 정보"]];
  function header(active) {
    const el = $("header");
    el.className = UI.header;
    el.innerHTML = `
      <div class="max-w-6xl mx-auto px-4 h-14 flex items-center gap-3">
        <a href="/meetings.html" class="flex items-center gap-2 shrink-0">
          <div class="${UI.logoMark}">M</div>
          <span class="font-extrabold tracking-tight">MeetingNote</span>
        </a>
        <nav class="flex items-center gap-1 text-[13px] font-bold ml-2 min-w-0 overflow-x-auto">
          ${NAV.map(([k, label]) => k === active
            ? `<span class="${UI.navActive} whitespace-nowrap">${label}</span>`
            : `<a href="/${k}.html" class="${UI.navItem} whitespace-nowrap">${label}</a>`).join("")}
        </nav>
        <div class="ml-auto flex items-center gap-2 shrink-0">
          <span class="hidden sm:inline text-[12px] ${UI.mute}" id="teamName">${esc(teamName())}</span>
          ${window.THEME_BTN}
        </div>
      </div>`;
  }

  // data-ui="btnPrimary" 처럼 적힌 이름을 theme.js 의 클래스로 바꿔 붙인다
  function applyUI(root) {
    (root || document).querySelectorAll("[data-ui]").forEach((el) => {
      el.dataset.ui.split(/\s+/).forEach((name) => {
        if (UI[name]) el.classList.add(...UI[name].split(/\s+/).filter(Boolean));
      });
    });
    (root || document).querySelectorAll("[data-stripe]").forEach((el) =>
      el.classList.add(...window.STRIPE[el.dataset.stripe].split(/\s+/)));
    (root || document).querySelectorAll("[data-label]").forEach((el) =>
      el.classList.add(...window.LABEL[el.dataset.label].split(/\s+/)));
  }
  const toggleUI = (el, name, on) => UI[name].split(/\s+/).forEach((c) => el.classList.toggle(c, on));

  // 화면 시작 - 클래스 붙이기 · 테마 · (있으면) 헤더
  function boot(active, onTheme) {
    document.body.className = UI.body;
    if (active && $("header")) header(active);
    else if ($("themeSlot")) $("themeSlot").innerHTML = window.THEME_BTN;
    applyUI();
    window.initTheme(onTheme);
  }

  // 알림 상자 - theme.js 의 notice 를 그대로 쓴다
  function notify(el, kind, title, body) {
    el.innerHTML = window.notice(kind, esc(title), body ? esc(body) : "");
    el.classList.remove("hidden");
  }
  const hide = (el) => { el.classList.add("hidden"); el.innerHTML = ""; };

  // ── 시각 (저장은 UTC, 표시는 현지) ────────────────────
  const pad = (n) => String(n).padStart(2, "0");
  const ymd = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const hm = (d) => `${pad(d.getHours())}:${pad(d.getMinutes())}`;
  const fmtDateTime = (iso) => { const d = new Date(iso); return `${ymd(d)} ${hm(d)}`; };
  // 활동 · 댓글용: 오늘 14:12 / 어제 17:40 / 9월 18일
  function fmtWhen(iso) {
    const d = new Date(iso), now = new Date();
    const days = Math.round((new Date(ymd(now)) - new Date(ymd(d))) / 86400000);
    if (days === 0) return `오늘 ${hm(d)}`;
    if (days === 1) return `어제 ${hm(d)}`;
    return `${d.getMonth() + 1}월 ${d.getDate()}일`;
  }
  // datetime-local 입력값 <-> ISO UTC
  const localToIso = (v) => new Date(v).toISOString();
  const isoToLocal = (iso) => { const d = new Date(iso); return `${ymd(d)}T${hm(d)}`; };

  // ── 기한 (결정사항 D4 · D13) ─────────────────────────
  // YYYY-MM-DD 로 시작하고 오늘보다 앞이며 완료가 아닐 때만 기한 지남
  function isLate(dueText, status, today) {
    if (status === "DONE") return false;
    const m = /^(\d{4}-\d{2}-\d{2})/.exec(dueText || "");
    return !!m && m[1] < ymd(today || new Date());
  }
  // 기한 배지를 누를 때마다: 미정 > 오늘 > 내일 > 이번 주 금요일 > 다음 주 금요일 > 미정
  function dueChoices(today) {
    const base = today || new Date();
    const plus = (n) => { const d = new Date(base); d.setDate(d.getDate() + n); return ymd(d); };
    const toFri = (5 - base.getDay() + 7) % 7;
    const list = ["미정", plus(0), plus(1), plus(toFri), plus(toFri + 7)];
    return list.filter((v, i) => list.indexOf(v) === i);
  }
  function nextDue(dueText, today) {
    const list = dueChoices(today);
    const i = list.indexOf(dueText);
    return list[(i + 1) % list.length];   // 목록에 없는 글자면 미정부터
  }

  const STATUS = {
    OPEN:  { label: "대기", color: "orange" },
    DOING: { label: "진행", color: "blue" },
    DONE:  { label: "완료", color: "green" }
  };
  // 활동 kind 별 띠 색 (정의서 7-2)
  const KIND_COLOR = {
    meeting_add: "blue", todo_assign: "orange", todo_done: "green", comment_add: "purple", member_join: "purple"
  };
  // 회의록 카드 띠 - 목록 순서대로 돌려 쓴다
  const CARD_COLORS = ["blue", "green", "orange", "purple", "red"];

  return {
    $, esc, api, upload, message, go, stop, boot, applyUI, toggleUI, notify, hide,
    token, setToken, setTeam, teamId, teamName, clearSession, myId,
    requireLogin, requireTeam, teamGone,
    fmtDateTime, fmtWhen, localToIso, isoToLocal, ymd,
    isLate, dueChoices, nextDue, STATUS, KIND_COLOR, CARD_COLORS
  };
})();
