const state = {
  bootstrap: null,
  selectedRoleId: null,
  selectedCompanyName: "",
  roleConfirmed: false,
  selectedRoleMode: "preset",
  customRoleTitle: "",
  selectedInterviewTrack: "technical",
  resumeMode: "custom",
  recommendedJobs: [],
  invitationsLoading: false,
  invitations: null,
  invitesNotifyPending: false,
  session: null,
  answerTimer: null,
  eventTimer: null,
  meetingStartedAt: 0,
  meetingClockTimer: null,
  pendingEvent: null,
  tts: {
    enabled: true,
    backendConfigured: null,
    lastSpokenIdx: 0,
    queue: [],
    playing: false,
    audio: null,
    aborter: null,
    utterance: null,
  },
};

const dimensionLabels = {
  roleFit: "岗位匹配度",
  logic: "逻辑表达",
  depth: "专业深度",
  consistency: "一致性",
  composure: "抗压表现",
  adaptability: "临场反应",
};

const TECH_COMPANY_NAMES = ["鹅讯", "志节", "化为", "北度", "啊里"];

const TECH_ROLE_HINTS = {
  "frontend-engineer": ["前端", "react", "typescript", "javascript", "vue", "浏览器", "组件", "可视化"],
  "backend-engineer": ["后端", "java", "go", "python", "mysql", "redis", "服务端", "api", "分布式"],
  "algorithm-engineer": ["算法", "机器学习", "深度学习", "pytorch", "tensorflow", "模型", "特征工程", "训练"],
  "fullstack-engineer": ["全栈", "node", "react", "数据库", "接口设计", "devops", "前后端"],
  "ai-application-engineer": ["llm", "大模型", "rag", "prompt", "agent", "工作流", "ai", "模型评估"],
  "client-engineer": ["客户端", "android", "ios", "swift", "kotlin", "移动端", "app"],
  "test-engineer": ["测试", "自动化测试", "qa", "回归", "ci", "接口测试", "质量保障"],
};

const INTERVIEWER_FILLERS = [
  "嗯，我看一下。",
  "稍等，我捋一捋你的思路。",
  "好，我想一下你这段回答。",
  "行，我先过一遍重点。",
  "嗯，这里我确认一下细节。",
  "让我对一下你刚才提到的点。",
  "好，等我组织一下下一问。",
  "嗯，你这段我先消化一下。",
  "我看下你这个说法落在哪个点上。",
  "稍等，我顺着你的回答往下想一下。",
];

const el = (id) => document.getElementById(id);

const els = {
  runtimeBadge: el("runtime-badge"),
  runtimeReason: el("runtime-reason"),
  appTopbar: document.querySelector(".app-topbar"),

  // resume view
  resumeView: el("resume-view"),
  roleList: el("role-list"),
  roleListHeading: el("role-list-heading"),
  offerPickerField: el("offer-picker-field"),
  generateJobsBtn: el("generate-jobs-btn"),
  recommendationHint: el("recommendation-hint"),
  selectedOfferField: el("selected-offer-field"),
  selectedOfferTitle: el("selected-offer-title"),
  changeOfferBtn: el("change-offer-btn"),
  submitRow: el("submit-row"),
  roleSelectHint: document.querySelector(".role-select-hint"),
  interviewTrackField: el("interview-track-field"),
  interviewTrackList: el("interview-track-list"),
  interviewTrackHint: el("interview-track-hint"),
  resumeText: el("resume-text"),
  resumeFile: el("resume-file"),
  uploadResumeBtn: el("upload-resume-btn"),
  mockResumeBtn: el("mock-resume-btn"),
  toInvitationsBtn: el("to-invitations-btn"),
  modeButtons: Array.from(document.querySelectorAll(".mode-btn")),
  setupTitle: document.querySelector("#resume-view .section-head h2"),
  roleFieldLabel: document.querySelector("#role-list")?.parentElement?.querySelector("span"),
  resumeModeField: el("resume-mode-field"),
  resumeContentField: el("resume-content-field"),
  startHint: document.querySelector(".start-row .muted"),
  invitationAnalysisTitle: document.querySelector("#invitation-analysis h4"),

  // invitation view
  invitationView: el("invitation-view"),
  invitationBlurb: el("invitation-blurb"),
  invitationStrengths: el("invitation-strengths"),
  invitationRisks: el("invitation-risks"),
  trackPlaceholder: el("track-placeholder"),
  trackPlaceholderTitle: el("track-placeholder-title"),
  trackPlaceholderDesc: el("track-placeholder-desc"),
  invitationList: el("invitation-list"),
  backToResumeBtn: el("back-to-resume-btn"),

  // meeting view
  meetingView: el("meeting-view"),
  meetingRole: el("meeting-role"),
  meetingClock: el("meeting-clock"),
  roundIdx: el("round-idx"),
  roundTotal: el("round-total"),
  hudScore: el("hud-score"),
  hudRoundScore: el("hud-round-score"),
  hudPass: el("hud-pass"),
  hudStress: el("hud-stress"),
  stressFill: el("stress-fill"),
  tileInterviewer: el("tile-interviewer"),
  tileAvatarImage: el("tile-avatar-image"),
  tileAvatarInitial: el("tile-avatar-initial"),
  tileName: el("tile-name"),
  tileTitle: el("tile-title"),
  transcript: el("transcript"),
  phaseIndicator: el("phase-indicator"),
  drillIndicator: el("drill-indicator"),
  timerFill: el("timer-fill"),
  timerHorse: el("timer-horse"),
  timerText: el("timer-text"),
  answerDock: document.querySelector(".answer-dock"),
  answerInput: el("answer-input"),
  submitAnswerBtn: el("submit-answer-btn"),
  leaveBtn: el("leave-btn"),

  // code modal
  codeModal: el("code-modal"),
  codeTitle: el("code-title"),
  codeDifficulty: el("code-difficulty"),
  codeDescription: el("code-description"),
  codeSignature: el("code-signature"),
  codeExamples: el("code-examples"),
  codeAnswerInput: el("code-answer-input"),
  codeSubmitBtn: el("code-submit-btn"),
  codeTimerFill: el("code-timer-fill"),
  codeTimerText: el("code-timer-text"),

  // event modal
  eventModal: el("event-modal"),
  eventIntro: el("event-intro"),
  eventPrompt: el("event-prompt"),
  eventChoiceArea: el("event-choice-area"),
  eventTextArea: el("event-text-area"),
  eventTextInput: el("event-text-input"),
  eventTextSubmit: el("event-text-submit"),
  eventTimerFill: el("event-timer-fill"),
  eventTimerText: el("event-timer-text"),

  // result view
  resultView: el("result-view"),
  resultTitle: el("result-title"),
  resultBadge: el("result-badge"),
  resultSummary: el("result-summary"),
  resultQuote: el("result-quote"),
  resultTips: el("result-tips"),
  highlightText: el("highlight-text"),
  flopText: el("flop-text"),
  dimensionGrid: el("dimension-grid"),
  shareLines: el("share-lines"),
  roundScoreList: el("round-score-list"),
  restartBtn: el("restart-btn"),
  resultNoticeCard: el("result-notice-card"),
  resultNoticeLine: el("result-notice-line"),
  offerLetter: el("offer-letter"),
  offerCompany: el("offer-company"),
  offerPosition: el("offer-position"),
  offerSalary: el("offer-salary"),
  offerStart: el("offer-start"),
  offerBody: el("offer-body"),
  offerSignature: el("offer-signature"),
  rejectCard: el("reject-card"),
  rejectReason: el("reject-reason"),
  toast: el("toast"),
  joiningMeetingOverlay: el("joining-meeting-overlay"),
  joiningMeetingSub: el("joining-meeting-sub"),
  hero: el("hero"),
  startView: el("start-view"),
  startGameBtn: el("start-game-btn"),
  chooseTrackView: el("choose-track-view"),
  pickTechnicalBtn: el("pick-technical-btn"),
  pickNonTechnicalBtn: el("pick-non-technical-btn"),

  meetingView: el("meeting-view"),
  hudToggleBtn: el("hud-toggle-btn"),
  appTabbar: el("app-tabbar"),
  tabJob: el("tab-job"),
  tabChat: el("tab-chat"),
  tabMore: el("tab-more"),
  tabChatDot: el("tab-chat-dot"),
  moreView: el("more-view"),
  moreCloseBtn: el("more-close-btn"),
};

document.addEventListener("DOMContentLoaded", init);

async function init() {
  bindEvents();
  setupStartViewEffects();
  await detectTTSMode();
  await loadBootstrap();
  updateEntryChrome();
}

