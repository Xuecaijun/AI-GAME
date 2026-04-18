const state = {
  bootstrap: null,
  selectedRoleId: null,
  roleConfirmed: false,
  selectedRoleMode: "preset",
  customRoleTitle: "",
  selectedInterviewTrack: "technical",
  selectedDifficulty: "normal",
  resumeMode: "custom",
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

const el = (id) => document.getElementById(id);

const els = {
  runtimeBadge: el("runtime-badge"),
  runtimeReason: el("runtime-reason"),
  appTopbar: document.querySelector(".app-topbar"),

  // resume view
  resumeView: el("resume-view"),
  difficultyList: el("difficulty-list"),
  roleList: el("role-list"),
  offerPickerField: el("offer-picker-field"),
  selectedOfferField: el("selected-offer-field"),
  selectedOfferTitle: el("selected-offer-title"),
  changeOfferBtn: el("change-offer-btn"),
  roleDependentFields: Array.from(document.querySelectorAll(".resume-requires-role")),
  roleSelectHint: document.querySelector(".role-select-hint"),
  interviewTrackList: el("interview-track-list"),
  interviewTrackHint: el("interview-track-hint"),
  resumeText: el("resume-text"),
  resumeFile: el("resume-file"),
  uploadResumeBtn: el("upload-resume-btn"),
  mockResumeBtn: el("mock-resume-btn"),
  toInvitationsBtn: el("to-invitations-btn"),
  modeButtons: Array.from(document.querySelectorAll(".mode-btn")),

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
  tileAvatarInitial: el("tile-avatar-initial"),
  tileName: el("tile-name"),
  tileTitle: el("tile-title"),
  transcript: el("transcript"),
  phaseIndicator: el("phase-indicator"),
  drillIndicator: el("drill-indicator"),
  timerFill: el("timer-fill"),
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

  els.startGameBtn?.addEventListener("click", openTrackPicker);
  els.pickTechnicalBtn?.addEventListener("click", () => {
    state.selectedInterviewTrack = "technical";
    beginGame();
  });
  els.pickNonTechnicalBtn?.addEventListener("click", () => {
    alert("非技术类面试正在开发中，敬请期待。");
  });

  els.mockResumeBtn.addEventListener("click", generateMockResume);
  els.changeOfferBtn?.addEventListener("click", resetOfferSelection);
  els.uploadResumeBtn.addEventListener("click", () => els.resumeFile.click());
  els.resumeFile.addEventListener("change", uploadResumeFile);
  els.toInvitationsBtn.addEventListener("click", fetchInvitations);
  els.backToResumeBtn.addEventListener("click", () => {
    if (state.invitations && !state.invitations.comingSoon) {
      state.invitesNotifyPending = true;
      updateChatTabDot();
    }
    switchView("resume");
  });
  els.submitAnswerBtn.addEventListener("click", submitAnswer);
  els.codeSubmitBtn.addEventListener("click", submitCodeAnswer);
  els.leaveBtn.addEventListener("click", leaveEarly);
  els.restartBtn.addEventListener("click", resetAll);
  els.eventTextSubmit.addEventListener("click", () => submitEvent({ text: els.eventTextInput.value }));
  bindRecruitChrome();
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
    renderBootstrap();
  } catch (err) {
    alert(err.message || "初始化失败");
  }
}

