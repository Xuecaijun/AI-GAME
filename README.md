# ShowMeTheOffer · 终面：AI面试官

一个 AI 面试网页小游戏：简历 → 面试邀请 → 仿腾讯会议的面试间（AI 出题 / 判题 / 深挖 / 提示 / 随机事件 / 计时） → Offer 或未录用。
内置两套运行模式：

- `Mock 模式`：不配大模型也能本地跑通整条链路。
- `LLM 模式`：配置 OpenAI 兼容接口后，出题、判题、提示、总结、Offer 信都由大模型生成。

## 目录结构

```text
backends/tech_interview_backend/
  engine.py              轮次状态机：ask / answer / judge / drill / hint / event / final
  events.py              随机事件引擎（掷骰 / 结算 / 一次性触发）
  interviewers/          面试官注册表 —— 新增面试官 = 新建一个 .py 文件
    gentle_senior.py
    steady_engineer.py
    strict_architect.py
  ai_client.py           LLM 调用封装
  prompts.py             各阶段 prompt 模板
  mock_content.py        岗位 / 难度 / AI 简历草稿生成
  resume_parser.py       PDF / DOCX / TXT / MD 简历解析
web/
  index.html             四步流程（简历 → 邀请 → 仿 TX 会议 → 结果）
  styles.css
  app.js
server.py                本地 HTTP 服务入口
requirements.txt         可选依赖（简历解析）
```

## 快速运行

```bash
pip install -r requirements.txt
python server.py
```

访问 `http://127.0.0.1:8765`。

## 接入大模型

复制 `.env.example` 为 `.env` 填入配置：

```env
OPENAI_API_KEY=你的密钥
OPENAI_BASE_URL=https://你的兼容服务/v1
OPENAI_MODEL=你的模型名
AI_GAME_FORCE_MOCK=0
```

没有配置或配置无效时，系统自动回退为 Mock 模式，不会中断流程。

## 核心玩法

1. 粘贴或 AI 生成一份简历，选择难度和应聘岗位。
   也可以直接上传 `.pdf` / `.docx` / `.txt` / `.md` 简历自动解析成文本。
2. 系统分析简历，随机抽 3 位面试官发出邀请，玩家择一接受。
3. 进入仿腾讯会议的面试间，按轮次作答：
   - 每题有倒计时，超时按放弃处理并计入最低分。
   - 答对有概率被深挖（最多 3 层，每层概率由面试官配置）。
   - 答错有概率获得提示再答（最多 3 次，否则本轮收束）。
   - 轮内 / 轮间会按概率触发随机事件（旁白 / 选择题 / 文字输入），部分事件会影响分数甚至直接终结面试。
   - 技术面中间可能切到编程题，前端会打开代码弹窗，后端只做 AI 静态点评，不执行代码。
4. 每轮结算出一个轮分（满分 100），多轮平均后与面试官的 `pass_score` 比较：达到则发出 Offer 文案，否则显示未录用卡片；六维评分仅用于结果页的复盘展示。

## 扩展：新增一位面试官

在 `backends/tech_interview_backend/interviewers/` 下新建一个 `.py` 文件，导出 `INTERVIEWER` 字典，包含人设、通过线、题库、深挖 / 提示概率、随机事件即可。框架会在进程启动时自动加载，无需改动其它文件。

## API 速览

- `GET  /api/bootstrap` 返回岗位、难度、运行模式。
- `POST /api/resume/mock` 生成一份可演示的 AI 简历。
- `POST /api/resume/upload` 上传简历文件（JSON：`{ filename, base64 }`）。
- `POST /api/invitations` 分析简历并抽样 3 位面试官。
- `POST /api/session/start` 开始面试，返回首个"阶段描述符"。
- `POST /api/session/answer` 提交回答，返回下一阶段描述符。
- `POST /api/session/timeout` 当前题超时通知。
- `POST /api/session/event` 玩家对随机事件的回应（选项 id 或文本）。

阶段描述符统一结构：`{ phase, question?, questionType?, codeQuestion?, eventNote?, timerMs?, event?, metrics, transcript, isFinal, report? }`。