async function detectTTSMode() {
  // Prefer backend TTS(v3) when configured; fallback to browser speechSynthesis.
  try {
    const data = await apiGet("/api/tts/status");
    state.tts.backendConfigured = Boolean(data?.configured);
  } catch (_) {
    state.tts.backendConfigured = false;
  }
}

function bindEvents() {
  els.modeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.resumeMode = button.dataset.mode;
      els.modeButtons.forEach((item) => item.classList.toggle("active", item === button));
    });
  });

  els.startGameBtn?.addEventListener("click", playStartTransition);
  els.pickTechnicalBtn?.addEventListener("click", () => {
    state.selectedInterviewTrack = "technical";
    beginGame();
  });
  els.pickNonTechnicalBtn?.addEventListener("click", () => {
    state.selectedInterviewTrack = "non-technical";
    beginNonTechnicalQuickEntry();
  });

  els.mockResumeBtn.addEventListener("click", generateMockResume);
  els.changeOfferBtn?.addEventListener("click", resetOfferSelection);
  els.generateJobsBtn?.addEventListener("click", generateRecommendedJobs);
  els.uploadResumeBtn.addEventListener("click", () => els.resumeFile.click());
  els.resumeFile.addEventListener("change", uploadResumeFile);
  els.resumeText?.addEventListener("input", handleResumeTextChange);
  els.toInvitationsBtn.addEventListener("click", fetchInvitations);
  els.backToResumeBtn.addEventListener("click", () => {
    state.invitations = null;
    state.invitesNotifyPending = false;
    updateChatTabDot();
    resetTechnicalRecommendationState();
    switchView("resume");
  });
  els.submitAnswerBtn.addEventListener("click", submitAnswer);
  els.codeSubmitBtn.addEventListener("click", submitCodeAnswer);
  els.leaveBtn.addEventListener("click", leaveEarly);
  els.restartBtn.addEventListener("click", resetAll);
  els.eventTextSubmit.addEventListener("click", () => submitEvent({ text: els.eventTextInput.value }));
  bindRecruitChrome();
}

function setupStartViewEffects() {
  const startView = els.startView;
  const startCard = startView?.querySelector(".landing-card");
  const titleEl = startCard?.querySelector("h1");
  const copyEl = startCard?.querySelector(".landing-copy");
  const startBtn = els.startGameBtn;

  if (!startView || !startCard || !titleEl || !copyEl || !startBtn) return;

  const originalTitle = titleEl.textContent || "";
  const originalCopy = copyEl.textContent || "";

  startView.classList.add("fx-ready");
  startCard.classList.add("fx-card-enter");
  startBtn.classList.add("fx-start-pulse");

  titleEl.textContent = "";
  copyEl.textContent = "";

  const typeText = (node, text, speed = 46, done) => {
    let index = 0;
    const timer = window.setInterval(() => {
      index += 1;
      node.textContent = text.slice(0, index);
      if (index >= text.length) {
        window.clearInterval(timer);
        if (typeof done === "function") done();
      }
    }, speed);
  };

  window.setTimeout(() => {
    typeText(titleEl, originalTitle, 44, () => {
      copyEl.classList.add("fx-copy-fade-in");
      typeText(copyEl, originalCopy, 24);
    });
  }, 160);
}

/* =====================================================================
 * Bootstrap
 * ================================================================ */

async function loadBootstrap() {
  try {
    const data = await apiGet("/api/bootstrap");
    state.bootstrap = data;
    state.selectedInterviewTrack = data.interviewTracks?.find((item) => item.enabled)?.id ?? "technical";
    state.selectedRoleMode = "preset";
    if (state.selectedInterviewTrack === "technical" && Array.isArray(data.technicalRoles) && data.technicalRoles.length) {
      state.selectedRoleId = data.technicalRoles[0].id;
    } else {
      state.selectedRoleId = data.roles[0]?.id ?? null;
    }
    state.selectedCompanyName = "";
    state.recommendedJobs = [];
    renderBootstrap();
  } catch (err) {
    alert(err.message || "初始化失败");
  }
}

function renderBootstrap() {
  renderRuntime(state.bootstrap.runtime);
  renderTrackMode();
  renderRoles();
  renderInterviewTracks();
  renderRoleDependentSections();
}

function renderTrackMode() {
  const isTechnical = state.selectedInterviewTrack === "technical";

  if (els.setupTitle) {
    els.setupTitle.textContent = isTechnical ? "上传简历并生成推荐岗位" : "挑一张你想入场的角色卡";
  }
  if (els.roleFieldLabel) {
    els.roleFieldLabel.textContent = isTechnical ? "推荐岗位" : "本轮卡池";
  }
  if (els.roleListHeading) {
    els.roleListHeading.textContent = isTechnical ? "推荐岗位" : "本轮卡池";
  }
  if (els.mockResumeBtn) {
    els.mockResumeBtn.style.display = isTechnical ? "" : "none";
  }
  if (els.resumeModeField) {
    els.resumeModeField.style.display = isTechnical ? "" : "none";
  }
  if (els.resumeContentField) {
    els.resumeContentField.style.display = isTechnical ? "" : "none";
  }
  if (els.interviewTrackField) {
    els.interviewTrackField.style.display = isTechnical ? "none" : "";
  }
  if (els.generateJobsBtn) {
    els.generateJobsBtn.style.display = isTechnical ? "" : "none";
  }
  if (els.recommendationHint) {
    els.recommendationHint.textContent = isTechnical
      ? "先上传个人简历，再生成与你经历相关的推荐岗位。"
      : "非技术面会直接展示面试官卡池。";
  }
  if (els.startHint) {
    els.startHint.textContent = isTechnical
      ? "系统会先分析简历，并基于你选择的岗位随机抽取 3 位技术面试官向你发起邀请。"
      : "非技术面不需要带简历。三位角色面试官会各自带着岗位卡登场，你挑中感兴趣的一张就能开面。";
  }
  if (!isTechnical) {
    state.resumeMode = "custom";
  }
}

function renderRuntime(runtime) {
  const mode = runtime.mode === "llm" ? "llm" : "mock";
  els.runtimeBadge.textContent = mode === "llm" ? "LLM 模式" : "Mock 模式";
  els.runtimeBadge.className = `badge ${mode}`;
  els.runtimeReason.textContent = runtime.reason;
}

function renderDifficulties() {
  els.difficultyList.innerHTML = "";
  state.bootstrap.difficulties.forEach((difficulty) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `chip difficulty-chip ${difficulty.id === state.selectedDifficulty ? "active" : ""}`;
    button.dataset.difficulty = String(difficulty.id || "").toLowerCase();
    button.textContent = difficulty.label;
    button.title = difficulty.description;
    button.addEventListener("click", () => {
      state.selectedDifficulty = difficulty.id;
      renderDifficulties();
    });
    els.difficultyList.appendChild(button);
  });
}

