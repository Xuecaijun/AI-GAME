from __future__ import annotations

import random
from textwrap import dedent

ROLE_LIBRARY = [
    {
        "id": "ai-game-planner",
        "title": "AI 游戏策划",
        "summary": "为带有大模型交互的游戏设计玩法、反馈循环与数值逻辑。",
        "keywords": ["玩法设计", "数值", "叙事", "用户体验", "迭代", "数据分析"],
        "opening_questions": [
            "先用一分钟介绍你自己，并说说为什么适合 AI 游戏策划这个岗位。",
            "如果让你把一个普通 Web 互动改造成 AI 游戏，你会先改哪一层？",
        ],
    },
    {
        "id": "frontend-engineer",
        "title": "前端交互开发",
        "summary": "负责高反馈、高表现力的 Web 交互界面与状态流转。",
        "keywords": ["React", "状态管理", "交互设计", "性能优化", "组件", "可视化"],
        "opening_questions": [
            "你做过最复杂的一次前端交互是什么？请讲清目标、实现和结果。",
            "如果一个 AI 对话页面越来越复杂，你会怎么拆前端状态？",
        ],
    },
    {
        "id": "ai-application-engineer",
        "title": "AI 应用工程师",
        "summary": "负责模型调用、Prompt 编排、结构化输出和业务集成。",
        "keywords": ["Prompt", "RAG", "评估", "API 集成", "工作流", "容错"],
        "opening_questions": [
            "请讲一个你把大模型真正接进产品或工具链的案例。",
            "如果模型输出经常不稳定，你会怎么设计兜底机制？",
        ],
    },
    {
        "id": "product-manager",
        "title": "AI 产品策划",
        "summary": "负责用户问题定义、功能拆解、体验闭环与产品验证。",
        "keywords": ["需求分析", "用户研究", "增长", "原型", "指标", "跨团队协作"],
        "opening_questions": [
            "请介绍一个你主导过的产品方案，以及你如何验证它真的解决了问题。",
            "AI 产品最容易做成炫技 Demo，你会怎么避免这个问题？",
        ],
    },
]

TECHNICAL_ROLES = [
    {
        "id": "frontend-engineer",
        "title": "前端工程师",
        "summary": "负责 Web 前端界面、交互与状态管理，关注性能与工程化。",
        "keywords": ["React", "TypeScript", "状态管理", "性能优化", "组件设计", "可视化"],
        "opening_questions": [
            "先简单介绍一下你自己，以及你最近在做的前端项目。",
            "挑一个你做过的前端项目，讲讲里面最棘手的一个技术点。",
        ],
        "resume_lines": [
            "负责业务前端模块的架构与迭代，使用 React + TypeScript 推动组件沉淀与性能优化。",
            "参与前端工程化建设，规范构建流程、单测接入和线上监控。",
            "与后端、设计协作打磨复杂交互，关注首屏、交互反馈与线上异常指标。",
        ],
    },
    {
        "id": "backend-engineer",
        "title": "后端工程师",
        "summary": "负责服务端业务逻辑、数据库与接口设计，关注稳定性与性能。",
        "keywords": ["Java", "Go", "MySQL", "Redis", "分布式", "API 设计"],
        "opening_questions": [
            "先介绍一下你自己，以及你主要用什么后端技术栈。",
            "讲一个你经手过的服务端项目，重点说说你负责的那块设计。",
        ],
        "resume_lines": [
            "负责业务后端核心服务的设计与开发，使用 Java/Go 编写高并发接口。",
            "参与数据库表结构设计、索引优化和慢查询治理，保障线上稳定。",
            "协作推进缓存、消息队列接入，关注服务可用性和故障复盘。",
        ],
    },
    {
        "id": "algorithm-engineer",
        "title": "算法工程师",
        "summary": "负责机器学习/深度学习模型的训练、评估与落地。",
        "keywords": ["机器学习", "深度学习", "PyTorch", "特征工程", "模型评估", "Python"],
        "opening_questions": [
            "先自我介绍一下，最近在做什么方向的算法工作。",
            "挑一个你自己从头做下来的模型项目，说说你是怎么验证效果的。",
        ],
        "resume_lines": [
            "负责业务场景下的模型训练与评估，使用 PyTorch 完成从数据到上线的闭环。",
            "参与特征工程、样本构造和离线指标监控，持续迭代模型表现。",
            "和工程团队协作推动模型服务化部署，关注线上效果与回流数据。",
        ],
    },
    {
        "id": "fullstack-engineer",
        "title": "全栈工程师",
        "summary": "前后端一起做，关注从用户界面到数据链路的完整交付。",
        "keywords": ["Node.js", "React", "数据库", "接口设计", "工程化", "DevOps"],
        "opening_questions": [
            "先做个自我介绍，说说你做过的项目里前后端各自占比多少。",
            "如果让你从零搭一个小工具，你会怎么规划前后端分工和技术选型？",
        ],
        "resume_lines": [
            "独立负责中小型项目的前后端开发，覆盖需求拆解、接口设计、UI 实现与部署。",
            "使用 Node.js / React 搭建主要业务模块，关注开发效率与上线稳定性。",
            "参与基础设施和自动化流程建设，推动小团队工程规范落地。",
        ],
    },
    {
        "id": "ai-application-engineer",
        "title": "AI 应用工程师",
        "summary": "负责大模型应用的接入、Prompt 编排、结构化输出与业务集成。",
        "keywords": ["Python", "Prompt", "RAG", "LLM", "工作流", "评估"],
        "opening_questions": [
            "先介绍下你自己，以及你最近在做的大模型相关工作。",
            "讲一个你把 LLM 真正接进产品的案例，重点聊聊你踩过的坑。",
        ],
        "resume_lines": [
            "负责大模型应用的 Prompt 设计、链路编排与结构化输出适配。",
            "参与 RAG 检索方案、向量库选型与离线评估流程的搭建。",
            "和前后端协作推动 AI 能力的产品化落地，持续关注稳定性与成本。",
        ],
    },
    {
        "id": "client-engineer",
        "title": "客户端工程师",
        "summary": "负责 iOS / Android 客户端的开发、性能与稳定性。",
        "keywords": ["iOS", "Android", "Swift", "Kotlin", "性能优化", "稳定性"],
        "opening_questions": [
            "简单介绍下你自己，以及你主要做哪个端。",
            "挑一个你在客户端做过的优化或重构，说说背景和效果。",
        ],
        "resume_lines": [
            "负责移动端业务模块开发，关注启动速度、流畅度和崩溃率指标。",
            "参与架构分层、组件化拆分和工程化改造，提升团队协作效率。",
            "协同定位和修复线上疑难问题，沉淀稳定性治理经验。",
        ],
    },
    {
        "id": "test-engineer",
        "title": "测试开发工程师",
        "summary": "负责自动化测试、质量保障与工程流程治理。",
        "keywords": ["自动化测试", "Python", "接口测试", "回归", "CI", "质量保障"],
        "opening_questions": [
            "先自我介绍，聊聊你目前主要的测试技术栈。",
            "讲一个你主导搭建或改造过的自动化测试流程。",
        ],
        "resume_lines": [
            "负责业务的接口自动化、UI 自动化测试用例设计与维护。",
            "参与测试平台与 CI 流程建设，推动用例覆盖率与回归效率提升。",
            "协同开发定位缺陷，关注上线质量和线上问题复盘。",
        ],
    },
]

