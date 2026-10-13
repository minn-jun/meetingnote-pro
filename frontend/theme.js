// MeetingNote Pro 공통 테마 - 모든 화면이 같은 토큰을 쓰도록 한 곳에 모음
// 라이트 = 시안 A 액센트 스트라이프 (카드 무채색, 색은 좌측 6px 띠와 라벨에만)
// 다크  = 시안 C 블랙 캔버스 (같은 구조에 배경만 뒤집음)
// 팔레트는 themes.html 비비드 9색. dot = 원색, text = 흰 배경용 어두운 값
// publish/theme.js 를 옮겨 온 구현용 파일. 색 · 크기를 고칠 일이 생기면 이 파일만 고친다
tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ['-apple-system','BlinkMacSystemFont','Segoe UI','Pretendard','Malgun Gothic','sans-serif']
      },
      colors: {
        page: "#f4f5f6",
        ink:  { DEFAULT:"#141414", 2:"#55595f", 3:"#8b9097" },
        line: "#e4e6e9",
        canvas:  "#0d0d0f",
        surface: "#17181c",
        chip:    "#1c1e23",
        fg:      "#f2f3f5",
        dim:     "#7c828b",
        edge:    "#23252a",
        blue:   { dot:"#4CA0E5", text:"#1565B0" },
        orange: { dot:"#EF8B22", text:"#A65A00" },
        green:  { dot:"#00A65A", text:"#007A42" },
        red:    { dot:"#E1232B", text:"#C21620" },
        purple: { dot:"#7C40A2", text:"#6B3590" }
      }
    }
  }
};