function renderBootstrap() {
  renderRuntime(state.bootstrap.runtime);
  renderDifficulties();
  renderRoles();
  renderInterviewTracks();
  renderRoleDependentSections();
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
    button.className = `chip ${difficulty.id === state.selectedDifficulty ? "active" : ""}`;
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
  const roleLibrary = isTechnical
    ? (state.bootstrap.technicalRoles || state.bootstrap.roles)
    : state.bootstrap.roles;

  if (!roleLibrary.some((role) => role.id === state.selectedRoleId)) {
    state.selectedRoleId = roleLibrary[0]?.id ?? null;
  }

  roleLibrary.forEach((role, index) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className = `select-card role-feed-card ${role.id === state.selectedRoleId ? "active" : ""}`;

    const seed = seededIndex(role.id || role.title || String(index));
    const salaryPool = isTechnical
      ? ["18-28K·14薪", "20-35K·16薪", "25-40K·15薪", "15-24K·13薪", "30-45K·16薪"]
      : ["8-12K·13薪", "10-15K·13薪", "12-20K·14薪", "15-22K·14薪", "6-9K·12薪"];
    const companyPool = ["曜石互动", "北辰科技", "星澜智能", "回声网络", "启元数据", "云途创新"];
    const cityPool = ["北京", "上海", "深圳", "杭州", "成都", "广州"];
    const scalePool = ["20-99人", "100-499人", "500-999人", "1000-9999人", "A轮", "B轮", "不需要融资"];
    const expPool = ["1-3年", "3-5年", "应届/实习", "经验不限"];
    const degreePool = ["本科", "大专", "硕士优先", "学历不限"];

    const keywords = Array.isArray(role.keywords) ? role.keywords.slice(0, 4) : [];
    card.innerHTML = `
      <div class="role-feed-head">
        <h4>${escapeHtml(role.title)}</h4>
        <strong class="role-feed-salary">${salaryPool[seed % salaryPool.length]}</strong>
      </div>
      <p class="role-feed-company">${companyPool[seed % companyPool.length]} · ${scalePool[(seed + 2) % scalePool.length]} · ${cityPool[(seed + 1) % cityPool.length]}</p>
      <p class="role-feed-summary">${escapeHtml(role.summary || "该岗位将根据你的简历进行深挖问答与场景事件追问。")}</p>
      <div class="role-feed-tags">
        ${(keywords.length ? keywords : [expPool[seed % expPool.length], degreePool[(seed + 1) % degreePool.length], isTechnical ? "技术面" : "通用面"])
          .map((tag) => `<span>${escapeHtml(String(tag))}</span>`)
          .join("")}
      </div>
    `;
    card.addEventListener("click", () => {
      state.selectedRoleMode = "preset";
      state.selectedRoleId = role.id;
      state.roleConfirmed = true;
      renderRoles();
      renderRoleDependentSections();
      els.resumeView?.scrollTo?.({ top: 0, behavior: "smooth" });
    });
    els.roleList.appendChild(card);
  });
}

function renderRoleDependentSections() {
  const ready = Boolean(state.roleConfirmed && state.selectedRoleId);
  (els.roleDependentFields || []).forEach((node) => {
    node.classList.toggle("hidden", !ready);
  });
  if (els.offerPickerField) {
    els.offerPickerField.classList.toggle("hidden", ready);
  }
  if (els.selectedOfferField) {
    els.selectedOfferField.classList.toggle("hidden", !ready);
  }
  if (els.roleSelectHint) {
    els.roleSelectHint.classList.toggle("hidden", ready);
  }
  const activeLibrary = state.selectedInterviewTrack === "technical"
    ? (state.bootstrap?.technicalRoles || state.bootstrap?.roles || [])
    : (state.bootstrap?.roles || []);
  const selectedRole = activeLibrary.find((role) => role.id === state.selectedRoleId);
  if (els.selectedOfferTitle) {
    els.selectedOfferTitle.textContent = selectedRole?.title || "—";
  }
}

function resetOfferSelection() {
  state.roleConfirmed = false;
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
      state.roleConfirmed = false;
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
  if (!ensureRoleSelection()) {
    return;
  }
  els.mockResumeBtn.disabled = true;
  try {
    const data = await apiPost("/api/resume/mock", buildResumePayload());
    syncResolvedRole(data.role);
    els.resumeText.value = data.resumeText;
    state.resumeMode = "ai-generated";
    els.modeButtons.forEach((button) => {
      button.classList.toggle("active", button.dataset.mode === "ai-generated");
    });
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
    els.modeButtons.forEach((button) => {
      button.classList.toggle("active", button.dataset.mode === "custom");
    });
  } catch (err) {
    alert(err.message || "上传简历失败");
  } finally {
    els.uploadResumeBtn.disabled = false;
    els.resumeFile.value = "";
  }
}

async function fetchInvitations() {
  if (!ensureRoleSelection()) {
    return;
  }
  const payload = buildResumePayload();
  if (!payload.resumeText) {
    alert("先粘贴或生成一份简历。");
    return;
  }
  els.toInvitationsBtn.disabled = true;
  try {
    const data = await apiPost("/api/invitations", payload);
    syncResolvedRole(data.role);
    state.invitations = data;
    renderInvitations(data);
    switchView("invitation");
  } catch (err) {
    alert(err.message || "请求失败");
  } finally {
    els.toInvitationsBtn.disabled = false;
  }
}