TECH_QUESTION_BANK = {
    "frontend-engineer": [
        {
            "topic": "React 渲染机制",
            "q": "聊一下 React 里 setState 之后组件为什么不会立刻同步更新，批量更新和调度大概是怎么回事？",
            "hint_directions": ["状态更新是同步还是异步可见", "批量更新为什么存在", "调度和渲染阶段怎么区分"],
            "difficulty": "medium",
            "related_skills": ["React", "状态管理"],
        },
        {
            "topic": "浏览器缓存",
            "q": "强缓存和协商缓存分别怎么工作？浏览器拿到 304 之前大概经历了什么判断过程？",
            "hint_directions": ["Cache-Control 和 Expires", "ETag 和 Last-Modified", "什么时候直接命中本地缓存"],
            "difficulty": "easy",
            "related_skills": ["性能优化"],
        },
        {
            "topic": "前端性能优化",
            "q": "一个页面首屏慢，你一般会从加载链路、资源体积和渲染阶段怎么拆问题？",
            "hint_directions": ["网络请求和资源加载", "打包体积与代码分割", "渲染阻塞和长任务"],
            "difficulty": "medium",
            "related_skills": ["React", "性能优化", "可视化"],
        },
        {
            "topic": "Diff 算法",
            "q": "React/Vue 这类框架做虚拟 DOM diff 时，为什么 key 很重要？key 用错会带来什么具体问题？",
            "hint_directions": ["节点复用怎么发生", "列表重排时会怎样", "状态错位为什么会出现"],
            "difficulty": "medium",
            "related_skills": ["React", "组件设计"],
        },
    ],
    "backend-engineer": [
        {
            "topic": "MySQL 索引",
            "q": "说一下 InnoDB 里的聚簇索引和二级索引结构差别，什么情况下会发生回表？",
            "hint_directions": ["叶子节点分别存什么", "主键索引和普通索引的区别", "覆盖索引为什么能避免回表"],
            "difficulty": "medium",
            "related_skills": ["MySQL", "数据库"],
        },
        {
            "topic": "Redis 持久化",
            "q": "Redis 的 RDB 和 AOF 各自适合什么场景？如果你只能选一种，判断依据会是什么？",
            "hint_directions": ["恢复速度和数据丢失窗口", "文件体积和写放大", "混合持久化解决什么问题"],
            "difficulty": "medium",
            "related_skills": ["Redis"],
        },
        {
            "topic": "事务隔离",
            "q": "MySQL 常见事务隔离级别分别解决了什么问题，又还会留下哪些并发异常？",
            "hint_directions": ["脏读 不可重复读 幻读", "Read Committed 和 Repeatable Read 的差别", "MVCC 在这里起什么作用"],
            "difficulty": "hard",
            "related_skills": ["MySQL", "数据库"],
        },
        {
            "topic": "接口幂等",
            "q": "下单或支付回调这类接口为什么必须做幂等？常见实现手段有哪些，各自风险点是什么？",
            "hint_directions": ["重复请求的来源", "唯一键 状态机 去重表", "并发下怎么避免重复执行"],
            "difficulty": "medium",
            "related_skills": ["API 设计", "分布式", "Java", "Go"],
        },
    ],
    "algorithm-engineer": [
        {
            "topic": "过拟合",
            "q": "模型训练里为什么会过拟合？你会从数据、模型复杂度和训练策略三个层面怎么缓解？",
            "hint_directions": ["训练集和验证集表现差异", "正则化与数据增强", "早停和模型容量控制"],
            "difficulty": "medium",
            "related_skills": ["机器学习", "深度学习", "模型评估"],
        },
        {
            "topic": "评估指标",
            "q": "分类问题里 precision、recall、F1 分别关注什么？什么业务场景会更偏向 recall？",
            "hint_directions": ["TP FP FN 分别影响什么", "漏判和误判代价", "指标之间为什么会互相拉扯"],
            "difficulty": "easy",
            "related_skills": ["模型评估", "机器学习"],
        },
        {
            "topic": "梯度下降",
            "q": "梯度下降为什么能工作？学习率过大或过小分别会出现什么现象？",
            "hint_directions": ["沿梯度反方向更新", "震荡和不收敛", "收敛过慢和局部最优"],
            "difficulty": "medium",
            "related_skills": ["深度学习", "机器学习", "Python"],
        },
        {
            "topic": "特征工程",
            "q": "做传统机器学习时，为什么特征工程往往直接决定上限？你会怎么判断一个特征值不值得留下？",
            "hint_directions": ["业务含义和可解释性", "信息增益或相关性", "线上可获取性和稳定性"],
            "difficulty": "medium",
            "related_skills": ["特征工程", "机器学习", "Python"],
        },
    ],
    "fullstack-engineer": [
        {
            "topic": "认证与鉴权",
            "q": "Session 和 JWT 分别适合什么场景？如果让你给一个中后台系统做登录态，你会怎么选？",
            "hint_directions": ["状态存在哪", "扩展性和失效控制", "安全风险和刷新机制"],
            "difficulty": "medium",
            "related_skills": ["Node.js", "接口设计"],
        },
        {
            "topic": "跨域",
            "q": "浏览器为什么会有跨域限制？一次带预检的 CORS 请求大概会经历哪些步骤？",
            "hint_directions": ["同源策略保护什么", "OPTIONS 预检为什么出现", "哪些请求头会触发预检"],
            "difficulty": "medium",
            "related_skills": ["React", "Node.js"],
        },
        {
            "topic": "系统拆层",
            "q": "一个小型全栈项目从前端到后端通常会怎么分层？哪些逻辑适合放前端，哪些必须放服务端？",
            "hint_directions": ["表现层和业务层", "权限与数据可信边界", "可复用逻辑和安全逻辑怎么分"],
            "difficulty": "medium",
            "related_skills": ["React", "Node.js", "数据库", "接口设计"],
        },
        {
            "topic": "部署发布",
            "q": "为什么很多 Web 项目上线都要做灰度发布？它和直接全量发布相比到底降低了什么风险？",
            "hint_directions": ["新版本风险怎么暴露", "流量比例怎么控制", "回滚成本为什么更低"],
            "difficulty": "easy",
            "related_skills": ["DevOps", "工程化"],
        },
    ],
    "ai-application-engineer": [
        {
            "topic": "RAG",
            "q": "RAG 为什么不只是“把知识库接给大模型”这么简单？一个基础 RAG 链路通常包含哪些关键阶段？",
            "hint_directions": ["切片 向量化 检索 重排 生成", "召回质量为什么关键", "上下文污染会带来什么问题"],
            "difficulty": "medium",
            "related_skills": ["RAG", "LLM", "工作流"],
        },
        {
            "topic": "Prompt 稳定性",
            "q": "同一个 Prompt 在不同时间输出不稳定，可能由哪些因素导致？你会怎么提高稳定性？",
            "hint_directions": ["模型温度和随机性", "指令边界是否清楚", "结构化输出和 few-shot 怎么帮助稳定"],
            "difficulty": "medium",
            "related_skills": ["Prompt", "LLM", "评估"],
        },
        {
            "topic": "幻觉问题",
            "q": "大模型为什么会产生幻觉？工程上通常怎么减轻，而不是只靠一句“不要胡编”？",
            "hint_directions": ["训练目标和概率生成", "检索增强与约束输出", "拒答策略和校验环节"],
            "difficulty": "medium",
            "related_skills": ["LLM", "RAG", "评估"],
        },
        {
            "topic": "成本与延迟",
            "q": "做 AI 应用时，为什么成本、延迟和效果经常互相拉扯？你会从哪些地方做取舍？",
            "hint_directions": ["模型大小与调用价格", "上下文长度和响应时间", "缓存 降级 批处理"],
            "difficulty": "medium",
            "related_skills": ["LLM", "工作流", "评估"],
        },
    ],
    "client-engineer": [
        {
            "topic": "内存泄漏",
            "q": "移动端为什么会出现内存泄漏？你通常会先怀疑哪些对象或引用关系？",
            "hint_directions": ["生命周期和长引用", "单例 回调 闭包", "Activity/View/Controller 持有链"],
            "difficulty": "medium",
            "related_skills": ["iOS", "Android", "稳定性"],
        },
        {
            "topic": "卡顿分析",
            "q": "一个客户端页面明显掉帧，你会从主线程、渲染和资源加载怎么排查？",
            "hint_directions": ["主线程是否被重活阻塞", "布局 绘制 过度渲染", "图片和 I/O 的影响"],
            "difficulty": "medium",
            "related_skills": ["iOS", "Android", "性能优化"],
        },
        {
            "topic": "启动优化",
            "q": "App 启动慢通常拆成哪几个阶段看？冷启动和热启动的优化思路有什么不同？",
            "hint_directions": ["进程启动和初始化", "首屏可见前做了什么", "延迟初始化为什么有效"],
            "difficulty": "medium",
            "related_skills": ["性能优化", "iOS", "Android"],
        },
        {
            "topic": "崩溃治理",
            "q": "线上崩溃率治理一般不是只修一个 bug 就完了，你觉得完整闭环应该包含哪些环节？",
            "hint_directions": ["采集 聚类 排查 修复 复盘", "版本和机型维度分析", "如何避免同类问题再出现"],
            "difficulty": "easy",
            "related_skills": ["稳定性", "iOS", "Android"],
        },
    ],
    "test-engineer": [
        {
            "topic": "测试分层",
            "q": "单元测试、接口测试、UI 自动化测试分别更适合兜什么风险？为什么不能只押一种？",
            "hint_directions": ["反馈速度和维护成本", "覆盖范围和稳定性", "测试金字塔为什么存在"],
            "difficulty": "medium",
            "related_skills": ["自动化测试", "接口测试", "质量保障"],
        },
        {
            "topic": "回归策略",
            "q": "版本临发前为什么不是把所有用例全跑一遍就最好？你会怎么设计有优先级的回归策略？",
            "hint_directions": ["时间成本和收益", "核心链路 高风险变更", "冒烟 回归 全量之间怎么取舍"],
            "difficulty": "medium",
            "related_skills": ["回归", "质量保障", "CI"],
        },
        {
            "topic": "缺陷定位",
            "q": "同一个线上问题，测试和开发常常都说不是自己的锅。你会怎样构造证据让定位更快收敛？",
            "hint_directions": ["复现步骤和环境信息", "日志 抓包 trace", "最小化复现和边界条件"],
            "difficulty": "medium",
            "related_skills": ["自动化测试", "接口测试", "质量保障"],
        },
        {
            "topic": "自动化价值",
            "q": "什么样的场景适合做自动化测试，什么样的场景做了反而维护成本会很高？",
            "hint_directions": ["稳定规则和高频回归", "页面变化快是否适合 UI 自动化", "投入产出比怎么判断"],
            "difficulty": "easy",
            "related_skills": ["自动化测试", "回归", "质量保障"],
        },
    ],
}

