const state = {
  bootstrap: null,
  selectedRoleId: null,
  selectedInterviewerId: null,
  selectedDifficulty: "normal",
  resumeMode: "custom",
  session: null,
};

const dimensionLabels = {
  roleFit: "岗位匹配度",
  logic: "逻辑表达",
  depth: "专业深度",
  consistency: "一致性",
  composure: "抗压表现",
  adaptability: "临场反应",
};

const elements = {
  runtimeBadge: document.getElementById("runtime-badge"),
  runtimeReason: document.getElementById("runtime-reason"),
  difficultyList: document.getElementById("difficulty-list"),
  roleList: document.getElementById("role-list"),
  interviewerList: document.getElementById("interviewer-list"),
  resumeText: document.getElementById("resume-text"),
  mockResumeBtn: document.getElementById("mock-resume-btn"),
  startBtn: document.getElementById("start-btn"),
  modeButtons: [...document.querySelectorAll(".mode-btn")],
  setupView: document.getElementById("setup-view"),
  interviewView: document.getElementById("interview-view"),
  resultView: document.getElementById("result-view"),
  transcript: document.getElementById("transcript"),
  scoreIndicator: document.getElementById("score-indicator"),
  stressIndicator: document.getElementById("stress-indicator"),
  stressFill: document.getElementById("stress-fill"),
  turnIndicator: document.getElementById("turn-indicator"),
  keywordIndicator: document.getElementById("keyword-indicator"),
  sessionBrief: document.getElementById("session-brief"),
  focusList: document.getElementById("focus-list"),
  answerInput: document.getElementById("answer-input"),
  submitAnswerBtn: document.getElementById("submit-answer-btn"),
  resultTitle: document.getElementById("result-title"),
  resultBadge: document.getElementById("result-badge"),
  resultSummary: document.getElementById("result-summary"),
  resultQuote: document.getElementById("result-quote"),
  resultTips: document.getElementById("result-tips"),
  highlightText: document.getElementById("highlight-text"),
  flopText: document.getElementById("flop-text"),
  dimensionGrid: document.getElementById("dimension-grid"),
  shareLines: document.getElementById("share-lines"),
  restartBtn: document.getElementById("restart-btn"),
};

document.addEventListener("DOMContentLoaded", init);

async function init() {
  bindEvents();
  await loadBootstrap();
}

function bindEvents() {
  elements.modeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.resumeMode = button.dataset.mode;
      elements.modeButtons.forEach((item) => item.classList.toggle("active", item === button));
    });
  });

  elements.mockResumeBtn.addEventListener("click", generateMockResume);
  elements.startBtn.addEventListener("click", startInterview);
  elements.submitAnswerBtn.addEventListener("click", submitAnswer);
  elements.restartBtn.addEventListener("click", resetToSetup);
}

async function loadBootstrap() {
  try {
    const data = await apiGet("/api/bootstrap");
    state.bootstrap = data;
    state.selectedRoleId = data.roles[0]?.id ?? null;
    state.selectedInterviewerId = data.interviewers[0]?.id ?? null;
    renderBootstrap();
  } catch (error) {
    alert(error.message || "初始化失败");
  }
}

function renderBootstrap() {
  renderRuntime(state.bootstrap.runtime);
  renderDifficulties();
  renderRoles();
  renderInterviewers();
}

function renderRuntime(runtime) {
  const mode = runtime.mode === "llm" ? "llm" : "mock";
  elements.runtimeBadge.textContent = mode === "llm" ? "LLM 模式" : "Mock 模式";
  elements.runtimeBadge.className = `badge ${mode}`;
  elements.runtimeReason.textContent = runtime.reason;
}

function renderDifficulties() {
  elements.difficultyList.innerHTML = "";
  state.bootstrap.difficulties.forEach((difficulty) => {
    const button = document.createElement("button");
    button.className = `chip ${difficulty.id === state.selectedDifficulty ? "active" : ""}`;
    button.textContent = difficulty.label;
    button.title = difficulty.description;
    button.addEventListener("click", () => {
      state.selectedDifficulty = difficulty.id;
      renderDifficulties();
    });
    elements.difficultyList.appendChild(button);
  });
}

function renderRoles() {
  elements.roleList.innerHTML = "";
  state.bootstrap.roles.forEach((role) => {
    const card = document.createElement("button");
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
    elements.roleList.appendChild(card);
  });
}

function renderInterviewers() {
  elements.interviewerList.innerHTML = "";
  state.bootstrap.interviewers.forEach((interviewer) => {
    const card = document.createElement("button");
    card.className = `select-card ${interviewer.id === state.selectedInterviewerId ? "active" : ""}`;
    card.innerHTML = `
      <h4>${interviewer.name}</h4>
      <p>${interviewer.style}</p>
      <small>${interviewer.tone}</small>
    `;
    card.addEventListener("click", () => {
      state.selectedInterviewerId = interviewer.id;
      renderInterviewers();
    });
    elements.interviewerList.appendChild(card);
  });
}