function renderRoles() {
  els.roleList.innerHTML = "";

  const isTechnical = state.selectedInterviewTrack === "technical";
  if (!isTechnical) {
    if (els.customRoleWrap) els.customRoleWrap.style.display = "none";
    (state.bootstrap.nonTechnicalInterviewers || []).slice(0, 3).forEach((interviewer) => {
      const role = interviewer.featured_role || {};
      const card = document.createElement("button");
      card.type = "button";
      card.className = `select-card role-feed-card non-technical-preview ${role.id === state.selectedRoleId ? "active" : ""}`;
      card.innerHTML = `
        ${avatarMarkup(interviewer, "select-card-avatar")}
        <h4>${escapeHtml(interviewer.name)}</h4>
        <p>${escapeHtml(interviewer.identity || interviewer.title || "")}</p>
        <p class="role-feed-summary">${escapeHtml(role.summary || interviewer.card_hint || "角色岗位将在下一步展示")}</p>
        <div class="role-feed-tags">
          ${(Array.isArray(role.keywords) ? role.keywords.slice(0, 3) : ["非技术面"]).map((tag) => `<span>${escapeHtml(String(tag))}</span>`).join("")}
        </div>
        <small>${escapeHtml(role.title || "岗位将在下一步展示")}</small>
      `;
      card.addEventListener("click", () => {
        state.selectedRoleMode = "interviewer-owned";
        state.selectedRoleId = role.id || interviewer.id;
        state.roleConfirmed = true;
        renderRoles();
        renderRoleDependentSections();
      });
      els.roleList.appendChild(card);
    });
    return;
  }
  const recommendedJobs = state.recommendedJobs || [];
  if (!recommendedJobs.length) {
    const empty = document.createElement("article");
    empty.className = "analysis-box recommendation-empty";
    empty.innerHTML = `
      <h4>先上传简历</h4>
      <p class="muted">系统会根据你的项目经历、技术关键词和岗位方向，生成 5 个对应不同公司的推荐岗位。</p>
    `;
    els.roleList.appendChild(empty);
    return;
  }

  recommendedJobs.forEach((item, index) => {
    const role = item.role;
    const card = document.createElement("button");
    card.type = "button";
    const active = state.roleConfirmed && role.id === state.selectedRoleId && item.company === state.selectedCompanyName;
    card.className = `select-card role-feed-card ${active ? "active" : ""}`;
    card.disabled = Boolean(state.invitationsLoading);

    const seed = seededIndex(`${item.company}-${role.id || role.title || String(index)}`);
    const salaryPool = ["18-28K·14薪", "20-35K·16薪", "25-40K·15薪", "15-24K·13薪", "30-45K·16薪"];
    const cityPool = ["北京", "上海", "深圳", "杭州", "成都", "广州"];
    const scalePool = ["20-99人", "100-499人", "500-999人", "1000-9999人", "A轮", "B轮", "不需要融资"];
    const tags = item.matches.length ? item.matches : (Array.isArray(role.keywords) ? role.keywords.slice(0, 4) : []);
    card.innerHTML = `
      <div class="role-feed-head">
        <h4>${escapeHtml(`${item.company} · ${role.title}`)}</h4>
        <strong class="role-feed-salary">${salaryPool[seed % salaryPool.length]}</strong>
      </div>
      <p class="role-feed-company">${escapeHtml(item.company)} · ${scalePool[(seed + 2) % scalePool.length]} · ${cityPool[(seed + 1) % cityPool.length]}</p>
      <p class="role-feed-summary">${escapeHtml(item.reason || role.summary || "该岗位将根据你的简历进行深挖问答与场景事件追问。")}</p>
      <div class="role-feed-tags">
        ${(tags.length ? tags : ["技术面", "项目经历", "岗位匹配"])
          .map((tag) => `<span>${escapeHtml(String(tag))}</span>`)
          .join("")}
      </div>
    `;
    card.addEventListener("click", async () => {
      if (state.invitationsLoading) return;
      state.selectedRoleMode = "preset";
      state.selectedRoleId = role.id;
      state.selectedCompanyName = item.company;
      state.roleConfirmed = true;
      state.invitationsLoading = true;
      if (els.recommendationHint) {
        els.recommendationHint.textContent = "正在获取新招呼…";
      }
      renderRoles();
      renderRoleDependentSections();
      try {
        await postInvitationsAndNavigate();
      } finally {
        state.invitationsLoading = false;
        renderRoles();
        renderRoleDependentSections();
      }
    });
    els.roleList.appendChild(card);
  });
}

function renderRoleDependentSections() {
  const isTechnical = state.selectedInterviewTrack === "technical";
  const ready = Boolean(state.roleConfirmed && state.selectedRoleId);
  const activeLibrary = isTechnical ? getTechnicalRoleLibrary() : (state.bootstrap?.roles || []);
  const selectedRole = activeLibrary.find((role) => role.id === state.selectedRoleId);
  const selectedRecommendation = getSelectedTechnicalRecommendation();

  if (els.generateJobsBtn) {
    const hasRecommendations = (state.recommendedJobs || []).length > 0;
    els.generateJobsBtn.disabled = isTechnical && !hasTechnicalResumeText();
    els.generateJobsBtn.textContent = hasRecommendations ? "重新生成推荐岗位" : "生成推荐岗位";
  }
  if (els.selectedOfferField) {
    els.selectedOfferField.classList.toggle("hidden", isTechnical ? true : !ready);
  }
  if (els.submitRow) {
    els.submitRow.classList.toggle("hidden", isTechnical ? true : !ready);
  }
  if (els.roleSelectHint) {
    if (!isTechnical) {
      els.roleSelectHint.classList.add("hidden");
    } else {
      const hasRecommendations = (state.recommendedJobs || []).length > 0;
      els.roleSelectHint.classList.remove("hidden");
      els.roleSelectHint.textContent = hasRecommendations
        ? "点击岗位卡片即可进入「沟通」新招呼页面。"
        : "先上传或粘贴简历，再生成推荐岗位。";
    }
  }
  if (els.recommendationHint) {
    if (!isTechnical) {
      els.recommendationHint.textContent = "非技术面会直接展示面试官卡池。";
    } else if (state.invitationsLoading) {
      els.recommendationHint.textContent = "正在获取新招呼…";
    } else if ((state.recommendedJobs || []).length > 0) {
      els.recommendationHint.textContent = "以下岗位根据你的简历关键词生成，每家公司各推荐 1 个岗位。点击卡片直接进入沟通页。";
    } else {
      els.recommendationHint.textContent = "先上传个人简历，再生成与你经历相关的推荐岗位。";
    }
  }

  if (els.selectedOfferTitle) {
    els.selectedOfferTitle.textContent = selectedRecommendation
      ? `${selectedRecommendation.company} · ${selectedRecommendation.role.title}`
      : (selectedRole?.title || "—");
  }
}

function resetOfferSelection() {
  state.selectedCompanyName = "";
  state.roleConfirmed = false;
  state.selectedRoleId = getDefaultTechnicalRole()?.id ?? state.selectedRoleId;
  renderRoles();
  renderRoleDependentSections();
  els.resumeView?.scrollTo?.({ top: 0, behavior: "smooth" });
}

function renderInterviewTracks() {
  els.interviewTrackList.innerHTML = "";
  (state.bootstrap.interviewTracks || []).forEach((track) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `chip ${track.id === state.selectedInterviewTrack ? "active" : ""}`;
    button.textContent = track.label;
    button.title = track.description || "";
    button.addEventListener("click", () => {
      state.selectedInterviewTrack = track.id;
      if (track.id === "technical") {
        resetTechnicalRecommendationState({ rerender: false });
        state.selectedRoleId = getDefaultTechnicalRole()?.id ?? state.bootstrap?.roles?.[0]?.id ?? null;
      } else {
        state.recommendedJobs = [];
        state.selectedCompanyName = "";
        state.roleConfirmed = false;
        state.selectedRoleId = null;
        state.selectedRoleMode = "preset";
        state.customRoleTitle = "";
      }
      renderTrackMode();
      renderInterviewTracks();
      renderRoles();
      renderRoleDependentSections();
    });
    els.interviewTrackList.appendChild(button);
  });

  const selected = (state.bootstrap.interviewTracks || []).find((item) => item.id === state.selectedInterviewTrack);
  els.interviewTrackHint.textContent = selected?.description || "选择技术面或非技术面后，再进入邀请阶段。";
}

/* =====================================================================
 * Step 1 -> 2：简历分析 & 邀请
 * ================================================================ */

async function generateMockResume() {
  els.mockResumeBtn.disabled = true;
  try {
    const payload = buildResumePayload({
      roleId: pickMockResumeRoleId(),
    });
    const data = await apiPost("/api/resume/mock", payload);
    els.resumeText.value = data.resumeText;
    state.resumeMode = "ai-generated";
    resetTechnicalRecommendationState();
    els.modeButtons.forEach((button) => {
      button.classList.toggle("active", button.dataset.mode === "ai-generated");
    });
    renderRoleDependentSections();
  } catch (err) {
    alert(err.message || "生成简历失败");
  } finally {
    els.mockResumeBtn.disabled = false;
  }
}

async function uploadResumeFile(event) {
  const [file] = event.target.files || [];
  if (!file) return;

  els.uploadResumeBtn.disabled = true;
  try {
    const base64 = await fileToDataUrl(file);
    const data = await apiPost("/api/resume/upload", {
      filename: file.name,
      base64,
    });
    els.resumeText.value = data.resumeText || "";
    state.resumeMode = "custom";
    resetTechnicalRecommendationState();
    els.modeButtons.forEach((button) => {
      button.classList.toggle("active", button.dataset.mode === "custom");
    });
    renderRoleDependentSections();
  } catch (err) {
    alert(err.message || "上传简历失败");
  } finally {
    els.uploadResumeBtn.disabled = false;
    els.resumeFile.value = "";
  }
}

async function generateRecommendedJobs() {
  if (state.selectedInterviewTrack !== "technical") {
    return;
  }
  if (!hasTechnicalResumeText()) {
    alert("请先上传、粘贴或生成一份简历。");
    return;
  }

  els.generateJobsBtn.disabled = true;
  try {
    state.recommendedJobs = buildTechnicalRecommendations(els.resumeText.value.trim());
    state.selectedRoleId = getDefaultTechnicalRole()?.id ?? state.selectedRoleId;
    state.selectedCompanyName = "";
    state.roleConfirmed = false;
    renderRoles();
    renderRoleDependentSections();
    els.resumeView?.scrollTo?.({ top: 0, behavior: "smooth" });
  } finally {
    els.generateJobsBtn.disabled = false;
    renderRoleDependentSections();
  }
}