WORKPLACE_QUESTION_BANK = [
    {
        "topic": "到岗时间",
        "q": "如果这边流程推进顺利，你最快多久可以到岗？",
        "hint_directions": ["先给明确时间", "再说明当前状态或交接安排", "避免只说尽快"],
    },
    {
        "topic": "工作生活冲突",
        "q": "如果项目高峰期和你的个人生活安排发生冲突，你一般会怎么处理？",
        "hint_directions": ["先说原则", "再说沟通和优先级判断", "补一个现实边界"],
    },
    {
        "topic": "加班沟通",
        "q": "如果临时出现加班需求，但你原本已经有安排了，你会怎么和团队沟通？",
        "hint_directions": ["先表态是否能支持", "再说怎么同步风险和边界", "体现沟通而不是硬扛"],
    },
    {
        "topic": "岗位预期",
        "q": "如果入职后发现实际工作内容和你原本理解的不完全一样，你会怎么处理？",
        "hint_directions": ["先确认差异", "再沟通预期", "最后说自己的适应策略"],
    },
    {
        "topic": "工作诉求",
        "q": "你选工作时通常更看重什么，比如薪资、成长、团队氛围，你会怎么权衡？",
        "hint_directions": ["先给排序", "再解释为什么", "别回答得过于模板化"],
    },
]

