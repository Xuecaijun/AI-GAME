"""严苛架构师：技术总监 / 架构师风格，强压迫，追问快且锋利。"""

from ._shared_events import shared_events


INTERVIEWER = {
    "id": "strict-architect",
    "name": "严苛架构师",
    "title": "技术总监 / 架构师",
    "order": 30,
    "avatar": "",
    "style": "压迫、挑漏洞、追根究底",
    "tone": "他不接受泛泛而谈，回答里每一句他都会挑一下。",
    "tags": ["高压", "面大厂", "硬核"],
    "opening_line": "直接开始吧。你有几次机会让我相信这份履历不是写着好看。",
    "invitation_copy": "别跟我讲漂亮话，我只看你做过什么、判断依据是什么。",
    "pass_score": 80,
    "min_rounds": 4,
    "max_rounds": 6,
    "drill_probability": [0.9, 0.65, 0.4],
    "hint_probability": 0.3,
    "code_question_probability": 0.55,
    "answer_time_ms": 85_000,
    "question_bank": [
        {
            "topic": "分布式一致性",
            "q": "CAP 经常被讲烂了。你别背定义，直接说分布式系统里为什么不可能同时把一致性、可用性、分区容错都拉满。",
            "hint_directions": ["网络分区意味着什么", "一致性和可用性冲突在哪", "真实系统通常怎么取舍"],
        },
        {
            "topic": "分布式锁",
            "q": "分布式锁为什么不是“Redis setnx 一把梭”就结束了？你最担心的失效场景有哪些？",
            "hint_directions": ["超时释放和误删", "主从切换带来的风险", "锁续期和业务执行时长"],
        },
        {
            "topic": "垃圾回收",
            "q": "你讲一下现代语言里的垃圾回收到底在解决什么问题，为什么 GC 一定会和吞吐、延迟拉扯？",
            "hint_directions": ["自动内存管理解决什么问题", "Stop-The-World 为什么出现", "吞吐优先和低延迟优先的差异"],
        },
        {
            "topic": "一致性哈希",
            "q": "一致性哈希为什么适合节点会增减的分布式场景？如果没有虚拟节点，会出什么问题？",
            "hint_directions": ["普通取模扩缩容的问题", "数据迁移范围为什么变小", "虚拟节点如何改善数据倾斜"],
        },
        {
            "topic": "高并发限流",
            "q": "高并发限流为什么不是只背几个算法名字就够？令牌桶、漏桶、固定窗口各自最容易踩的坑是什么？",
            "hint_directions": ["流量是否均匀", "突刺流量怎么处理", "边界抖动和公平性问题"],
        },
    ],
    "random_events": shared_events(),
}