async function postInvitationsAndNavigate() {
  const payload = buildResumePayload();
  if (state.selectedInterviewTrack === "technical" && !payload.resumeText) {
    alert("先粘贴或生成一份简历。");
    return false;
  }
  try {
    const data = await apiPost("/api/invitations", payload);
    syncResolvedRole(data.role);
    state.invitations = data;
    renderInvitations(data);
    switchView("invitation");
    return true;
  } catch (err) {
    alert(err.message || "请求失败");
    return false;
  }
}

async function fetchInvitations() {
  if (!ensureRoleSelection()) {
    return;
  }
  els.toInvitationsBtn.disabled = true;
  try {
    await postInvitationsAndNavigate();
  } finally {
    els.toInvitationsBtn.disabled = false;
  }
}

function renderInvitations(data) {
  const isTechnical = state.selectedInterviewTrack === "technical";
  els.invitationList.classList.toggle("nontech-rune-list", !isTechnical);
  if (els.invitationAnalysisTitle) {
    els.invitationAnalysisTitle.textContent = isTechnical ? "AI 简历分析" : "今夜卡池";
  }
  els.invitationBlurb.textContent = data.analysis.themeBlurb;
  els.invitationStrengths.innerHTML = data.analysis.strengths
    .map((item) => `<li>${escapeHtml(item)}</li>`) 
    .join("");
  els.invitationRisks.innerHTML = data.analysis.riskPoints
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("");

  els.invitationList.innerHTML = "";
  if (data.comingSoon) {
    els.trackPlaceholder.classList.remove("hidden");
    els.trackPlaceholderTitle.textContent = data.placeholder?.title || "接口预留中";
    els.trackPlaceholderDesc.textContent = data.placeholder?.description || "";
    return;
  }

  els.trackPlaceholder.classList.add("hidden");
  data.invitations.forEach((interviewer) => {
    const snippet = interviewer.invitation_copy || interviewer.tone || "";
    const role = interviewer.featured_role || {};
    const card = document.createElement("article");
    card.className = `boss-invite-card ${isTechnical ? "" : "nontech-rune-card"}`.trim();
    card.innerHTML = isTechnical
      ? `
        <div class="boss-invite-avatar-wrap">
          ${avatarMarkup(interviewer, "boss-invite-avatar")}
        </div>
        <div class="boss-invite-main">
          <div class="boss-invite-top">
            <h4 class="boss-invite-name">${escapeHtml(interviewer.name)}</h4>
            <span class="boss-invite-pass">通过线 ${escapeHtml(String(interviewer.pass_score ?? ""))}</span>
          </div>
          <p class="boss-invite-role">${escapeHtml(interviewer.title || "")}</p>
          <div class="boss-invite-tags">
            ${(interviewer.tags || []).map((tag) => `<span>${escapeHtml(tag)}</span>`).join("")}
          </div>
          <p class="boss-invite-snippet">${escapeHtml(snippet)}</p>
          <p class="boss-invite-style muted">${escapeHtml(interviewer.style || "")}</p>
        </div>
        <button type="button" class="boss-invite-cta primary-btn">立即沟通</button>
      `
      : `
        <div class="nontech-rune-portrait">${avatarMarkup(interviewer, "boss-invite-avatar")}</div>
        <div class="boss-invite-main">
          <div class="boss-invite-top">
            <h4 class="boss-invite-name">${escapeHtml(interviewer.name)}</h4>
            <span class="boss-invite-pass">通过线 ${escapeHtml(String(interviewer.pass_score ?? ""))}</span>
          </div>
          <p class="boss-invite-role">${escapeHtml(interviewer.identity || interviewer.title || "")}</p>
          <p class="boss-invite-style muted">${escapeHtml(interviewer.style || snippet || "")}</p>
          <p class="nontech-rune-job">招募岗位：${escapeHtml(role.title || "角色专属岗位")}</p>
          <p class="boss-invite-snippet">${escapeHtml(role.summary || "暂无岗位说明")}</p>
          <div class="boss-invite-tags">
            ${(interviewer.tags || []).map((tag) => `<span>${escapeHtml(tag)}</span>`).join("")}
          </div>
        </div>
        <button type="button" class="boss-invite-cta primary-btn">选择这张卡</button>
      `;
    card.querySelector(".boss-invite-cta").addEventListener("click", () => startInterview(interviewer.id));
    els.invitationList.appendChild(card);
  });
}

/* =====================================================================
 * Step 3：面试会议
 * ================================================================ */

const JOINING_MEETING_TIPS = ["正在连接会议…", "正在同步音视频…", "即将进入面试间…"];
let joiningMeetingTipTimer = null;
let joiningMeetingTipIndex = 0;

function showJoiningMeetingOverlay() {
  const overlay = els.joiningMeetingOverlay;
  if (!overlay) return;
  document.body.classList.add("joining-meeting-active");
  overlay.classList.remove("hidden");
  overlay.setAttribute("aria-hidden", "false");
  overlay.setAttribute("aria-busy", "true");
  joiningMeetingTipIndex = 0;
  if (els.joiningMeetingSub) {
    els.joiningMeetingSub.textContent = JOINING_MEETING_TIPS[0];
  }
  if (joiningMeetingTipTimer != null) {
    clearInterval(joiningMeetingTipTimer);
  }
  joiningMeetingTipTimer = window.setInterval(() => {
    joiningMeetingTipIndex = (joiningMeetingTipIndex + 1) % JOINING_MEETING_TIPS.length;
    if (els.joiningMeetingSub) {
      els.joiningMeetingSub.textContent = JOINING_MEETING_TIPS[joiningMeetingTipIndex];
    }
  }, 1200);
}

function hideJoiningMeetingOverlay() {
  if (joiningMeetingTipTimer != null) {
    clearInterval(joiningMeetingTipTimer);
    joiningMeetingTipTimer = null;
  }
  document.body.classList.remove("joining-meeting-active");
  const overlay = els.joiningMeetingOverlay;
  if (!overlay) return;
  overlay.classList.add("hidden");
  overlay.setAttribute("aria-hidden", "true");
  overlay.removeAttribute("aria-busy");
}

function awaitDoubleRaf() {
  return new Promise((resolve) => {
    requestAnimationFrame(() => {
      requestAnimationFrame(resolve);
    });
  });
}

async function startInterview(interviewerId) {
  showJoiningMeetingOverlay();
  try {
    await detectTTSMode();
    const payload = { ...buildResumePayload(), interviewerId };
    const descriptor = await apiPost("/api/session/start", payload);
    state.session = descriptor;
    switchView("meeting");
    if (els.meetingView) {
      els.meetingView.classList.remove("hud-collapsed");
    }
    if (els.hudToggleBtn) {
      els.hudToggleBtn.setAttribute("aria-expanded", "true");
      els.hudToggleBtn.textContent = "隐藏分数栏";
    }
    startMeetingClock();
    applyDescriptor(descriptor);
    await awaitDoubleRaf();
  } catch (err) {
    hideJoiningMeetingOverlay();
    alert(err.message || "开始面试失败");
  } finally {
    hideJoiningMeetingOverlay();
  }
}

function applyDescriptor(descriptor) {
  state.session = descriptor;
  renderRuntime(descriptor.runtime);
  renderMeetingHud(descriptor);
  renderTranscript(descriptor.transcript);
  enqueueTTSFromTranscript(descriptor.transcript);
  if (descriptor.eventNote) {
    showToast(descriptor.eventNote);
  }

  stopAnswerTimer();
  stopEventTimer();
  closeEventModal();
  closeCodeModal();

  if (descriptor.isFinal || descriptor.phase === "final") {
    finishMeeting(descriptor);
    return;
  }

  if (descriptor.phase === "event") {
    openEventModal(descriptor.event);
    els.phaseIndicator.textContent = "随机事件";
    els.submitAnswerBtn.disabled = true;
    toggleAnswerMode("normal");
    return;
  }

  // awaiting_answer
  els.phaseIndicator.textContent = descriptor.metrics.drillDepth > 0 ? `追问 ${descriptor.metrics.drillDepth}/3` : "作答中";
  if (descriptor.questionType === "code" && descriptor.codeQuestion) {
    toggleAnswerMode("code");
    renderCodeQuestion(descriptor.codeQuestion);
    els.codeAnswerInput.value = "";
    els.codeSubmitBtn.disabled = false;
    els.codeAnswerInput.focus();
  } else {
    toggleAnswerMode("normal");
    els.submitAnswerBtn.disabled = false;
    els.answerInput.value = "";
    els.answerInput.focus();
  }
  if (descriptor.timerMs) {
    startAnswerTimer(descriptor.timerMs);
  }
}