DIFFICULTIES = {
    "easy": {
        "label": "Easy",
        "description": "简历与岗位高度匹配，问题较基础。",
        "resume_gap": "low",
        "starting_stress": 18,
        "max_turns": 4,
        "score_multiplier": 0.85,
    },
    "normal": {
        "label": "Normal",
        "description": "有少量模糊点，开始出现追问。",
        "resume_gap": "mid",
        "starting_stress": 24,
        "max_turns": 4,
        "score_multiplier": 1.0,
    },
    "hard": {
        "label": "Hard",
        "description": "简历会埋下明显风险点，追问更密集。",
        "resume_gap": "high",
        "starting_stress": 32,
        "max_turns": 5,
        "score_multiplier": 1.1,
    },
    "expert": {
        "label": "Expert",
        "description": "回答一旦不自洽，就会被连续施压。",
        "resume_gap": "very_high",
        "starting_stress": 40,
        "max_turns": 5,
        "score_multiplier": 1.2,
    },
    "master": {
        "label": "Master",
        "description": "人设反差大，高压追问，适合比赛展示。",
        "resume_gap": "extreme",
        "starting_stress": 48,
        "max_turns": 6,
        "score_multiplier": 1.3,
    },
}

CODE_QUESTION_BANK = [
    {
        "id": "two-sum",
        "title": "两数之和",
        "difficulty": "easy",
        "topic": "数组 / 哈希",
        "description": (
            "给定一个整数数组 nums 和一个目标值 target，返回数组中两个元素的下标，使它们相加等于 target。\n"
            "假设每组输入只有一个答案，同一元素不能使用两次。请尽量给出比 O(n^2) 更好的做法。"
        ),
        "signature": "def two_sum(nums: list[int], target: int) -> list[int]:",
        "examples": [
            {"input": "nums=[2,7,11,15], target=9", "output": "[0,1]"},
            {"input": "nums=[3,2,4], target=6", "output": "[1,2]"},
        ],
    },
    {
        "id": "reverse-linked-list",
        "title": "反转链表",
        "difficulty": "easy",
        "topic": "链表",
        "description": (
            "给你一个单链表的头结点 head，将其反转，并返回反转后的头结点。\n"
            "可以给出迭代或递归任一写法，解释一下你选这种写法的理由。"
        ),
        "signature": "def reverse_list(head: ListNode | None) -> ListNode | None:",
        "examples": [
            {"input": "head: 1->2->3->4->5", "output": "5->4->3->2->1"},
            {"input": "head: 1->2", "output": "2->1"},
        ],
    },
    {
        "id": "valid-parentheses",
        "title": "有效的括号",
        "difficulty": "easy",
        "topic": "栈",
        "description": (
            "给定一个只包括 '()'、'[]'、'{}' 的字符串 s，判断字符串是否有效。\n"
            "有效字符串需满足：左括号必须用相同类型的右括号闭合，且以正确的顺序闭合。"
        ),
        "signature": "def is_valid(s: str) -> bool:",
        "examples": [
            {"input": 's="()[]{}"', "output": "True"},
            {"input": 's="(]"', "output": "False"},
        ],
    },
    {
        "id": "lru-cache",
        "title": "LRU 缓存",
        "difficulty": "medium",
        "topic": "哈希 / 双向链表",
        "description": (
            "实现一个 LRU 缓存类：支持 get(key) 与 put(key, value)，容量固定 capacity。\n"
            "要求 get / put 的平均时间复杂度为 O(1)，当缓存满时淘汰最久未使用的键。"
        ),
        "signature": "class LRUCache:\n    def __init__(self, capacity: int): ...\n    def get(self, key: int) -> int: ...\n    def put(self, key: int, value: int) -> None: ...",
        "examples": [
            {"input": "capacity=2, put(1,1) put(2,2) get(1) put(3,3) get(2)", "output": "1, -1"},
        ],
    },
    {
        "id": "longest-substring",
        "title": "最长无重复字符子串",
        "difficulty": "medium",
        "topic": "滑动窗口",
        "description": (
            "给定一个字符串 s，找到其中不含有重复字符的最长子串的长度。\n"
            "请说明你的时间复杂度。"
        ),
        "signature": "def length_of_longest_substring(s: str) -> int:",
        "examples": [
            {"input": 's="abcabcbb"', "output": "3"},
            {"input": 's="bbbbb"', "output": "1"},
        ],
    },
    {
        "id": "merge-intervals",
        "title": "合并区间",
        "difficulty": "medium",
        "topic": "排序 / 数组",
        "description": (
            "给出一个区间的集合，合并所有重叠的区间，并返回合并后的结果。\n"
            "区间以 [start, end] 形式给出。"
        ),
        "signature": "def merge(intervals: list[list[int]]) -> list[list[int]]:",
        "examples": [
            {"input": "[[1,3],[2,6],[8,10],[15,18]]", "output": "[[1,6],[8,10],[15,18]]"},
        ],
    },
    {
        "id": "token-bucket",
        "title": "简易令牌桶限流器",
        "difficulty": "medium",
        "topic": "限流 / 并发",
        "description": (
            "实现一个令牌桶限流器：每秒向桶中放入 rate 个令牌（桶容量为 capacity，满了不再加）。\n"
            "调用 allow() 时，如果桶里有令牌则扣 1 并返回 True，否则返回 False。\n"
            "可以用单线程即可，说明你如何处理时间精度。"
        ),
        "signature": "class TokenBucket:\n    def __init__(self, rate: float, capacity: int): ...\n    def allow(self) -> bool: ...",
        "examples": [
            {"input": "rate=5, capacity=5, 每秒调用 10 次", "output": "前 5 次 True，后 5 次 False"},
        ],
    },
    {
        "id": "binary-search",
        "title": "二分查找（左边界）",
        "difficulty": "easy",
        "topic": "二分",
        "description": (
            "给定一个升序整数数组 nums 和目标值 target，返回 target 第一次出现的下标；\n"
            "若不存在，返回应插入的位置（保持有序）。"
        ),
        "signature": "def search_left(nums: list[int], target: int) -> int:",
        "examples": [
            {"input": "nums=[1,3,5,5,7], target=5", "output": "2"},
            {"input": "nums=[1,3,5,5,7], target=4", "output": "2"},
        ],
    },
]


