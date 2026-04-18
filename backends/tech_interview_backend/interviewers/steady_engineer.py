"""稳重工程师：业务线资深工程师，问题密度适中，追问讲逻辑。"""

from ._shared_events import shared_events


INTERVIEWER = {
    "id": "steady-engineer",
    "name": "稳重工程师",
    "title": "业务线资深工程师",
    "order": 20,
    "avatar": "",
    "style": "理性、讲逻辑、抓细节但不咄咄逼人",
    "tone": "他更关心你的判断过程，回答含糊会被顺着往下问。",
    "tags": ["标准难度", "重判断", "工程向"],
    "opening_line": "好，咱们正式开始。你先讲，我会挑几个点往下问。",
    "invitation_copy": "我比较看回答背后的判断，你照你自己的节奏讲就行。",
    "pass_score": 72,
    "min_rounds": 3,
    "max_rounds": 5,
    "drill_probability": [0.75, 0.5, 0.25],
    "hint_probability": 0.5,
    "code_question_probability": 0.35,
    "answer_time_ms": 95_000,
    "question_bank": [
        {
            "topic": "Redis 持久化",
            "q": "Redis 的 RDB 和 AOF 各自适合什么场景？如果线上只能二选一，你会怎么权衡？",
            "hint_directions": ["恢复速度和数据丢失窗口", "性能开销和文件体积", "混合持久化为什么会出现"],
        },
        {
            "topic": "数据库事务",
            "q": "MySQL 事务隔离级别主要是在解决什么问题？Repeatable Read 为什么还会经常被单独拿出来讲？",
            "hint_directions": ["脏读 不可重复读 幻读", "MVCC 和快照读", "为什么默认隔离级别常被选为 RR"],
        },
        {
            "topic": "服务幂等",
            "q": "接口幂等为什么在支付、回调、消息消费这类场景里特别重要？工程上通常怎么做？",
            "hint_directions": ["重复请求从哪来", "唯一键 状态机 去重表", "并发下的竞态条件"],
        },
        {
            "topic": "连接池",
            "q": "数据库连接池为什么能提升吞吐？如果池子参数配得不合适，常见会出什么问题？",
            "hint_directions": ["建连成本在哪里", "最大连接数与等待队列", "连接泄漏和雪崩风险"],
        },
        {
            "topic": "消息队列",
            "q": "消息队列为什么能削峰解耦，但又为什么会把系统复杂度抬上去？",
            "hint_directions": ["异步化和流量缓冲", "顺序 重复 消息丢失", "最终一致性和补偿逻辑"],
        },
    ],
    "random_events": shared_events(),
}