function renderMeetingHud(descriptor) {
  const { selected, metrics } = descriptor;
  els.meetingRole.textContent = selected.role.title;
  els.roundIdx.textContent = metrics.roundIndex;
  els.roundTotal.textContent = metrics.totalRounds;
  els.hudScore.textContent = metrics.sessionScore;
  els.hudRoundScore.textContent = metrics.roundScore;
  els.hudPass.textContent = metrics.passScore;
  els.hudStress.textContent = metrics.stress;
  els.stressFill.style.width = `${Math.min(100, metrics.stress)}%`;

  els.tileName.textContent = selected.interviewer.name;
  els.tileTitle.textContent = selected.interviewer.title || selected.interviewer.style || "";
  els.tileAvatarInitial.textContent = initialOf(selected.interviewer.name);
  const avatar = String(selected.interviewer.avatar || "").trim();
  const hasAvatar = Boolean(avatar);
  els.tileAvatarImage.classList.toggle("hidden", !hasAvatar);
  els.tileAvatarInitial.parentElement.classList.toggle("hidden", hasAvatar);
  if (hasAvatar) {
    els.tileAvatarImage.src = avatar;
    els.tileAvatarImage.alt = `${selected.interviewer.name}形象`;
    els.tileAvatarImage.style.objectPosition = avatarObjectPosition(selected.interviewer.id);
  } else {
    els.tileAvatarImage.removeAttribute("src");
    els.tileAvatarImage.alt = "面试官形象";
    els.tileAvatarImage.style.objectPosition = "50% 50%";
  }
  els.tileInterviewer.classList.toggle("has-video", hasAvatar);

  const dots = els.drillIndicator.querySelectorAll(".drill-dot");
  dots.forEach((dot) => {
    const depth = Number(dot.dataset.depth);
    dot.classList.toggle("active", depth <= metrics.drillDepth);
  });
}

function renderTranscript(transcript) {
  els.transcript.innerHTML = "";
  transcript.forEach((message) => {
    const bubble = document.createElement("article");
    bubble.className = `bubble message-bubble ${message.speaker}`;
    const label = document.createElement("span");
    label.className = "bubble-label";
    label.textContent = speakerLabel(message.speaker);
    const content = document.createElement("div");
    content.textContent = message.text;
    bubble.append(label, content);
    els.transcript.appendChild(bubble);
  });
  els.transcript.scrollTop = els.transcript.scrollHeight;
  els.tileInterviewer.classList.add("speaking");
  clearTimeout(state._speakingTimeout);
  state._speakingTimeout = setTimeout(() => els.tileInterviewer.classList.remove("speaking"), 2200);
}

function pickInterviewerFiller() {
  const interviewerId = state.session?.selected?.interviewer?.id || "";
  const roleTitle = state.session?.selected?.role?.title || "";

  if (interviewerId === "master-strategist") {
    const options = [
      "嗯，我先盘一下你这步棋。",
      "稍等，我看看你这段话的落点。",
      "好，我把前后的逻辑串一下。",
    ];
    return options[Math.floor(Math.random() * options.length)];
  }

  if (roleTitle && /前端|后端|算法|测试|客户端|全栈|AI/i.test(roleTitle)) {
    const options = [
      "嗯，我先对一下你这个技术点。",
      "稍等，我看下你这个回答落没落到关键处。",
      "好，我顺着你这个实现往下想一下。",
    ];
    return options[Math.floor(Math.random() * options.length)];
  }

  return INTERVIEWER_FILLERS[Math.floor(Math.random() * INTERVIEWER_FILLERS.length)];
}

function showInterviewerFillerBubble(text) {
  if (!els.transcript || !text) return null;
  const bubble = document.createElement("article");
  bubble.className = "bubble message-bubble interviewer";
  bubble.dataset.filler = "true";

  const label = document.createElement("span");
  label.className = "bubble-label";
  label.textContent = speakerLabel("interviewer");

  const content = document.createElement("div");
  content.textContent = text;

  bubble.append(label, content);
  els.transcript.appendChild(bubble);
  els.transcript.scrollTop = els.transcript.scrollHeight;
  els.tileInterviewer.classList.add("speaking");
  clearTimeout(state._speakingTimeout);
  state._speakingTimeout = setTimeout(() => els.tileInterviewer.classList.remove("speaking"), 2200);
  return bubble;
}

function beginInterviewerThinking() {
  const pending = {
    timer: null,
    bubble: null,
  };

  pending.timer = setTimeout(() => {
    pending.bubble = showInterviewerFillerBubble(pickInterviewerFiller());
  }, 450);

  return pending;
}

function endInterviewerThinking(pending) {
  if (!pending) return;
  if (pending.timer) {
    clearTimeout(pending.timer);
  }
  if (pending.bubble?.parentNode) {
    pending.bubble.parentNode.removeChild(pending.bubble);
  }
}

function toggleAnswerMode(mode) {
  const isCode = mode === "code";
  els.answerDock.classList.toggle("hidden", isCode);
  els.codeModal.classList.toggle("hidden", !isCode);
  els.submitAnswerBtn.disabled = isCode;
}

function renderCodeQuestion(codeQuestion) {
  els.codeTitle.textContent = codeQuestion.title || "编程题";
  els.codeDifficulty.textContent = `难度：${formatCodeDifficulty(codeQuestion.difficulty)}`;
  els.codeDescription.textContent = codeQuestion.description || "";
  els.codeSignature.textContent = codeQuestion.signature || "";
  els.codeExamples.innerHTML = "";
  (codeQuestion.examples || []).forEach((item, index) => {
    const card = document.createElement("div");
    card.className = "code-example";
    card.innerHTML = `
      <div><b>示例 ${index + 1}</b></div>
      <div><b>输入</b>${escapeHtml(item.input || "")}</div>
      <div><b>输出</b>${escapeHtml(item.output || "")}</div>
    `;
    els.codeExamples.appendChild(card);
  });
}

function closeCodeModal() {
  els.codeModal.classList.add("hidden");
}

function enqueueTTSFromTranscript(transcript) {
  if (!state.tts.enabled) return;
  if (!Array.isArray(transcript)) return;

  const startIdx = Math.max(0, Number(state.tts.lastSpokenIdx || 0));
  const newMessages = transcript.slice(startIdx);
  state.tts.lastSpokenIdx = transcript.length;

  newMessages.forEach((message) => {
    if (!message || typeof message.text !== "string") return;
    if (message.speaker !== "interviewer" && message.speaker !== "question") return;
    const text = sanitizeTTSMessage(message.text);
    if (!text) return;
    state.tts.queue.push(text);
  });

  pumpTTSQueue();
}

function sanitizeTTSMessage(text) {
  let clean = String(text || "").trim();
  // Remove leading bracket tags in UI transcript, e.g.:
  // [第 2 轮] xxx / [追问 1] xxx / [提示 1/3] xxx
  clean = clean.replace(/^(?:\[[^\]]+\]\s*)+/u, "");
  return clean.trim();
}

async function pumpTTSQueue() {
  if (state.tts.playing) return;
  if (!state.tts.queue.length) return;

  state.tts.playing = true;
  try {
    while (state.tts.queue.length) {
      const text = state.tts.queue.shift();
      await playTTS(text);
    }
  } finally {
    state.tts.playing = false;
  }
}

function stopTTS() {
  state.tts.queue = [];
  state.tts.playing = false;
  if (state.tts.aborter) {
    try { state.tts.aborter.abort(); } catch (_) {}
  }
  state.tts.aborter = null;
  if (state.tts.audio) {
    try { state.tts.audio.pause(); } catch (_) {}
    state.tts.audio = null;
  }
  if (state.tts.utterance && "speechSynthesis" in window) {
    try { window.speechSynthesis.cancel(); } catch (_) {}
    state.tts.utterance = null;
  }
}

async function playTTS(text) {
  if (state.tts.backendConfigured === true) {
    try {
      await playBackendTTS(text);
      return;
    } catch (_) {
      // If backend call fails at runtime, fallback to browser TTS.
      await playBrowserTTS(text);
      return;
    }
  }
  await playBrowserTTS(text);
}

async function playBackendTTS(text) {
  stopCurrentAudioOnly();
  const aborter = new AbortController();
  state.tts.aborter = aborter;

  const response = await fetch("/api/tts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
    signal: aborter.signal,
  });

  if (!response.ok) {
    try { await response.text(); } catch (_) {}
    throw new Error("backend tts failed");
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);

  const audio = new Audio(url);
  state.tts.audio = audio;
  audio.volume = 1.0;
  audio.preload = "auto";

  await new Promise((resolve, reject) => {
    const done = () => resolve();
    const fail = () => reject(new Error("audio playback failed"));
    audio.addEventListener("ended", done, { once: true });
    audio.addEventListener("error", fail, { once: true });
    audio.play().catch(reject);
  });

  URL.revokeObjectURL(url);
  if (state.tts.audio === audio) {
    state.tts.audio = null;
  }
}