COMMON_SKILLS = [
    "Python",
    "JavaScript",
    "TypeScript",
    "Unity",
    "数据分析",
    "用户研究",
    "Prompt",
    "A/B 测试",
    "运营",
    "SQL",
    "Figma",
    "React",
]

CUSTOM_ROLE_PROFILES = [
    {
        "hints": ["技术美术", "ta", "tech art", "美术技术", "shader", "特效美术"],
        "keywords": ["Shader", "渲染表现", "美术管线", "性能优化", "Unity", "工具开发"],
        "summary_template": "围绕视觉表现落地、技术约束平衡与美术流程提效展开，重点考察 {focus}。",
        "opening_questions": [
            "请讲一次你在视觉效果、性能限制和开发周期之间做平衡取舍的经历。",
            "如果项目里美术资源效果很好但性能压力过大，你会如何定位问题并推动优化方案落地？",
        ],
        "resume_lines": [
            "负责角色与场景效果的技术支持，优化 Shader、材质表现和实时渲染效果，保证画面质量与性能平衡。",
            "参与搭建美术制作规范与资源导入流程，协助策划、程序和美术团队提升协作效率。",
            "围绕 Unity 项目中的特效、后处理和资源性能问题进行排查与工具化支持，推动版本稳定迭代。",
        ],
    },
    {
        "hints": ["教师", "老师", "讲师", "班主任", "教研", "培训师", "辅导员"],
        "keywords": ["课程设计", "课堂管理", "学情分析", "表达沟通", "因材施教", "教学复盘"],
        "summary_template": "围绕教学目标达成、课堂组织与学生成长展开，重点考察 {focus}。",
        "opening_questions": [
            "请介绍一次你针对不同学生情况调整教学方式的经历，以及最后的效果。",
            "如果让你接手一个基础参差不齐的班级，你会如何设计教学目标、课堂节奏和复盘方式？",
        ],
        "resume_lines": [
            "负责课程方案设计、课堂组织与课后反馈整理，持续优化教学体验。",
            "基于学生表现和作业数据调整授课节奏，提升班级整体达成度。",
            "与家长或教研团队协作推进教学计划，沉淀可复用的教学资料。",
        ],
    },
    {
        "hints": ["医生", "医师", "护士", "医疗", "药师", "康复", "临床"],
        "keywords": ["病情评估", "诊疗流程", "医患沟通", "风险意识", "病例记录", "协同配合"],
        "summary_template": "围绕诊疗判断、流程执行与患者沟通展开，重点考察 {focus}。",
        "opening_questions": [
            "请讲一次你在时间紧张或信息不完整的情况下完成判断和处置的经历。",
            "如果遇到患者或家属对方案有疑虑，你会如何沟通、记录并推动后续处理？",
        ],
        "resume_lines": [
            "参与患者评估、流程执行与病例记录，关注关键风险点和交接质量。",
            "在规范流程下完成多环节协同，保障诊疗或护理工作稳定推进。",
            "重视与患者及家属的沟通反馈，结合实际情况持续优化处理方式。",
        ],
    },
    {
        "hints": ["律师", "法务", "法律", "合规", "律所"],
        "keywords": ["法律检索", "合同审核", "风险判断", "证据梳理", "沟通谈判", "合规意识"],
        "summary_template": "围绕法律判断、风险控制与沟通推进展开，重点考察 {focus}。",
        "opening_questions": [
            "请分享一次你梳理复杂事实关系并形成法律判断的经历。",
            "如果业务方希望快速推进但存在明显法律风险，你会如何给出可执行建议？",
        ],
        "resume_lines": [
            "参与合同审核、条款梳理与法律风险提示，支持业务稳妥推进。",
            "负责法规检索、证据整理和案例分析，形成清晰的判断依据。",
            "在沟通协同中平衡业务效率与合规要求，推动方案落地。",
        ],
    },
    {
        "hints": ["会计", "财务", "审计", "税务", "出纳", "成本"],
        "keywords": ["账务处理", "报表分析", "成本控制", "预算管理", "风险意识", "细节准确性"],
        "summary_template": "围绕财务准确性、报表分析与风险控制展开，重点考察 {focus}。",
        "opening_questions": [
            "请讲一个你通过对账、分析或复核发现异常并推动解决的问题。",
            "如果你接手一项时间紧、数据多、关联部门复杂的财务工作，你会如何保证准确性和进度？",
        ],
        "resume_lines": [
            "负责账务整理、报表输出与数据复核，关注准确性和时效性。",
            "参与预算跟踪、成本分析和异常排查，为业务提供财务支持。",
            "与业务及外部协作方沟通关键数据口径，推动流程规范化。",
        ],
    },
    {
        "hints": ["销售", "商务", "客户经理", "招商主管", "bd", "business development"],
        "keywords": ["客户沟通", "需求挖掘", "方案呈现", "商机推进", "谈判能力", "结果导向"],
        "summary_template": "围绕客户理解、商机转化与关系推进展开，重点考察 {focus}。",
        "opening_questions": [
            "请分享一次你从客户线索到推动成交的完整过程，重点讲讲关键转折点。",
            "如果客户需求频繁变化、内部资源又有限，你会如何稳住节奏并推进结果？",
        ],
        "resume_lines": [
            "负责客户拜访、需求挖掘和方案沟通，推动商机向成交转化。",
            "根据客户反馈调整推进策略，协调内部资源提升交付确定性。",
            "跟进关键节点数据和复盘结果，持续优化销售节奏与转化效率。",
        ],
    },
    {
        "hints": ["运营", "新媒体", "内容", "社群", "投放", "增长"],
        "keywords": ["内容策划", "用户运营", "数据分析", "活动执行", "转化优化", "节奏把控"],
        "summary_template": "围绕内容、用户与转化结果展开，重点考察 {focus}。",
        "opening_questions": [
            "请讲一个你策划并执行的内容或活动项目，最后是如何衡量效果的。",
            "如果一个渠道数据持续下滑，你会如何拆解问题并安排后续动作？",
        ],
        "resume_lines": [
            "负责内容策划、活动执行与用户反馈整理，关注数据表现和转化效率。",
            "基于渠道数据和用户行为调整节奏，优化留存、互动或转化结果。",
            "与设计、商务或产品协同推进项目落地，并持续复盘迭代。",
        ],
    },
    {
        "hints": ["行政", "人事", "hr", "招聘", "组织发展", "培训"],
        "keywords": ["招聘流程", "组织协调", "沟通推进", "员工体验", "流程管理", "数据复盘"],
        "summary_template": "围绕组织协同、流程执行与人才支持展开，重点考察 {focus}。",
        "opening_questions": [
            "请介绍一次你协调多方资源推进招聘、培训或组织事务的经历。",
            "如果岗位需求变化快、候选人体验又容易受影响，你会如何兼顾效率和质量？",
        ],
        "resume_lines": [
            "参与招聘、入转调离或培训支持等流程，推动组织事务稳定运行。",
            "负责信息整理、进度跟踪与跨部门沟通，保障关键节点按时完成。",
            "关注员工或候选人反馈，结合数据持续优化流程体验。",
        ],
    },
]