// ── 공통 클래스 (문자열 상수) ──────────────────────────────
// 새 화면을 만들 때 이 값을 그대로 쓴다. 임의 조합 금지
window.UI = {
  // 입력
  input:  "w-full h-11 px-3.5 rounded-xl bg-page dark:bg-chip border border-line dark:border-edge " +
          "text-sm placeholder:text-ink-3 dark:placeholder:text-dim " +
          "focus:outline-none focus:border-blue-dot focus:ring-2 focus:ring-blue-dot/25 transition",
  label:  "block text-xs font-bold mb-1.5",
  help:   "mt-1.5 text-[11px] text-ink-3 dark:text-dim",
  errText:"mt-1.5 text-[11px] font-semibold text-red-text dark:text-red-dot",

  // 버튼
  btnPrimary: "h-11 px-4 rounded-xl bg-ink dark:bg-fg text-white dark:text-canvas text-sm font-bold " +
              "hover:opacity-90 active:scale-[.99] disabled:opacity-60 transition",
  btnGhost:   "h-11 px-4 rounded-xl bg-white dark:bg-chip border border-line dark:border-edge " +
              "text-sm font-bold hover:border-ink dark:hover:border-dim transition",
  btnDanger:  "h-11 px-4 rounded-xl bg-red-dot text-white text-sm font-bold hover:opacity-90 transition",

  // 카드 / 패널
  panel: "rounded-2xl bg-white dark:bg-surface border border-line dark:border-edge",
  card:  "rounded-xl bg-white dark:bg-surface border border-line dark:border-edge",

  // 배지
  badge: "px-2.5 py-1 rounded-md text-[11px] font-extrabold tracking-wide",

  // ── 아래는 화면 6종에서 반복되던 조합을 이름으로 등록한 것 (docs/결정사항.md D1) ──
  // 바탕 · 글자 톤
  body: "bg-page dark:bg-canvas text-ink dark:text-fg font-sans antialiased min-h-screen flex flex-col",
  sub:  "text-ink-2 dark:text-dim",
  mute: "text-ink-3 dark:text-dim",
  link: "font-bold text-blue-text dark:text-blue-dot hover:underline",
  errBorder: "border-red-dot",

  // 헤더
  header:    "sticky top-0 z-30 bg-white dark:bg-canvas border-b border-line dark:border-edge",
  logoMark:  "w-7 h-7 rounded-lg bg-ink dark:bg-fg grid place-items-center text-white dark:text-canvas font-extrabold text-sm",
  logoMarkLg:"w-9 h-9 rounded-xl bg-ink dark:bg-fg grid place-items-center text-white dark:text-canvas font-extrabold",
  navItem:   "px-2.5 py-1 rounded-lg text-ink-2 dark:text-dim hover:bg-page dark:hover:bg-chip transition",
  navActive: "px-2.5 py-1 rounded-lg bg-page dark:bg-chip",

  // 입력 변형
  inputOnChip: "w-full h-11 px-3.5 rounded-xl bg-white dark:bg-surface border border-line dark:border-edge " +
               "text-sm placeholder:text-ink-3 dark:placeholder:text-dim " +
               "focus:outline-none focus:border-blue-dot focus:ring-2 focus:ring-blue-dot/25 transition",
  textarea: "w-full px-3.5 py-3 rounded-xl bg-page dark:bg-chip border border-line dark:border-edge text-sm " +
            "placeholder:text-ink-3 dark:placeholder:text-dim focus:outline-none focus:border-blue-dot transition",
  date:     "h-11 px-3 rounded-xl bg-page dark:bg-chip border border-line dark:border-edge text-sm " +
            "focus:outline-none focus:border-blue-dot transition",
  select:   "h-11 px-3 rounded-xl bg-page dark:bg-chip border border-line dark:border-edge text-[13px] font-bold " +
            "focus:outline-none focus:border-blue-dot transition",
  selectSm: "h-7 px-2 rounded-md bg-white dark:bg-surface border border-line dark:border-edge text-[11px] font-bold " +
            "focus:outline-none focus:border-blue-dot transition",
  titleInput: "w-full text-lg font-extrabold bg-transparent border-0 p-0 focus:outline-none focus:ring-0",
  titleEditing: "ring-2 ring-blue-dot/25 rounded-lg px-2",
  codeBox:  "h-11 px-4 grid place-items-center rounded-xl bg-page dark:bg-chip border border-line dark:border-edge " +
            "font-mono text-sm font-extrabold tracking-[0.2em]",

  // 버튼 변형
  btnGhostDanger: "h-11 px-4 rounded-xl bg-white dark:bg-chip border border-line dark:border-edge " +
                  "text-sm font-bold text-red-text dark:text-red-dot hover:border-red-dot disabled:opacity-60 transition",
  btnOnChip: "h-11 px-4 rounded-xl bg-white dark:bg-surface border border-line dark:border-edge " +
             "text-sm font-bold hover:border-ink dark:hover:border-dim transition",
  locked:   "opacity-40 pointer-events-none",

  // 카드 안 항목 · 작은 배지
  item:      "rounded-xl bg-page dark:bg-chip border border-line dark:border-edge",
  hoverable: "hover:border-ink dark:hover:border-dim transition cursor-pointer",
  tag:       "px-2 py-0.5 rounded-md text-[10px] font-bold bg-page dark:bg-chip",
  tagOnChip: "px-2 py-0.5 rounded-md text-[10px] font-bold bg-white dark:bg-surface",
  tagBtn:    "hover:ring-1 hover:ring-ink-3 transition",
  tagBtnDanger: "text-red-text dark:text-red-dot hover:ring-1 hover:ring-red-dot transition",
  avatar:    "w-9 h-9 rounded-xl bg-white dark:bg-surface border border-line dark:border-edge grid place-items-center text-[13px] font-extrabold",
  avatarLg:  "w-12 h-12 rounded-2xl bg-page dark:bg-chip border border-line dark:border-edge grid place-items-center text-lg font-extrabold",
  empty:     "rounded-2xl bg-white dark:bg-surface border border-line dark:border-edge px-5 py-12 text-center",

  // 탭 · 칸반
  tabWrap:   "flex gap-1 p-1 rounded-xl bg-page dark:bg-chip",
  tab:       "px-3 py-1.5 rounded-lg text-[13px] font-bold transition text-ink-2 dark:text-dim",
  tabActive: "px-3 py-1.5 rounded-lg text-[13px] font-bold transition bg-white dark:bg-surface shadow-sm",
  kanbanCard:"card touch-none select-none cursor-grab active:cursor-grabbing rounded-xl bg-white dark:bg-surface " +
             "border border-line dark:border-edge p-3 hover:border-ink dark:hover:border-dim transition",
  dragging:  "opacity-40",
  ghost:     "fixed pointer-events-none z-50 opacity-80 shadow-lg",
  column:    "dropzone rounded-2xl bg-white dark:bg-surface p-4 min-h-[220px] transition",
  columnIdle:"border border-line dark:border-edge",
  pickBar:   "mt-2 flex gap-1.5 border-t border-line dark:border-edge pt-2",
  pickBtn:   "flex-1 py-1.5 rounded-lg text-[11px] font-bold transition bg-white dark:bg-surface " +
             "border border-line dark:border-edge hover:border-ink dark:hover:border-dim",
  pickBtnCurrent: "flex-1 py-1.5 rounded-lg text-[11px] font-bold transition bg-page dark:bg-chip text-ink-3 dark:text-dim",

  // 업로드
  dropzone:   "rounded-xl border-2 border-dashed border-line dark:border-edge px-4 py-6 text-center cursor-pointer",
  dropzoneHot:"border-blue-dot",
  progressTrack: "h-1.5 rounded-full bg-page dark:bg-chip overflow-hidden",
  progressBar:   "h-full bg-blue-dot transition-all"
};