async function playBrowserTTS(text) {
  if (!("speechSynthesis" in window) || typeof SpeechSynthesisUtterance === "undefined") {
    return;
  }
  stopCurrentAudioOnly();

  await new Promise((resolve) => {
    try {
      const utterance = new SpeechSynthesisUtterance(text);
      state.tts.utterance = utterance;
      utterance.lang = "zh-CN";
      utterance.rate = 1;
      utterance.pitch = 1;
      utterance.volume = 1;
      utterance.onend = () => {
        if (state.tts.utterance === utterance) state.tts.utterance = null;
        resolve();
      };
      utterance.onerror = () => {
        if (state.tts.utterance === utterance) state.tts.utterance = null;
        resolve();
      };
      window.speechSynthesis.speak(utterance);
    } catch (_) {
      resolve();
    }
  });
}

function stopCurrentAudioOnly() {
  if (state.tts.audio) {
    try { state.tts.audio.pause(); } catch (_) {}
    state.tts.audio = null;
  }
  if (state.tts.utterance && "speechSynthesis" in window) {
    try { window.speechSynthesis.cancel(); } catch (_) {}
    state.tts.utterance = null;
  }
}

async function submitAnswer() {
  const answer = els.answerInput.value.trim();
  if (!answer || !state.session) {
    return;
  }
  stopAnswerTimer();
  els.submitAnswerBtn.disabled = true;
  const pendingThinking = beginInterviewerThinking();
  try {
    const descriptor = await apiPost("/api/session/answer", {
      sessionId: state.session.sessionId,
      answer,
    });
    applyDescriptor(descriptor);
  } catch (err) {
    alert(err.message || "提交失败");
    els.submitAnswerBtn.disabled = false;
  } finally {
    endInterviewerThinking(pendingThinking);
  }
}

async function submitCodeAnswer() {
  const answer = els.codeAnswerInput.value.trim();
  if (!answer || !state.session) {
    return;
  }
  stopAnswerTimer();
  els.codeSubmitBtn.disabled = true;
  const pendingThinking = beginInterviewerThinking();
  try {
    const descriptor = await apiPost("/api/session/answer", {
      sessionId: state.session.sessionId,
      answer,
    });
    applyDescriptor(descriptor);
  } catch (err) {
    alert(err.message || "提交失败");
    els.codeSubmitBtn.disabled = false;
  } finally {
    endInterviewerThinking(pendingThinking);
  }
}

async function submitTimeout() {
  if (!state.session) return;
  els.submitAnswerBtn.disabled = true;
  els.codeSubmitBtn.disabled = true;
  const pendingThinking = beginInterviewerThinking();
  try {
    const descriptor = await apiPost("/api/session/timeout", {
      sessionId: state.session.sessionId,
    });
    applyDescriptor(descriptor);
  } catch (err) {
    console.error(err);
    els.submitAnswerBtn.disabled = false;
    els.codeSubmitBtn.disabled = false;
  } finally {
    endInterviewerThinking(pendingThinking);
  }
}

function leaveEarly() {
  if (!state.session) return;
  if (!confirm("提前离开会被记为未通过，确定吗？")) return;
  finishMeeting({
    isFinal: true,
    phase: "final",
    report: {
      verdict: "reject",
      verdictLabel: "自主退出",
      summary: "你在面试进行中选择了离开，本场结果按未通过处理。",
      interviewerQuote: "下次准备好再来。",
      highlight: "—",
      flop: "—",
      tips: "建议在正式面试前练习多轮持续发言，保持节奏。",
      shareLines: ["我在 ShowMeTheOffer 中途退出了。", "下一次我会撑完全场。", ""],
      dimensions: state.session.metrics.dimensions,
      roundScores: state.session.roundHistory || [],
      offerLetter: null,
      forcedEndReason: "player_left",
    },
    runtime: state.session.runtime,
    selected: state.session.selected,
    metrics: state.session.metrics,
    transcript: state.session.transcript,
  });
}

/* =====================================================================
 * 定时器：答题 & 事件
 * ================================================================ */

function startAnswerTimer(ms) {
  stopAnswerTimer();
  const start = performance.now();
  const total = ms;
  paintAnswerTimer(100, "--", false);
  const tick = () => {
    const elapsed = performance.now() - start;
    const remaining = Math.max(0, total - elapsed);
    const pct = (remaining / total) * 100;
    const remainSec = Math.ceil(remaining / 1000);
    paintAnswerTimer(pct, `${remainSec}s`, remainSec <= 15);
    if (remaining <= 0) {
      stopAnswerTimer();
      submitTimeout();
      return;
    }
    state.answerTimer = requestAnimationFrame(tick);
  };
  state.answerTimer = requestAnimationFrame(tick);
}

function stopAnswerTimer() {
  if (state.answerTimer) {
    cancelAnimationFrame(state.answerTimer);
    state.answerTimer = null;
  }
  paintAnswerTimer(0, "--", false);
}

function paintAnswerTimer(pct, text, urgent) {
  [els.timerFill, els.codeTimerFill].forEach((node) => {
    node.style.width = `${pct}%`;
  });

  if (els.timerHorse) {
    const clamped = Math.max(0, Math.min(100, pct));
    els.timerHorse.style.left = `${clamped}%`;
    els.timerHorse.classList.toggle("is-urgent", urgent);
  }

  [els.timerText, els.codeTimerText].forEach((node) => {
    node.textContent = text;
    node.classList.toggle("urgent", urgent);
  });
}

function startEventTimer(ms) {
  stopEventTimer();
  const start = performance.now();
  const total = ms;
  els.eventTimerFill.style.width = "100%";
  const tick = () => {
    const elapsed = performance.now() - start;
    const remaining = Math.max(0, total - elapsed);
    const pct = (remaining / total) * 100;
    els.eventTimerFill.style.width = `${pct}%`;
    const remainSec = Math.ceil(remaining / 1000);
    els.eventTimerText.textContent = `${remainSec}s`;
    if (remaining <= 0) {
      stopEventTimer();
      submitEvent({ timedOut: true });
      return;
    }
    state.eventTimer = requestAnimationFrame(tick);
  };
  state.eventTimer = requestAnimationFrame(tick);
}

function stopEventTimer() {
  if (state.eventTimer) {
    cancelAnimationFrame(state.eventTimer);
    state.eventTimer = null;
  }
  els.eventTimerFill.style.width = "0%";
  els.eventTimerText.textContent = "--";
}

function startMeetingClock() {
  state.meetingStartedAt = Date.now();
  clearInterval(state.meetingClockTimer);
  state.meetingClockTimer = setInterval(() => {
    const secs = Math.floor((Date.now() - state.meetingStartedAt) / 1000);
    const mm = String(Math.floor(secs / 60)).padStart(2, "0");
    const ss = String(secs % 60).padStart(2, "0");
    els.meetingClock.textContent = `${mm}:${ss}`;
  }, 500);
}

function stopMeetingClock() {
  clearInterval(state.meetingClockTimer);
  state.meetingClockTimer = null;
}

/* =====================================================================
 * 事件弹窗
 * ================================================================ */

function openEventModal(event) {
  state.pendingEvent = event;
  els.eventIntro.textContent = event.intro || "";
  const interaction = event.interaction;

  if (!interaction) {
    setTimeout(() => submitEvent({ timedOut: false }), 1800);
    els.eventModal.classList.remove("hidden");
    els.eventPrompt.textContent = "（旁白事件，等会儿自动继续……）";
    els.eventChoiceArea.classList.add("hidden");
    els.eventTextArea.classList.add("hidden");
    return;
  }

  els.eventPrompt.textContent = interaction.prompt || "";
  els.eventModal.classList.remove("hidden");

  if (interaction.type === "choice") {
    els.eventChoiceArea.classList.remove("hidden");
    els.eventTextArea.classList.add("hidden");
    els.eventChoiceArea.innerHTML = "";
    (interaction.options || []).forEach((option) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "event-choice-btn";
      button.textContent = option.label;
      button.addEventListener("click", () => submitEvent({ choiceId: option.id }));
      els.eventChoiceArea.appendChild(button);
    });
  } else if (interaction.type === "text") {
    els.eventChoiceArea.classList.add("hidden");
    els.eventTextArea.classList.remove("hidden");
    els.eventTextInput.value = "";
    els.eventTextInput.focus();
  }

  if (interaction.timeLimitMs) {
    startEventTimer(interaction.timeLimitMs);
  }
}