async function generateMockResume() {
  elements.mockResumeBtn.disabled = true;
  try {
    const data = await apiPost("/api/resume/mock", buildSetupPayload());
    elements.resumeText.value = data.resumeText;
    state.resumeMode = "ai-generated";
    elements.modeButtons.forEach((button) => {
      button.classList.toggle("active", button.dataset.mode === "ai-generated");
    });
  } catch (error) {
    alert(error.message || "生成简历失败");
  } finally {
    elements.mockResumeBtn.disabled = false;
  }
}

async function startInterview() {
  const payload = buildSetupPayload();
  if (!payload.resumeText) {
    alert("先填一份简历，或者点击“生成 AI 简历草稿”。");
    return;
  }

  elements.startBtn.disabled = true;
  try {
    const session = await apiPost("/api/session/start", payload);
    state.session = session;
    renderRuntime(session.runtime);
    switchView("interview");
    renderSession();
    elements.answerInput.focus();
  } catch (error) {
    alert(error.message || "开始面试失败");
  } finally {
    elements.startBtn.disabled = false;
  }
}

async function submitAnswer() {
  const answer = elements.answerInput.value.trim();
  if (!answer || !state.session) {
    return;
  }

  elements.submitAnswerBtn.disabled = true;
  try {
    const session = await apiPost("/api/session/answer", {
      sessionId: state.session.sessionId,
      answer,
    });
    state.session = session;
    elements.answerInput.value = "";
    renderRuntime(session.runtime);

    if (session.isFinal) {
      renderResult(session.report);
      switchView("result");
      return;
    }

    renderSession();
    elements.answerInput.focus();
  } catch (error) {
    alert(error.message || "提交回答失败");
  } finally {
    elements.submitAnswerBtn.disabled = false;
  }
}

function renderSession() {
  const { selected, metrics, transcript, analysis } = state.session;
  elements.scoreIndicator.textContent = metrics.score;
  elements.stressIndicator.textContent = metrics.stress;
  elements.turnIndicator.textContent = `${metrics.turn} / ${metrics.maxTurns}`;
  elements.keywordIndicator.textContent = selected.interviewer.name;
  elements.stressFill.style.width = `${metrics.stress}%`;
  elements.sessionBrief.innerHTML = `
    <p><strong>${selected.role.title}</strong></p>
    <p>${selected.interviewer.name} · ${selected.difficulty.label}</p>
    <p>${analysis.themeBlurb}</p>
  `;

  elements.focusList.innerHTML = "";
  analysis.riskPoints.concat(analysis.followUpFocus).slice(0, 5).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    elements.focusList.appendChild(li);
  });

  elements.transcript.innerHTML = "";
  transcript.forEach((message) => {
    const bubble = document.createElement("article");
    bubble.className = `bubble ${message.speaker}`;
    const label = document.createElement("span");
    label.className = "bubble-label";
    label.textContent = speakerLabel(message.speaker);
    const content = document.createElement("div");
    content.textContent = message.text;
    bubble.append(label, content);
    elements.transcript.appendChild(bubble);
  });
  elements.transcript.scrollTop = elements.transcript.scrollHeight;
}

function renderResult(report) {
  const { selected, metrics } = state.session;
  elements.resultTitle.textContent = `${selected.role.title} 面试报告`;
  elements.resultBadge.textContent = report.verdict;
  elements.resultSummary.textContent = report.summary;
  elements.resultQuote.textContent = report.interviewerQuote;
  elements.resultTips.textContent = `${report.tips} 当前总分 ${metrics.score}，压力值 ${metrics.stress}。`;
  elements.highlightText.textContent = report.highlight;
  elements.flopText.textContent = report.flop;

  elements.dimensionGrid.innerHTML = "";
  Object.entries(report.dimensions).forEach(([key, value]) => {
    const card = document.createElement("div");
    card.className = "dimension-card";
    card.innerHTML = `<span>${dimensionLabels[key]}</span><strong>${value}</strong>`;
    elements.dimensionGrid.appendChild(card);
  });

  elements.shareLines.innerHTML = "";
  report.shareLines.forEach((line) => {
    const p = document.createElement("p");
    p.textContent = line;
    elements.shareLines.appendChild(p);
  });
}

function switchView(view) {
  elements.setupView.classList.toggle("active", view === "setup");
  elements.interviewView.classList.toggle("active", view === "interview");
  elements.resultView.classList.toggle("active", view === "result");
}

function resetToSetup() {
  state.session = null;
  elements.answerInput.value = "";
  switchView("setup");
}

function buildSetupPayload() {
  return {
    themeKeyword: "",
    roleId: state.selectedRoleId,
    interviewerId: state.selectedInterviewerId,
    difficulty: state.selectedDifficulty,
    resumeMode: state.resumeMode,
    resumeText: elements.resumeText.value.trim(),
  };
}

function speakerLabel(type) {
  return {
    interviewer: "面试官",
    question: "追问",
    candidate: "你",
    feedback: "判定",
  }[type] || "系统";
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
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "请求失败");
  }
  return data;
}