def get_role(role_id: str) -> dict:
    return next((item for item in ROLE_LIBRARY if item["id"] == role_id), ROLE_LIBRARY[0])


def get_technical_role(role_id: str = "") -> dict:
    """技术面岗位解析：只从 TECHNICAL_ROLES 中选，找不到回退首位。"""

    normalized = (role_id or "").strip()
    if normalized == "random" or not normalized:
        return copy_role(random.choice(TECHNICAL_ROLES))
    matched = next((item for item in TECHNICAL_ROLES if item["id"] == normalized), None)
    if matched:
        return copy_role(matched)
    return copy_role(TECHNICAL_ROLES[0])


def get_difficulty(difficulty_id: str) -> dict:
    return DIFFICULTIES.get(difficulty_id, DIFFICULTIES["normal"])


def get_tech_questions(role_id: str) -> list[dict]:
    bank = TECH_QUESTION_BANK.get(role_id, [])
    return [dict(item) for item in bank]


def get_workplace_questions() -> list[dict]:
    return [dict(item) for item in WORKPLACE_QUESTION_BANK]


def resolve_role(role_id: str = "", role_title: str = "", interview_track: str = "") -> dict:
    normalized_id = (role_id or "").strip()
    normalized_title = (role_title or "").strip()

    # 技术面强制走计算机领域岗位，忽略自定义/随机/非技术岗位
    if interview_track == "technical":
        return get_technical_role(normalized_id)

    if normalized_title:
        return build_custom_role(normalized_title, role_id=normalized_id or "custom-role")

    if normalized_id == "random":
        return random.choice(get_random_role_candidates())

    matched = next((item for item in ROLE_LIBRARY if item["id"] == normalized_id), None)
    if matched:
        return copy_role(matched)

    return copy_role(ROLE_LIBRARY[0])