function closeEventModal() {
  els.eventModal.classList.add("hidden");
  stopEventTimer();
  state.pendingEvent = null;
}

async function submitEvent(payload) {
  if (!state.session) return;
  stopEventTimer();
  try {
    const descriptor = await apiPost("/api/session/event", {
      sessionId: state.session.sessionId,
      ...payload,
    });
    closeEventModal();
    applyDescriptor(descriptor);
  } catch (err) {
    alert(err.message || "事件处理失败");
  }
}

/* =====================================================================
 * Step 4：结果 / Offer / Reject
 * ================================================================ */

function finishMeeting(descriptor) {
  stopAnswerTimer();
  stopEventTimer();
  stopMeetingClock();
  closeEventModal();
  closeCodeModal();
  stopTTS();

  const report = descriptor.report;
  const selected = descriptor.selected || state.session.selected;

  els.resultTitle.textContent = `${selected.role.title} · 面试结果`;
  const verdictLabel = report.verdictLabel || (report.verdict === "offer" ? "Offer" : "未录用");
  els.resultBadge.textContent = verdictLabel;
  if (els.resultNoticeLine) {
    els.resultNoticeLine.textContent =
      report.verdict === "offer"
        ? `结果：${verdictLabel}。综合分 ${report.sessionScore}，已超过通过线 ${report.passScore}。`
        : `结果：${verdictLabel}。综合分 ${report.sessionScore}，通过线 ${report.passScore}。`;
  }
  if (els.resultNoticeCard) {
    els.resultNoticeCard.classList.toggle("is-offer", report.verdict === "offer");
    els.resultNoticeCard.classList.toggle("is-reject", report.verdict !== "offer");
  }
  els.resultSummary.textContent = report.summary;
  els.resultQuote.textContent = report.interviewerQuote;
  els.resultTips.textContent = `${report.tips} 综合 ${report.sessionScore} / 通过线 ${report.passScore}。`;
  els.highlightText.textContent = report.highlight;
  els.flopText.textContent = report.flop;

  els.dimensionGrid.innerHTML = "";
  Object.entries(report.dimensions).forEach(([key, value]) => {
    const card = document.createElement("div");
    card.className = "dimension-card";
    card.innerHTML = `<span>${dimensionLabels[key] || key}</span><strong>${value}</strong>`;
    els.dimensionGrid.appendChild(card);
  });

  els.shareLines.innerHTML = "";
  (report.shareLines || []).forEach((line) => {
    if (!line) return;
    const p = document.createElement("p");
    p.textContent = line;
    els.shareLines.appendChild(p);
  });

  els.roundScoreList.innerHTML = "";
  (report.roundScores || []).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = `第 ${item.round} 轮：${item.score} 分（深挖 ${item.drillDepth} / 提示 ${item.hintsUsed}）`;
    els.roundScoreList.appendChild(li);
  });

  if (report.verdict === "offer" && report.offerLetter) {
    const letter = report.offerLetter;
    els.offerLetter.classList.remove("hidden");
    els.rejectCard.classList.add("hidden");
    els.offerCompany.textContent = letter.company || "—";
    els.offerPosition.textContent = letter.position || selected.role.title;
    els.offerSalary.textContent = letter.salaryRange || "—";
    els.offerStart.textContent = letter.startDate || "—";
    els.offerBody.textContent = letter.body || "";
    els.offerSignature.textContent = letter.signature || `—— ${selected.interviewer.name}`;
  } else {
    els.offerLetter.classList.add("hidden");
    els.rejectCard.classList.remove("hidden");
    els.rejectReason.textContent = report.forcedEndReason === "event_ends"
      ? "一次关键事件中断了面试。建议复盘你的临场应对。"
      : "综合分未达通过线。请参考下方高光/翻车回答进行复盘。";
  }

  switchView("result");
}

/* =====================================================================
 * 视图切换 & 工具函数
 * ================================================================ */

function playStartTransition() {
  const startView = els.startView;
  if (!startView) {
    openTrackPicker();
    return;
  }

  if (startView.classList.contains("fx-loading")) return;

  startView.classList.add("fx-loading");

  const loadingOverlay = document.createElement("div");
  loadingOverlay.className = "start-loading-overlay";
  loadingOverlay.innerHTML = `
    <div class="start-loading-card panel">
      <div class="start-loading-title">系统启动中...</div>
      <div class="start-loading-sub">正在连接面试官会场</div>
      <div class="start-loading-bar"><span></span></div>
    </div>
  `;

  startView.appendChild(loadingOverlay);

  window.setTimeout(() => {
    loadingOverlay.classList.add("done");
  }, 860);

  window.setTimeout(() => {
    startView.classList.remove("fx-loading");
    loadingOverlay.remove();
    openTrackPicker();
  }, 1120);
}

function openTrackPicker() {
  els.startView?.classList.remove("active");
  els.startView?.classList.add("hidden");
  updateEntryChrome();
  switchView("choose-track");
}

async function beginNonTechnicalQuickEntry() {
  els.startView?.classList.remove("active");
  els.startView?.classList.add("hidden");
  state.roleConfirmed = true;
  state.selectedRoleId = null;
  renderBootstrap();
  try {
    const data = await apiPost("/api/invitations", buildResumePayload());
    state.invitations = data;
    renderInvitations(data);
    switchView("invitation");
  } catch (err) {
    alert(err.message || "加载非技术卡池失败");
    switchView("resume");
  }
  resetTechnicalRecommendationState({ rerender: false });
}

function beginGame() {
  els.startView?.classList.remove("active");
  els.startView?.classList.add("hidden");
  switchView("resume");
  renderBootstrap();
}

function bindRecruitChrome() {
  if (els.tabJob) {
    els.tabJob.addEventListener("click", () => {
      if (els.startView?.classList.contains("active")) {
        beginGame();
        return;
      }
      switchView("resume");
    });
  }
  if (els.tabChat) {
    els.tabChat.addEventListener("click", () => {
      if (!state.invitations || state.invitations.comingSoon) {
        alert("请先在「求职」里上传简历、生成推荐岗位，并点击岗位卡片进入沟通。");
        switchView("resume");
        return;
      }
      state.invitesNotifyPending = false;
      updateChatTabDot();
      switchView("invitation");
    });
  }
  if (els.tabMore) {
    els.tabMore.addEventListener("click", () => switchView("more"));
  }
  if (els.moreCloseBtn) {
    els.moreCloseBtn.addEventListener("click", () => switchView("resume"));
  }
  if (els.hudToggleBtn && els.meetingView) {
    els.hudToggleBtn.addEventListener("click", () => {
      const collapsed = els.meetingView.classList.toggle("hud-collapsed");
      els.hudToggleBtn.setAttribute("aria-expanded", String(!collapsed));
      els.hudToggleBtn.textContent = collapsed ? "显示分数栏" : "隐藏分数栏";
    });
  }
}

function updateChatTabDot() {
  if (!els.tabChatDot) return;
  const show = Boolean(state.invitesNotifyPending);
  els.tabChatDot.classList.toggle("hidden", !show);
}

function syncRecruitTabs(view) {
  if (!els.tabJob || !els.tabChat || !els.tabMore) return;
  els.tabJob.classList.toggle("active", view === "resume");
  els.tabChat.classList.toggle("active", view === "invitation");
  els.tabMore.classList.toggle("active", view === "more");
}

function updateEntryChrome() {
  const inEntry = Boolean(els.startView?.classList.contains("active"));
  if (els.appTopbar) {
    els.appTopbar.classList.toggle("hidden", inEntry);
  }
  if (els.appTabbar) {
    // 与 switchView 中的全屏子视图（会议/结果/选赛道）一致：底栏由 subview-fullscreen 决定，不能在此处误删 hidden
    if (inEntry) {
      els.appTabbar.classList.add("hidden");
    } else if (!document.body.classList.contains("subview-fullscreen")) {
      els.appTabbar.classList.remove("hidden");
    }
  }
}

function switchView(view) {
  [
    ["choose-track", els.chooseTrackView],
    ["resume", els.resumeView],
    ["invitation", els.invitationView],
    ["meeting", els.meetingView],
    ["result", els.resultView],
    ["more", els.moreView],
  ].forEach(([name, node]) => {
    if (node) node.classList.toggle("active", name === view);
  });

  const hideChrome = view === "meeting" || view === "result" || view === "choose-track";
  document.body.classList.toggle("subview-fullscreen", hideChrome);
  if (els.appTabbar) {
    els.appTabbar.classList.toggle("hidden", hideChrome);
  }

  if (els.hero) {
    els.hero.classList.toggle("hidden", view !== "resume");
  }

  if (view === "invitation") {
    state.invitesNotifyPending = false;
    updateChatTabDot();
  }

  syncRecruitTabs(view);
  updateEntryChrome();
}

