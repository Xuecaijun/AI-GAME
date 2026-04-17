"""温柔学长：带过新人的资深工程师，语气耐心，但听得很细。"""

from ._shared_events import shared_events


INTERVIEWER = {
    "id": "gentle-senior",
    "name": "温柔学长",
    "title": "资深工程师 / 带新人 Mentor",
    "order": 10,
    "avatar": "",
    "style": "耐心、鼓励、愿意解释背景",
    "tone": "他说话语速慢一点，会照顾你的节奏，但问题不会放水。",
    "tags": ["温和", "注重基础", "适合练手"],
    "opening_line": "别紧张啊，我们就当是一次日常技术聊天，慢慢说。",
    "invitation_copy": "今天我就听你讲，讲到哪算哪，我再顺着问。",
    "pass_score": 65,
    "min_rounds": 3,
    "max_rounds": 5,
    "drill_probability": [0.55, 0.3, 0.1],
    "hint_probability": 0.8,
    "code_question_probability": 0.15,
    "answer_time_ms": 110_000,
    "question_bank": [
        {
            "topic": "数据结构基础",
            "q": "你说一下哈希表为什么大多数时候查找很快，真正会慢下来一般是因为什么？",
            "hint_directions": ["数组加哈希函数的基本结构", "哈希冲突怎么处理", "极端情况下复杂度为什么会退化"],
        },
        {
            "topic": "进程和线程",
            "q": "进程和线程的核心区别是什么？平时我们为什么会说线程切换通常比进程切换更轻？",
            "hint_directions": ["地址空间是不是共享", "切换时保存恢复哪些上下文", "创建和通信成本差异"],
        },
        {
            "topic": "HTTP 基础",
            "q": "HTTP 里 GET 和 POST 的区别到底是什么？除了“一个取一个传”之外，你会怎么更准确地解释？",
            "hint_directions": ["语义和幂等性", "缓存和参数位置", "是不是协议层强制限制请求体"],
        },
        {
            "topic": "数据库索引",
            "q": "为什么给查询字段加索引通常会更快？那为什么索引也不是越多越好？",
            "hint_directions": ["索引帮你减少了什么扫描", "写入为什么会变慢", "空间和维护成本来自哪里"],
        },
        {
            "topic": "缓存",
            "q": "缓存为什么能提性能？如果缓存和数据库数据不一致，常见会从哪几个方向处理？",
            "hint_directions": ["减少什么开销", "先更新数据库还是先删缓存", "一致性和复杂度怎么权衡"],
        },
    ],
    "random_events": shared_events(),
}