def build_theme_blurb(keyword: str, role: dict) -> str:
    if not keyword:
        return f"你面试的岗位是“{role['title']}”，公司正在寻找能把 AI 落到真实体验里的成员。"
    return (
        f"本场比赛关键词是“{keyword}”。你面试的岗位是“{role['title']}”，"
        f"你需要证明自己能把“{keyword}”真正融入产品体验，而不是只写在包装文案里。"
    )


def generate_mock_resume(role: dict, keyword: str, difficulty: dict) -> str:
    keyword_text = keyword or "AI 面试训练"
    gap_level = difficulty["resume_gap"]
    keyword_line = "、".join(role["keywords"][:4]) if role.get("keywords") else "项目推进、分析复盘、跨团队协作"
    project_focus = role["keywords"][0] if role.get("keywords") else role["title"]
    resume_lines = role.get("resume_lines") or [
        f"负责“{keyword_text} 智能体验”项目的需求拆解与方案设计，围绕{project_focus}完成从调研到上线复盘的闭环。",
        "参与“多轮对话式面试助手”项目，整理追问逻辑、评分维度与结果报告文案，并推动版本迭代。",
        "和前后端协作完成 Demo 上线，支持在短周期内快速试错和优化体验。",
    ]

    extra_skill = {
        "low": "擅长把复杂需求拆成清晰流程，并持续复盘结果。",
        "mid": "能快速做出 Demo，并与设计、研发和业务团队对齐。",
        "high": "简历里提到了多模块协同、A/B 测试与增长实验，但细节未完全展开。",
        "very_high": "自称主导过高影响力项目优化，并列出了多项高级能力，存在明显可追问空间。",
        "extreme": "履历极其亮眼，覆盖策略、增长、落地与跨部门推进，真实性需要严格验证。",
    }[gap_level]

    risky_line = {
        "low": "项目描述整体自洽，漏洞较少。",
        "mid": f"曾参与一个以“{keyword_text}”为主题的项目，但职责边界略显模糊。",
        "high": f"在“{keyword_text} 智能平台”项目中写了“独立负责核心策略”，但没有展开验证方法。",
        "very_high": f"在“{keyword_text} AI 平台”项目里写了“全面提升留存与转化”，缺少关键指标解释。",
        "extreme": f"在“{keyword_text} 全链路系统”中自称覆盖从 0 到 1 全部工作，容易被质疑是否夸大。",
    }[gap_level]

    return dedent(
        f"""
        姓名：林岚
        应聘岗位：{role['title']}
        教育背景：某综合大学，本科，信息管理与数字媒体相关专业
        核心技能：{keyword_line}、{role['title']}相关实践、跨团队协作、复盘总结
        项目经历：
        1. {resume_lines[0]}
        2. {resume_lines[1]}
        3. {resume_lines[2]}
        补充说明：{extra_skill}
        潜在风险：{risky_line}
        """
    ).strip()