function resetAll() {
  state.session = null;
  state.invitations = null;
  state.invitationsLoading = false;
  state.selectedRoleMode = "preset";
  state.resumeMode = "custom";
  els.startView?.classList.add("hidden");
  els.startView?.classList.remove("active");
  state.customRoleTitle = "";
  state.selectedInterviewTrack = "technical";
  resetTechnicalRecommendationState({ rerender: false });
  state.selectedRoleId = getDefaultTechnicalRole()?.id ?? null;
  els.resumeText.value = "";
  els.modeButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.mode === "custom");
  });
  renderTrackMode();
  renderRoles();
  renderInterviewTracks();
  renderRoleDependentSections();
  els.answerInput.value = "";
  stopAnswerTimer();
  stopEventTimer();
  stopMeetingClock();
  stopTTS();
  closeCodeModal();
  toggleAnswerMode("normal");
  hideToast();
  state.tts.lastSpokenIdx = 0;
  state.invitesNotifyPending = false;
  updateChatTabDot();
  switchView("choose-track");
}

function buildResumePayload(overrides = {}) {
  const isTechnical = state.selectedInterviewTrack === "technical";
  const resolvedRoleId = isTechnical
    ? (overrides.roleId ?? state.selectedRoleId ?? getDefaultTechnicalRole()?.id ?? "")
    : "";
  return {
    themeKeyword: "",
    roleId: resolvedRoleId,
    roleTitle: "",
    roleMode: isTechnical ? "preset" : "interviewer-owned",
    interviewTrack: state.selectedInterviewTrack,
    difficulty: "normal",
    resumeMode: overrides.resumeMode ?? state.resumeMode,
    resumeText: isTechnical ? (overrides.resumeText ?? els.resumeText.value.trim()) : "",
  };
}

function ensureRoleSelection() {
  const isTechnical = state.selectedInterviewTrack === "technical";
  if (!state.selectedRoleId) {
    alert(isTechnical ? "请先选择一个岗位。" : "请先选择一张角色岗位卡。");
    return false;
  }
  if (!state.roleConfirmed) {
    alert(isTechnical ? "请先点击岗位卡片确认岗位。" : "请先点击角色卡确认你要挑战的岗位。");
    return false;
  }
  return true;
}

function syncResolvedRole(role) {
  if (!role) return;
  state.selectedRoleId = role.id || state.selectedRoleId;
  state.selectedRoleMode = "preset";
  state.roleConfirmed = true;
  renderRoles();
  renderRoleDependentSections();
}

function getTechnicalRoleLibrary() {
  return state.bootstrap?.technicalRoles || state.bootstrap?.roles || [];
}

function getDefaultTechnicalRole() {
  return getTechnicalRoleLibrary()[0] || null;
}

function getSelectedTechnicalRecommendation() {
  return (state.recommendedJobs || []).find((item) => (
    item.role.id === state.selectedRoleId && item.company === state.selectedCompanyName
  )) || null;
}

function hasTechnicalResumeText() {
  return state.selectedInterviewTrack !== "technical" || Boolean(els.resumeText.value.trim());
}

function handleResumeTextChange() {
  if (state.selectedInterviewTrack !== "technical") {
    return;
  }
  if (!(state.recommendedJobs || []).length && !state.roleConfirmed && !state.selectedCompanyName) {
    renderRoleDependentSections();
    return;
  }
  resetTechnicalRecommendationState();
  renderRoleDependentSections();
}

function resetTechnicalRecommendationState(options = {}) {
  const { rerender = true } = options;
  state.invitationsLoading = false;
  state.recommendedJobs = [];
  state.selectedCompanyName = "";
  state.roleConfirmed = false;
  if (state.selectedInterviewTrack === "technical") {
    state.selectedRoleId = getDefaultTechnicalRole()?.id ?? null;
  }
  if (rerender) {
    renderRoles();
    renderRoleDependentSections();
  }
}

function pickMockResumeRoleId() {
  const selected = getSelectedTechnicalRecommendation();
  if (selected?.role?.id) {
    return selected.role.id;
  }
  return state.selectedRoleId || getDefaultTechnicalRole()?.id || "";
}

function buildTechnicalRecommendations(resumeText) {
  const roles = getTechnicalRoleLibrary();
  if (!roles.length) {
    return [];
  }

  const ranked = roles
    .map((role) => scoreTechnicalRoleAgainstResume(role, resumeText))
    .sort((left, right) => (
      right.score - left.score
      || right.matches.length - left.matches.length
      || left.role.title.localeCompare(right.role.title, "zh-CN")
    ));

  const uniqueRanked = [];
  const usedIds = new Set();
  ranked.forEach((item) => {
    if (usedIds.has(item.role.id)) return;
    uniqueRanked.push(item);
    usedIds.add(item.role.id);
  });

  const pool = uniqueRanked.length ? uniqueRanked : ranked;
  return TECH_COMPANY_NAMES.map((company, index) => {
    const picked = pool[index % pool.length];
    return {
      company,
      role: picked.role,
      score: picked.score,
      matches: picked.matches.slice(0, 3),
      reason: picked.matches.length
        ? `简历里命中了 ${picked.matches.slice(0, 3).join("、")}，推荐你优先尝试这个方向。`
        : `根据你的简历背景，${picked.role.title} 适合作为本轮技术面的推荐方向。`,
    };
  });
}

function scoreTechnicalRoleAgainstResume(role, resumeText) {
  const loweredResume = String(resumeText || "").toLowerCase();
  const candidates = [
    ...(Array.isArray(role.keywords) ? role.keywords : []),
    ...(TECH_ROLE_HINTS[role.id] || []),
    role.title,
    role.title.replace(/工程师|开发|方向|岗位/g, ""),
  ]
    .map((item) => String(item || "").trim())
    .filter((item, index, array) => item && array.indexOf(item) === index);

  const matches = [];
  let score = 0;

  candidates.forEach((token) => {
    const loweredToken = token.toLowerCase();
    if (!loweredToken || !loweredResume.includes(loweredToken)) {
      return;
    }
    matches.push(token);
    score += (role.keywords || []).includes(token) ? 4 : 2;
    if (token === role.title) {
      score += 2;
    }
  });

  return {
    role,
    score,
    matches,
  };
}

function speakerLabel(type) {
  return (
    {
      interviewer: "面试官",
      question: "题目",
      candidate: "你",
      feedback: "反馈",
    }[type] || "系统"
  );
}

function formatCodeDifficulty(value) {
  return (
    {
      easy: "简单",
      medium: "中等",
      hard: "偏难",
    }[value] || "中等"
  );
}

function initialOf(name) {
  if (!name) return "面";
  return Array.from(name)[0] || "面";
}

function seededIndex(input) {
  const text = String(input || "role");
  let hash = 0;
  for (let i = 0; i < text.length; i += 1) {
    hash = (hash * 31 + text.charCodeAt(i)) >>> 0;
  }
  return hash;
}

function avatarMarkup(interviewer, className = "invitation-avatar") {
  const src = String(interviewer?.avatar || "").trim();
  const initial = escapeHtml(initialOf(interviewer?.name || ""));
  const label = escapeHtml(interviewer?.name || "面试官");
  if (src) {
    const pos = avatarObjectPosition(interviewer?.id);
    return `
      <div class="${className} has-image">
        <img src="${escapeHtml(src)}" alt="${label}形象" loading="lazy" style="object-position: ${escapeHtml(pos)};" />
      </div>
    `;
  }
  return `<div class="${className}">${initial}</div>`;
}

function avatarObjectPosition(interviewerId) {
  const map = {
    "donald-trump": "50% 22%",
    "jackeylove": "50% 24%",
    "song-jiang": "50% 20%",
    "sun-wukong": "50% 22%",
    "master-strategist": "50% 24%",
    "queen-of-order": "50% 22%",
    "detective-kid": "50% 24%",
  };
  return map[String(interviewerId || "")] || "50% 50%";
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char]));
}

function showToast(message) {
  const text = String(message || "").trim();
  if (!text) return;
  clearTimeout(state.toastTimer);
  els.toast.textContent = text;
  els.toast.classList.remove("hidden");
  state.toastTimer = setTimeout(() => {
    hideToast();
  }, 2600);
}

function hideToast() {
  clearTimeout(state.toastTimer);
  els.toast.classList.add("hidden");
  els.toast.textContent = "";
}

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error("文件读取失败"));
    reader.readAsDataURL(file);
  });
}

async function apiGet(url) {
  const response = await fetch(url);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "请求失败");
  }
  return data;
}

async function apiPost(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "请求失败");
  }
  return data;
}