// 상태색 - 좌측 6px 띠 + 라벨. 카드 배경은 항상 무채색
window.STRIPE = {
  blue:   "border-l-[6px] border-l-blue-dot dark:border-l-blue-dot",
  orange: "border-l-[6px] border-l-orange-dot dark:border-l-orange-dot",
  green:  "border-l-[6px] border-l-green-dot dark:border-l-green-dot",
  red:    "border-l-[6px] border-l-red-dot dark:border-l-red-dot",
  purple: "border-l-[6px] border-l-purple-dot dark:border-l-purple-dot"
};
// 칸반에서 카드를 끌어 올린 칸 - 점선 테두리
window.DROP = {
  blue:   "border-2 border-dashed border-blue-dot",
  orange: "border-2 border-dashed border-orange-dot",
  green:  "border-2 border-dashed border-green-dot",
  red:    "border-2 border-dashed border-red-dot",
  purple: "border-2 border-dashed border-purple-dot"
};
window.LABEL = {
  blue:   "text-blue-text dark:text-blue-dot",
  orange: "text-orange-text dark:text-orange-dot",
  green:  "text-green-text dark:text-green-dot",
  red:    "text-red-text dark:text-red-dot",
  purple: "text-purple-text dark:text-purple-dot"
};

// 알림 박스 - 좌측 띠로 종류 구분
window.notice = (kind, title, body) => `
  <div class="rounded-xl bg-white dark:bg-surface border border-line dark:border-edge ${window.STRIPE[kind]} px-4 py-3">
    <p class="text-[13px] font-bold ${window.LABEL[kind]}">${title}</p>
    ${body ? `<p class="text-[12px] text-ink-2 dark:text-dim mt-0.5">${body}</p>` : ""}
  </div>`;

// 테마 토글 - localStorage('theme'), 초기값 prefers-color-scheme
window.initTheme = function (onChange) {
  const root = document.documentElement;
  const saved = localStorage.getItem("theme");
  root.classList.toggle("dark",
    saved ? saved === "dark" : matchMedia("(prefers-color-scheme: dark)").matches);
  const btn = document.getElementById("themeBtn");
  if (btn) btn.onclick = () => {
    localStorage.setItem("theme", root.classList.toggle("dark") ? "dark" : "light");
    if (onChange) onChange();
  };
};

window.THEME_BTN = `
  <button id="themeBtn" class="w-8 h-8 grid place-items-center rounded-lg hover:bg-page dark:hover:bg-edge transition" aria-label="테마 전환">
    <svg class="w-4 h-4 hidden dark:block" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
    <svg class="w-4 h-4 block dark:hidden" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z"/></svg>
  </button>`;