def build_custom_role(role_title: str, role_id: str = "custom-role") -> dict:
    title = role_title.strip()
    profile = match_custom_role_profile(title)
    keywords = infer_keywords_from_role(title, profile)
    opening_questions = build_custom_opening_questions(title, profile)
    return {
        "id": sanitize_role_id(role_id or title),
        "title": title,
        "summary": build_role_summary(title, keywords, profile),
        "keywords": keywords,
        "opening_questions": opening_questions,
        "resume_lines": build_resume_lines(title, profile),
        "is_custom": True,
    }


def infer_keywords_from_role(role_title: str, profile: dict | None = None) -> list[str]:
    if profile:
        return list(profile["keywords"])

    title = role_title.lower()
    keyword_groups = [
        (["技术美术", "tech art", "ta", "shader", "特效"], ["Shader", "渲染表现", "美术管线", "性能优化", "Unity", "工具开发"]),
        (["前端", "frontend", "web", "h5"], ["React", "TypeScript", "交互设计", "性能优化", "组件设计", "可视化"]),
        (["后端", "backend", "服务端", "java", "python"], ["Python", "API 设计", "数据库", "服务治理", "性能优化", "稳定性"]),
        (["算法", "algorithm", "机器学习", "model"], ["机器学习", "特征工程", "模型评估", "Python", "实验设计", "数据分析"]),
        (["数据", "data", "分析", "bi"], ["SQL", "数据分析", "指标体系", "实验设计", "可视化", "业务洞察"]),
        (["产品", "product", "pm"], ["需求分析", "用户研究", "原型设计", "指标设计", "项目推进", "跨团队协作"]),
        (["运营", "operation", "growth"], ["增长", "活动策划", "数据分析", "用户运营", "转化优化", "内容策略"]),
        (["设计", "designer", "ux", "ui"], ["用户体验", "Figma", "交互设计", "视觉表达", "设计系统", "原型"]),
        (["测试", "qa", "quality"], ["测试用例", "自动化测试", "缺陷分析", "质量保障", "回归测试", "风险控制"]),
        (["销售", "business", "商务"], ["客户沟通", "方案呈现", "需求挖掘", "商机推进", "谈判", "结果导向"]),
        (["人力", "hr", "招聘"], ["招聘流程", "人才评估", "沟通协调", "组织规划", "候选人体验", "数据复盘"]),
        (["财务", "finance"], ["财务分析", "预算管理", "成本控制", "报表", "风险意识", "业务协同"]),
        (["游戏", "game"], ["玩法设计", "数值", "叙事", "用户体验", "活动设计", "版本迭代"]),
        (["ai", "人工智能", "大模型", "llm"], ["Prompt", "工作流", "模型评估", "RAG", "自动化", "AI 产品化"]),
    ]

    for hints, keywords in keyword_groups:
        if any(hint in title for hint in hints):
            return keywords

    return ["沟通协作", "项目推进", "问题拆解", "数据分析", "执行落地", "复盘优化"]


def build_role_summary(role_title: str, keywords: list[str], profile: dict | None = None) -> str:
    focus = "、".join(keywords[:3]) if keywords else "问题拆解、执行与协作"
    if profile and profile.get("summary_template"):
        return str(profile["summary_template"]).format(role=role_title, focus=focus)
    return f"围绕 {role_title} 的核心工作展开，重点考察 {focus} 等能力。"


def build_custom_opening_questions(role_title: str, profile: dict | None = None) -> list[str]:
    if profile and profile.get("opening_questions"):
        return list(profile["opening_questions"])
    return [
        f"先介绍一下你自己，并说明为什么适合 {role_title} 这个岗位。",
        f"如果让你从 0 到 1 推进一项与 {role_title} 相关的工作，你会如何拆解目标、执行和验证？",
    ]


def build_resume_lines(role_title: str, profile: dict | None = None) -> list[str]:
    if profile and profile.get("resume_lines"):
        return list(profile["resume_lines"])
    return [
        f"负责与 {role_title} 相关项目的需求拆解、执行推进与阶段复盘，推动工作稳定落地。",
        "参与跨团队协作项目，整理关键流程、结果指标与风险点，支持持续迭代。",
        "根据反馈和数据调整执行节奏，在有限时间内优化结果与体验。",
    ]


def match_custom_role_profile(role_title: str) -> dict | None:
    normalized = role_title.lower()
    for profile in CUSTOM_ROLE_PROFILES:
        if any(hint.lower() in normalized for hint in profile["hints"]):
            return profile
    return None


def sanitize_role_id(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return cleaned or "custom-role"


def copy_role(role: dict) -> dict:
    return {
        "id": role["id"],
        "title": role["title"],
        "summary": role["summary"],
        "keywords": list(role.get("keywords", [])),
        "opening_questions": list(role.get("opening_questions", [])),
        **({"resume_lines": list(role["resume_lines"])} if "resume_lines" in role else {}),
        **({"is_custom": role["is_custom"]} if "is_custom" in role else {}),
    }


def get_random_role_candidates() -> list[dict]:
    candidates = [copy_role(role) for role in ROLE_LIBRARY]
    seen_titles = {role["title"] for role in candidates}

    for profile in CUSTOM_ROLE_PROFILES:
        title = str(profile.get("random_title") or profile["hints"][0]).strip()
        if not title or title in seen_titles:
            continue
        candidates.append(build_custom_role(title, role_id=f"random-{sanitize_role_id(title)}"))
        seen_titles.add(title)

    return candidates