function renderInvitations(data) {
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
    const card = document.createElement("article");
    card.className = "boss-invite-card";
    card.innerHTML = `
      <div class="boss-invite-avatar" aria-hidden="true">${escapeHtml(initialOf(interviewer.name))}</div>
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
    `;
    card.querySelector(".boss-invite-cta").addEventListener("click", () => startInterview(interviewer.id));
    els.invitationList.appendChild(card);
  });
}

/* =====================================================================
 * Step 3：面试会议
 * ================================================================ */

async function startInterview(interviewerId) {
  await detectTTSMode();
  const payload = { ...buildResumePayload(), interviewerId };
  try {
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
  } catch (err) {
    alert(err.message || "开始面试失败");
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
  try {
    const descriptor = await apiPost("/api/session/answer", {
      sessionId: state.session.sessionId,
      answer,
    });
    applyDescriptor(descriptor);
  } catch (err) {
    alert(err.message || "提交失败");
    els.submitAnswerBtn.disabled = false;
  }
}

async function submitCodeAnswer() {
  const answer = els.codeAnswerInput.value.trim();
  if (!answer || !state.session) {
    return;
  }
  stopAnswerTimer();
  els.codeSubmitBtn.disabled = true;
  try {
    const descriptor = await apiPost("/api/session/answer", {
      sessionId: state.session.sessionId,
      answer,
    });
    applyDescriptor(descriptor);
  } catch (err) {
    alert(err.message || "提交失败");
    els.codeSubmitBtn.disabled = false;
  }
}

async function submitTimeout() {
  if (!state.session) return;
  els.submitAnswerBtn.disabled = true;
  els.codeSubmitBtn.disabled = true;
  try {
    const descriptor = await apiPost("/api/session/timeout", {
      sessionId: state.session.sessionId,
    });
    applyDescriptor(descriptor);
  } catch (err) {
    console.error(err);
    els.submitAnswerBtn.disabled = false;
    els.codeSubmitBtn.disabled = false;
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

function openTrackPicker() {
  els.startView?.classList.remove("active");
  els.startView?.classList.add("hidden");
  updateEntryChrome();
  switchView("choose-track");
}

function beginGame() {
  if (state.selectedInterviewTrack !== "technical") {
    state.selectedInterviewTrack = "technical";
  }
  els.startView?.classList.remove("active");
  els.startView?.classList.add("hidden");
  switchView("resume");
  renderBootstrap();
}

function bindRecruitChrome() {
  if (els.tabJob) {
    els.tabJob.addEventListener("click", () => {
      beginGame();
    });
  }
  if (els.tabChat) {
    els.tabChat.addEventListener("click", () => {
      if (!state.invitations || state.invitations.comingSoon) {
        alert("请先在「求职」里完善简历并点击「完善并投递 · 收取新招呼」。");
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
    els.appTabbar.classList.toggle("hidden", inEntry);
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
  state.selectedRoleMode = "preset";
  state.roleConfirmed = false;
  els.startView?.classList.add("hidden");
  els.startView?.classList.remove("active");
  state.customRoleTitle = "";
  state.selectedInterviewTrack = state.bootstrap?.interviewTracks?.find((item) => item.enabled)?.id ?? "technical";
  if (state.selectedInterviewTrack === "technical" && state.bootstrap?.technicalRoles?.length) {
    state.selectedRoleId = state.bootstrap.technicalRoles[0].id;
  } else {
    state.selectedRoleId = state.bootstrap?.roles?.[0]?.id ?? null;
  }
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
  switchView("resume");
}

function buildResumePayload() {
  return {
    themeKeyword: "",
    roleId: state.selectedRoleId,
    roleTitle: "",
    roleMode: "preset",
    interviewTrack: state.selectedInterviewTrack,
    difficulty: state.selectedDifficulty,
    resumeMode: state.resumeMode,
    resumeText: els.resumeText.value.trim(),
  };
}

function ensureRoleSelection() {
  if (!state.selectedRoleId) {
    alert("请先选择一个岗位。");
    return false;
  }
  if (!state.roleConfirmed) {
    alert("请先点击岗位卡片确认岗位。");
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
