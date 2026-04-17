const state = {
  bootstrap: null,
  selectedRoleId: null,
  selectedDifficulty: "normal",
  resumeMode: "custom",
  invitations: null,
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

  // resume view
  resumeView: el("resume-view"),
  difficultyList: el("difficulty-list"),
  roleList: el("role-list"),
  resumeText: el("resume-text"),
  mockResumeBtn: el("mock-resume-btn"),
  toInvitationsBtn: el("to-invitations-btn"),
  modeButtons: Array.from(document.querySelectorAll(".mode-btn")),

  // invitation view
  invitationView: el("invitation-view"),
  invitationBlurb: el("invitation-blurb"),
  invitationStrengths: el("invitation-strengths"),
  invitationRisks: el("invitation-risks"),
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
  answerInput: el("answer-input"),
  submitAnswerBtn: el("submit-answer-btn"),
  leaveBtn: el("leave-btn"),

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
  offerLetter: el("offer-letter"),
  offerCompany: el("offer-company"),
  offerPosition: el("offer-position"),
  offerSalary: el("offer-salary"),
  offerStart: el("offer-start"),
  offerBody: el("offer-body"),
  offerSignature: el("offer-signature"),
  rejectCard: el("reject-card"),
  rejectReason: el("reject-reason"),
};

document.addEventListener("DOMContentLoaded", init);

async function init() {
  bindEvents();
  await detectTTSMode();
  await loadBootstrap();
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

  els.mockResumeBtn.addEventListener("click", generateMockResume);
  els.toInvitationsBtn.addEventListener("click", fetchInvitations);
  els.backToResumeBtn.addEventListener("click", () => switchView("resume"));
  els.submitAnswerBtn.addEventListener("click", submitAnswer);
  els.leaveBtn.addEventListener("click", leaveEarly);
  els.restartBtn.addEventListener("click", resetAll);
  els.eventTextSubmit.addEventListener("click", () => submitEvent({ text: els.eventTextInput.value }));
}

/* =====================================================================
 * Bootstrap
 * ================================================================ */

async function loadBootstrap() {
  try {
    const data = await apiGet("/api/bootstrap");
    state.bootstrap = data;
    state.selectedRoleId = data.roles[0]?.id ?? null;
    renderBootstrap();
  } catch (err) {
    alert(err.message || "初始化失败");
  }
}

function renderBootstrap() {
  renderRuntime(state.bootstrap.runtime);
  renderDifficulties();
  renderRoles();
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
  state.bootstrap.roles.forEach((role) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className = `select-card ${role.id === state.selectedRoleId ? "active" : ""}`;
    card.innerHTML = `
      <h4>${role.title}</h4>
      <p>${role.summary}</p>
      <small>${role.keywords.slice(0, 3).join(" / ")}</small>
    `;
    card.addEventListener("click", () => {
      state.selectedRoleId = role.id;
      renderRoles();
    });
    els.roleList.appendChild(card);
  });
}

/* =====================================================================
 * Step 1 -> 2：简历分析 & 邀请
 * ================================================================ */

async function generateMockResume() {
  els.mockResumeBtn.disabled = true;
  try {
    const data = await apiPost("/api/resume/mock", buildResumePayload());
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

async function fetchInvitations() {
  const payload = buildResumePayload();
  if (!payload.resumeText) {
    alert("先粘贴或生成一份简历。");
    return;
  }
  els.toInvitationsBtn.disabled = true;
  try {
    const data = await apiPost("/api/invitations", payload);
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
  data.invitations.forEach((interviewer) => {
    const card = document.createElement("article");
    card.className = "invitation-card";
    card.innerHTML = `
      <div class="invitation-head">
        <div class="invitation-avatar">${initialOf(interviewer.name)}</div>
        <div>
          <h4>${escapeHtml(interviewer.name)}</h4>
          <p class="invitation-title">${escapeHtml(interviewer.title || "")}</p>
          <div class="invitation-tags">
            ${(interviewer.tags || []).map((tag) => `<span>${escapeHtml(tag)}</span>`).join("")}
          </div>
        </div>
      </div>
      <p class="invitation-copy">${escapeHtml(interviewer.invitation_copy || interviewer.tone || "")}</p>
      <div class="invitation-meta">
        <span>通过线：<b>${interviewer.pass_score}</b></span>
        <span>${escapeHtml(interviewer.style || "")}</span>
      </div>
      <button type="button" class="accept-btn">接受面试</button>
    `;
    card.querySelector(".accept-btn").addEventListener("click", () => startInterview(interviewer.id));
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

  stopAnswerTimer();
  stopEventTimer();
  closeEventModal();

  if (descriptor.isFinal || descriptor.phase === "final") {
    finishMeeting(descriptor);
    return;
  }

  if (descriptor.phase === "event") {
    openEventModal(descriptor.event);
    els.phaseIndicator.textContent = "随机事件";
    els.submitAnswerBtn.disabled = true;
    return;
  }

  // awaiting_answer
  els.phaseIndicator.textContent = descriptor.metrics.drillDepth > 0 ? `追问 ${descriptor.metrics.drillDepth}/3` : "作答中";
  els.submitAnswerBtn.disabled = false;
  els.answerInput.value = "";
  els.answerInput.focus();
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
    bubble.className = `bubble ${message.speaker}`;
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

async function submitTimeout() {
  if (!state.session) return;
  els.submitAnswerBtn.disabled = true;
  try {
    const descriptor = await apiPost("/api/session/timeout", {
      sessionId: state.session.sessionId,
    });
    applyDescriptor(descriptor);
  } catch (err) {
    console.error(err);
    els.submitAnswerBtn.disabled = false;
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
  els.timerFill.style.width = "100%";
  const tick = () => {
    const elapsed = performance.now() - start;
    const remaining = Math.max(0, total - elapsed);
    const pct = (remaining / total) * 100;
    els.timerFill.style.width = `${pct}%`;
    const remainSec = Math.ceil(remaining / 1000);
    els.timerText.textContent = `${remainSec}s`;
    els.timerText.classList.toggle("urgent", remainSec <= 15);
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
  els.timerFill.style.width = "0%";
  els.timerText.textContent = "--";
  els.timerText.classList.remove("urgent");
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
  stopTTS();

  const report = descriptor.report;
  const selected = descriptor.selected || state.session.selected;

  els.resultTitle.textContent = `${selected.role.title} 面试报告`;
  els.resultBadge.textContent = report.verdictLabel || (report.verdict === "offer" ? "Offer" : "未录用");
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

function switchView(view) {
  [["resume", els.resumeView], ["invitation", els.invitationView], ["meeting", els.meetingView], ["result", els.resultView]].forEach(
    ([name, node]) => {
      node.classList.toggle("active", name === view);
    }
  );
}

function resetAll() {
  state.session = null;
  state.invitations = null;
  els.answerInput.value = "";
  stopAnswerTimer();
  stopEventTimer();
  stopMeetingClock();
  stopTTS();
  state.tts.lastSpokenIdx = 0;
  switchView("resume");
}

function buildResumePayload() {
  return {
    themeKeyword: "",
    roleId: state.selectedRoleId,
    difficulty: state.selectedDifficulty,
    resumeMode: state.resumeMode,
    resumeText: els.resumeText.value.trim(),
  };
}

function speakerLabel(type) {
  return (
    {
      interviewer: "面试官",
      question: "题目",
      candidate: "你",
      feedback: "判定",
      system: "旁白",
    }[type] || "系统"
  );
}

function initialOf(name) {
  if (!name) return "面";
  return Array.from(name)[0] || "面";
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
