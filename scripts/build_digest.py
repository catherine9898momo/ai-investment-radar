#!/usr/bin/env python3
import datetime as dt
import email.utils
import html
import json
import os
import re
import textwrap
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "feeds.json"
DIST_DIR = ROOT / "dist"
PROGRESS_FILENAME = "value-investing-progress.json"
PROGRESS_FILE_PREFIX = "value-investing-progress"
LEGACY_OUTPUT_FILENAMES = [
    "daily-digest.md",
    "daily-digest.zh.md",
    "daily-items.json",
    "daily-concept.zh.md",
    PROGRESS_FILENAME,
]


CATEGORY_LABELS_ZH = {
    "hard_signal": "硬信号",
    "risk_signal": "风险信号",
    "ai_value_chain": "AI 价值链",
}

KEYWORD_LABELS_ZH = {
    "agent": "智能体",
    "backlog": "未交付订单",
    "capacity": "产能或容量",
    "cloud": "云服务",
    "contract": "合同",
    "cowos": "CoWoS 先进封装",
    "customer advance": "客户预付款",
    "data center": "数据中心",
    "delay": "延期",
    "enterprise ai": "企业 AI",
    "ethernet": "以太网",
    "export control": "出口管制",
    "financing": "融资",
    "gpu": "GPU",
    "hbm": "HBM 高带宽内存",
    "inference": "推理",
    "infiniband": "InfiniBand 网络",
    "inventory": "库存",
    "lease": "租赁",
    "liquid cooling": "液冷",
    "margin pressure": "利润率压力",
    "optical": "光通信",
    "order": "订单",
    "oversupply": "供给过剩",
    "packaging": "先进封装",
    "power": "电力",
    "power purchase": "电力采购协议",
    "ppa": "购电协议",
    "prepayment": "预付款",
    "production": "生产",
    "purchase agreement": "采购协议",
    "restriction": "限制",
    "shipment": "出货",
    "shortage": "短缺",
    "slowing": "放缓",
    "supply agreement": "供应协议",
    "tariff": "关税",
    "write-down": "减记",
}

TAG_LABELS_ZH = {
    "ai_infrastructure": "AI 基础设施",
    "capex": "资本开支",
    "china_ai": "中国 AI",
    "chips": "芯片",
    "cloud": "云服务",
    "data_center": "数据中心",
    "filings": "监管文件",
    "hbm": "HBM 高带宽内存",
    "nvidia": "NVIDIA",
    "packaging": "先进封装",
    "power": "电力",
    "supply_chain": "供应链",
}



VALUE_INVESTING_ROUTE_NAME = "路线 A：想学投资"
VALUE_INVESTING_ROUTE = [
    {
        "book": "The Intelligent Investor",
        "book_zh": "聪明的投资者",
        "author": "Benjamin Graham",
        "why": "先建立投资与投机、安全边际、市场先生这几个基础概念。",
    },
    {
        "book": "Common Stocks and Uncommon Profits",
        "book_zh": "怎样选择成长股",
        "author": "Philip Fisher",
        "why": "理解 Buffett 从便宜烟蒂股走向优秀公司合理价格的一半来源。",
    },
    {
        "book": "The Essays of Warren Buffett",
        "book_zh": "巴菲特致股东的信",
        "author": "Lawrence Cunningham 编",
        "why": "直接读 Buffett 对企业、资本配置、保险、会计和股东关系的系统表达。",
    },
    {
        "book": "The Outsiders",
        "book_zh": "局外人",
        "author": "William N. Thorndike Jr.",
        "why": "学习 CEO 如何用回购、并购、分红和再投资创造股东价值。",
    },
    {
        "book": "Security Analysis",
        "book_zh": "证券分析",
        "author": "Benjamin Graham, David Dodd",
        "why": "补上更专业的财报、债券、股票和估值分析训练。",
    },
    {
        "book": "Poor Charlie's Almanack",
        "book_zh": "穷查理宝典",
        "author": "Charles T. Munger / Peter Kaufman 编",
        "why": "把投资训练扩展到多元思维模型、逆向思考和误判心理学。",
    },
]

VALUE_INVESTING_CURRICULUM = [
    {
        "book": "The Intelligent Investor",
        "book_zh": "聪明的投资者",
        "author": "Benjamin Graham",
        "chapter_number": 1,
        "chapter_title": "Investment versus Speculation: Results to Be Expected by the Intelligent Investor",
        "chapter_title_zh": "投资与投机：聪明投资者可以期待什么结果",
        "main_idea": "先把自己定义成投资者，而不是被行情牵着跑的投机者。",
        "key_points": [
            {
                "point": "投资动作需要建立在分析、本金安全和合理回报这三件事上。",
                "how": "买入前写三句话：这家公司怎么赚钱；最坏情况下本金可能损失多少；合理回报来自利润增长、分红还是估值修复。",
                "check": "如果删掉行情图，只看公司和价格，你还能解释买入理由，就说明不是只在看波动。",
            },
            {
                "point": "投机不是绝对不能碰，但必须承认它是投机，并控制金额。",
                "how": "把每笔交易标成投资或投机。投机仓位单独设上限，比如不超过总资产的一个小比例。",
                "check": "如果你的理由主要是明天会涨、别人会接、消息会发酵，那就诚实地归为投机。",
            },
            {
                "point": "市场短期报价不是老师，更像每天来敲门的报价员。",
                "how": "价格大涨或大跌时，先写企业价值是否变化，再决定是否行动。",
                "check": "你能说出价格变化背后的基本面变化吗？不能，就先把它当成报价，不当成结论。",
            },
        ],
        "simple": "买股票前先问：我是在买一门生意，还是只是在赌明天有人用更高价格接走？如果说不清生意和价格，只是在猜行情。",
        "buffett_munger_link": "Buffett 继承了 Graham 的投资和投机区分；Munger 后来把重点扩展到好生意、长期复利和避免愚蠢错误。",
        "action": "今天选一个持仓或观察标的，写两栏：投资理由、投机理由。投机理由更多时，先不要加仓。",
        "question": "如果市场明天关门一年，你还愿意持有它吗？",
        "source": "Benjamin Graham《The Intelligent Investor》第 1 章；Warren Buffett 多次称这本书是投资经典。",
    },
    {
        "book": "The Intelligent Investor",
        "book_zh": "聪明的投资者",
        "author": "Benjamin Graham",
        "chapter_number": 2,
        "chapter_title": "The Investor and Inflation",
        "chapter_title_zh": "投资者与通货膨胀",
        "main_idea": "通胀会侵蚀现金购买力，但这不等于任何股票都能抗通胀。",
        "key_points": [
            {
                "point": "长期投资需要考虑购买力，而不是只看账户数字。",
                "how": "把目标收益写成实际购买力目标：预期收益率减去通胀后，还剩多少。",
                "check": "如果名义收益看起来不错，但扣除通胀后很薄，就不能把它当成高质量回报。",
            },
            {
                "point": "股票有可能抵御通胀，但前提是企业能把成本转嫁出去并保持盈利。",
                "how": "检查公司过去成本上涨时，毛利率和销量有没有明显恶化。",
                "check": "能涨价且客户不大量流失，才说明可能有定价权。",
            },
            {
                "point": "为了抗通胀而高价买入，可能把另一个风险引进来。",
                "how": "把抗通胀逻辑和买入估值分开写，先确认价格没有透支太多好消息。",
                "check": "如果只有“抗通胀”一个理由，却说不清估值安全边际，就还没通过。",
            },
        ],
        "simple": "钱放着不动也有风险，因为购买力会变弱；但为了不拿现金而乱买，也不是解决方案。",
        "buffett_munger_link": "Buffett 喜欢有定价权、轻资产、能长期产生现金的企业，这正是应对通胀时更值得看的特征。",
        "action": "找一个你关注的公司，判断它是否有提价能力：涨价后客户会留下，还是会流失？",
        "question": "这家公司面对成本上涨时，是能提价，还是只能牺牲利润率？",
        "source": "Benjamin Graham《The Intelligent Investor》第 2 章；Berkshire Hathaway 股东信中关于定价权和通胀的讨论。",
    },
    {
        "book": "The Intelligent Investor",
        "book_zh": "聪明的投资者",
        "author": "Benjamin Graham",
        "chapter_number": 3,
        "chapter_title": "A Century of Stock-Market History",
        "chapter_title_zh": "一百年股市历史",
        "main_idea": "看历史不是为了预测明天，而是为了知道市场会反复过热和过冷。",
        "key_points": [
            {
                "point": "长期回报和起始估值关系很大。",
                "how": "记录买入时的市盈率、市净率、自由现金流收益率或你采用的估值指标。",
                "check": "你能解释为什么这个起始估值仍有合理回报空间，才算过关。",
            },
            {
                "point": "市场繁荣时，投资者容易把高估值当成正常状态。",
                "how": "把当前估值放进 5 到 10 年区间里看，不只和最近一个月比。",
                "check": "如果你用“大家都这么贵”来证明合理，说明还没真正校验。",
            },
            {
                "point": "历史能提醒你：好资产在过高价格下也会带来差回报。",
                "how": "找一个好公司历史高估值买入后的回撤或多年回报，写下教训。",
                "check": "你能区分“好公司”和“好价格”，说明这个概念开始入门。",
            },
        ],
        "simple": "股市历史像温度计，告诉你现在是偏热还是偏冷；它不能告诉你明天几点降温。",
        "buffett_munger_link": "Buffett 常用历史和常识约束预期，不因为市场兴奋就提高自己愿意支付的价格。",
        "action": "给一个指数或行业看 10 年估值区间，标出现在大概处在高位、中位还是低位。",
        "question": "你现在的收益预期，是来自企业增长，还是来自估值继续变贵？",
        "source": "Benjamin Graham《The Intelligent Investor》第 3 章。",
    },
    {
        "book": "The Intelligent Investor",
        "book_zh": "聪明的投资者",
        "author": "Benjamin Graham",
        "chapter_number": 4,
        "chapter_title": "General Portfolio Policy: The Defensive Investor",
        "chapter_title_zh": "防御型投资者的组合策略",
        "main_idea": "防御型投资者的目标不是赢得每一轮行情，而是用简单规则避免大错。",
        "key_points": [
            {
                "point": "组合要和自己的时间、能力、情绪承受力匹配。",
                "how": "写下你每周能投入研究的小时数、最大可承受回撤、未来 3 年现金需求。",
                "check": "如果组合复杂度超过你的维护时间，就不匹配。",
            },
            {
                "point": "债券、现金和股票比例不是道德问题，是风险承受问题。",
                "how": "给现金和低风险资产设一个功能：生活备用、等待机会、降低波动，而不是只看收益低。",
                "check": "你能说清每类资产在组合里的任务，才不是随便配置。",
            },
            {
                "point": "规则的价值在于让你在情绪最强时仍有边界。",
                "how": "提前写好加仓、减仓和不行动条件。不要在暴涨暴跌当天发明规则。",
                "check": "行情剧烈波动时，你能照着规则复核，而不是临时拍脑袋。",
            },
        ],
        "simple": "如果你没有时间深入研究公司，就不要用需要深度研究的方式投资。",
        "buffett_munger_link": "Buffett 可以集中持有，是因为他能评估企业并承受波动；普通投资者不必模仿仓位集中度。",
        "action": "写下你属于防御型还是进取型投资者，并说明原因：时间、知识、情绪、现金需求。",
        "question": "你的组合复杂度，是否超过了你能维护的程度？",
        "source": "Benjamin Graham《The Intelligent Investor》第 4 章。",
    },
    {
        "book": "The Intelligent Investor",
        "book_zh": "聪明的投资者",
        "author": "Benjamin Graham",
        "chapter_number": 5,
        "chapter_title": "The Defensive Investor and Common Stocks",
        "chapter_title_zh": "防御型投资者与普通股",
        "main_idea": "防御型投资者可以买股票，但要用质量、分散和价格纪律保护自己。",
        "key_points": [
            {
                "point": "股票不是因为热门才值得买，而是因为企业质量和价格合适。",
                "how": "把热门理由删掉，只保留盈利、现金流、资产负债表、估值这几项事实。",
                "check": "如果删掉赛道叙事后理由仍成立，质量才可能经得住。",
            },
            {
                "point": "防御型投资者要避免过度依赖单一公司或单一主题。",
                "how": "把持仓按风险来源分类，而不是按股票数量分类。",
                "check": "如果多只股票都靠同一个变量赚钱，它们不是有效分散。",
            },
            {
                "point": "简单、可坚持的规则通常比临时判断更可靠。",
                "how": "把买入标准压缩成 5 条以内，并每次买入前逐条打勾。",
                "check": "标准太复杂以至于你不愿复查，就不能算可执行规则。",
            },
        ],
        "simple": "你不是不能买 AI 相关股票，而是要问：这家公司够稳吗？价格够合理吗？我是不是买太集中？",
        "buffett_munger_link": "Buffett 后来更强调优秀公司，但仍然保留 Graham 的价格纪律：好公司也不能无限价格买。",
        "action": "给一个持仓打三分：公司质量、估值价格、组合占比。任何一项说不清，就先不加仓。",
        "question": "你买的是企业长期现金流，还是主题热度？",
        "source": "Benjamin Graham《The Intelligent Investor》第 5 章。",
    },
    {
        "book": "The Intelligent Investor",
        "book_zh": "聪明的投资者",
        "author": "Benjamin Graham",
        "chapter_number": 6,
        "chapter_title": "Portfolio Policy for the Enterprising Investor: Negative Approach",
        "chapter_title_zh": "进取型投资者的组合策略：先排除什么",
        "main_idea": "进取不是更敢赌，而是更勤奋地排除不该碰的东西。",
        "key_points": [
            {
                "point": "高收益承诺、复杂证券、热门故事都需要更高警惕。",
                "how": "遇到看起来很诱人的机会，先写下你看不懂的部分，而不是先写上涨空间。",
                "check": "如果收益很好解释、风险很难解释，要先停下来。",
            },
            {
                "point": "先排除坏机会，比急着寻找好机会更重要。",
                "how": "建立不投清单：看不懂、负债过高、依赖融资、估值只靠故事、治理不透明。",
                "check": "每笔新机会先过不投清单，碰到一条就暂停。",
            },
            {
                "point": "进取型投资者要有更多工作量，而不是更多冲动。",
                "how": "给进取型机会设研究任务：读财报、算估值、找反方观点、写失败情景。",
                "check": "如果没有完成研究任务却想买，那是冲动，不是进取。",
            },
        ],
        "simple": "真正的进取不是看到机会就冲进去，而是先列出哪些东西坚决不碰。",
        "buffett_munger_link": "Munger 常说避免愚蠢比追求聪明更重要；这和 Graham 的负面筛选非常接近。",
        "action": "写一份你的“不投清单”：看不懂、负债太高、依赖融资、估值只靠故事等。",
        "question": "这笔投资有没有触碰你的不投清单？",
        "source": "Benjamin Graham《The Intelligent Investor》第 6 章；Charlie Munger 关于 inversion 和避免愚蠢错误的思维方式。",
    },
    {
        "book": "The Intelligent Investor",
        "book_zh": "聪明的投资者",
        "author": "Benjamin Graham",
        "chapter_number": 7,
        "chapter_title": "Portfolio Policy for the Enterprising Investor: The Positive Side",
        "chapter_title_zh": "进取型投资者的组合策略：可以寻找什么",
        "main_idea": "进取型投资者要寻找被低估、被忽视、但事实可验证的机会。",
        "key_points": [
            {
                "point": "机会通常来自市场忽视、误解或短期情绪。",
                "how": "找出市场为什么不喜欢它，再判断这个理由是暂时的还是长期的。",
                "check": "如果你不能复述反方观点，就还没有真正理解机会。",
            },
            {
                "point": "便宜本身不够，还要有资产、盈利或事件支撑。",
                "how": "列出便宜之外的证据：现金、资产、稳定盈利、回购、分红、经营改善或催化事件。",
                "check": "如果只有低 PE 或大跌，没有价值支撑，可能是价值陷阱。",
            },
            {
                "point": "进取型策略需要持续研究和耐心等待。",
                "how": "为每个机会设置跟踪指标和复查日期，而不是买完就等运气。",
                "check": "你知道接下来要观察哪三个事实变化，才算进入跟踪状态。",
            },
        ],
        "simple": "不是买跌得多的股票，而是买市场暂时没正确理解、但你能验证价值的股票。",
        "buffett_munger_link": "Buffett 早期更 Graham，找便宜货；后来叠加 Fisher/Munger，更重视好生意。",
        "action": "找一个市场不喜欢的公司，写清楚它便宜的原因，以及这个原因是否会长期存在。",
        "question": "你发现的是价格低，还是价值被低估？",
        "source": "Benjamin Graham《The Intelligent Investor》第 7 章。",
    },
    {
        "book": "The Intelligent Investor",
        "book_zh": "聪明的投资者",
        "author": "Benjamin Graham",
        "chapter_number": 8,
        "chapter_title": "The Investor and Market Fluctuations",
        "chapter_title_zh": "投资者与市场波动",
        "main_idea": "市场波动是服务你的报价，不是指挥你的命令。",
        "key_points": [
            {
                "point": "价格下跌可能是机会，也可能是风险，关键看价值是否变化。",
                "how": "下跌时重新检查收入、利润、资产负债表、竞争优势和估值假设。",
                "check": "如果价值没变而价格更低，可能是机会；如果价值变差，便宜可能是假象。",
            },
            {
                "point": "Mr. Market 的情绪每天变，投资者不必跟着变。",
                "how": "把市场报价当成可选项：接受、拒绝、继续等。每天不行动也是一种选择。",
                "check": "你能说出“不行动”的理由，就说明没有被报价牵着走。",
            },
            {
                "point": "长期投资者要利用波动，而不是被波动利用。",
                "how": "提前写好你愿意买入的价格区间和需要重新评估的坏消息清单。",
                "check": "价格到位时你能按清单行动，而不是临时被恐惧或兴奋控制。",
            },
        ],
        "simple": "市场每天给你报价。你可以接受，也可以拒绝；你没有义务因为报价变化就行动。",
        "buffett_munger_link": "Buffett 非常重视这一章，Mr. Market 是他解释市场波动时最常用的框架之一。",
        "action": "拿一个下跌或上涨的持仓，分开写：价格变了什么？企业价值变了什么？",
        "question": "这次价格变化给你的是机会、风险，还是噪音？",
        "source": "Benjamin Graham《The Intelligent Investor》第 8 章；Buffett 关于 Mr. Market 的长期引用。",
    },
    {
        "book": "The Intelligent Investor",
        "book_zh": "聪明的投资者",
        "author": "Benjamin Graham",
        "chapter_number": 20,
        "chapter_title": "Margin of Safety as the Central Concept of Investment",
        "chapter_title_zh": "安全边际：投资的核心概念",
        "main_idea": "安全边际是价值投资的刹车系统：承认自己会错，所以价格必须留余地。",
        "key_points": [
            {
                "point": "安全边际来自价格低于价值，而不是来自故事动听。",
                "how": "先给出保守内在价值，再写愿意买入价，中间差额就是你的保护。",
                "check": "如果没有估值过程，只有好故事，就没有安全边际。",
            },
            {
                "point": "越不确定，越需要更大的折价。",
                "how": "给业务稳定性、财务杠杆、行业变化打分，不确定性越高，要求折价越大。",
                "check": "高不确定公司如果只给很小折价，说明风险没有进入价格。",
            },
            {
                "point": "安全边际不能消灭风险，但能降低错误判断的伤害。",
                "how": "写一个悲观情景：利润少 20% 或估值下调后，结果还能不能接受。",
                "check": "悲观情景下仍不至于永久性大亏，安全边际才有意义。",
            },
        ],
        "simple": "你估值 100 元，不代表 98 元就该买。因为你可能估错，所以要留出一段缓冲。",
        "buffett_munger_link": "Buffett 早期深受 Graham 安全边际影响；Munger 加入后，更强调用合理价格买优秀公司。",
        "action": "给一个关注标的写出：保守价值、愿意买入价格、安全边际百分比。",
        "question": "如果你的估值错了 20%，这笔投资还有保护吗？",
        "source": "Benjamin Graham《The Intelligent Investor》第 20 章；Benjamin Graham 与 David Dodd《Security Analysis》。",
    },
    {
        "book": "Common Stocks and Uncommon Profits",
        "book_zh": "怎样选择成长股",
        "author": "Philip Fisher",
        "chapter_number": 1,
        "chapter_title": "What to Buy: The Fifteen Points to Look for in a Common Stock",
        "chapter_title_zh": "买什么：寻找普通股的十五个要点",
        "main_idea": "从只看便宜，转向研究一家公司能否长期变得更好。",
        "key_points": [
            {
                "point": "好公司需要有长期增长空间，而不是只靠一时低估。",
                "how": "写下公司未来 5 年增长来自哪里：新客户、提价、新产品、海外市场，还是行业总量扩大。",
                "check": "如果增长理由只剩下市场情绪变好，就还不是 Fisher 说的好公司研究。",
            },
            {
                "point": "管理层质量要通过行动校验，而不是只听口号。",
                "how": "看过去几年资本开支、研发、并购、回购、分红是否和管理层说法一致。",
                "check": "如果管理层说重视长期，却持续牺牲长期投入换短期利润，要打折。",
            },
            {
                "point": "研究公司时要找多方信息，不能只读公司自己的材料。",
                "how": "至少找三类外部线索：客户、供应商、竞争对手、员工评价或行业报告。",
                "check": "如果所有证据都来自公司公告，你还没有完成 Fisher 式的事实核对。",
            },
        ],
        "simple": "便宜不是唯一标准。你要问：这家公司是不是值得长期拥有，还是只是短期看起来不贵？",
        "buffett_munger_link": "Buffett 曾说自己的方法受到 Graham 和 Fisher 共同影响；Munger 也推动他更重视优秀企业的质量。",
        "action": "选一个你认为的好公司，写出 3 条长期增长证据和 2 条反方证据。",
        "question": "如果这家公司不再被市场追捧，它自身的业务还能继续变好吗？",
        "source": "Philip Fisher《Common Stocks and Uncommon Profits》；Berkshire Hathaway 2012 年股东信推荐阅读书单。",
    },
    {
        "book": "The Essays of Warren Buffett",
        "book_zh": "巴菲特致股东的信",
        "author": "Lawrence Cunningham 编",
        "chapter_number": 1,
        "chapter_title": "Owner-Related Business Principles",
        "chapter_title_zh": "股东视角下的企业原则",
        "main_idea": "把自己当成企业所有者，而不是屏幕上价格跳动的旁观者。",
        "key_points": [
            {
                "point": "买股票就是拥有企业的一部分。",
                "how": "把持仓改写成一句企业所有权描述：我拥有一家怎样赚钱的公司的一小部分。",
                "check": "如果你只能说股票代码和涨跌，说明还没有切换到所有者视角。",
            },
            {
                "point": "管理层是否对股东诚实，比短期业绩更耐看。",
                "how": "读年报里管理层如何解释错误、亏损、回购和资本开支。",
                "check": "只报喜不报忧、总把问题推给外部环境的管理层，要降低信任。",
            },
            {
                "point": "资本配置决定长期复利质量。",
                "how": "追踪公司赚到 1 元钱后怎么用：再投资、分红、回购、还债还是并购。",
                "check": "如果钱花出去后的回报越来越低，增长可能没有创造价值。",
            },
        ],
        "simple": "你不是在租一段行情，而是在买一小块企业。企业怎么赚钱、钱怎么再投资，才是重点。",
        "buffett_munger_link": "这本书直接整理 Buffett 股东信，是理解 Berkshire 思维方式的入口。",
        "action": "找一个持仓，写下它过去 3 年赚到的钱主要用到了哪里。",
        "question": "这家公司是在增加每股价值，还是只是在扩大规模？",
        "source": "Lawrence Cunningham 编《The Essays of Warren Buffett》；Berkshire Hathaway 历年股东信。",
    },
    {
        "book": "The Outsiders",
        "book_zh": "局外人",
        "author": "William N. Thorndike Jr.",
        "chapter_number": 1,
        "chapter_title": "The Outsider CEO and Capital Allocation",
        "chapter_title_zh": "局外人 CEO 与资本配置",
        "main_idea": "优秀 CEO 不只是经营业务，还要决定每一块钱留在公司还是还给股东。",
        "key_points": [
            {
                "point": "资本配置要看每股价值，不只看营收规模。",
                "how": "比较公司营收增长、利润增长和每股收益增长是否一致。",
                "check": "如果规模变大但每股价值没变好，扩张未必对股东有利。",
            },
            {
                "point": "回购只有在价格低于价值时才有意义。",
                "how": "看公司回购发生在估值低位还是高位，以及回购后股本是否真的下降。",
                "check": "高价回购、同时大量发股权激励，可能只是稀释的遮羞布。",
            },
            {
                "point": "并购要看回报，而不是新闻声量。",
                "how": "跟踪并购后投入资本回报率、商誉减值和整合成本。",
                "check": "如果并购后回报下降，说明管理层可能在买规模，不是在买价值。",
            },
        ],
        "simple": "CEO 像家庭管钱的人。赚到钱以后怎么分配，往往比赚到钱本身更能拉开差距。",
        "buffett_munger_link": "Buffett 推荐过这本书，因为它把股东价值和资本配置讲得很清楚。",
        "action": "选一家公司，查它最近三年是否回购、分红、并购或还债，并判断哪一项最影响股东价值。",
        "question": "管理层是在提高每股价值，还是在追求公司看起来更大？",
        "source": "William Thorndike《The Outsiders》；Berkshire Hathaway 2012 年股东信推荐阅读书单。",
    },
    {
        "book": "Security Analysis",
        "book_zh": "证券分析",
        "author": "Benjamin Graham, David Dodd",
        "chapter_number": 1,
        "chapter_title": "The Scope and Limitations of Security Analysis",
        "chapter_title_zh": "证券分析的范围与限制",
        "main_idea": "分析可以提高胜率，但不能消除不确定性，所以结论必须保守。",
        "key_points": [
            {
                "point": "证券分析要把事实、假设和结论分开。",
                "how": "估值表里分三栏：已发生事实、你做的假设、由此得到的估值结论。",
                "check": "如果结论变化来自假设微调，而不是事实变化，要降低信心。",
            },
            {
                "point": "资产、盈利和现金流要互相印证。",
                "how": "不要只看利润，补看现金流、债务期限、资产质量和一次性项目。",
                "check": "利润好但现金流长期跟不上，需要解释原因。",
            },
            {
                "point": "复杂分析最后仍要回到安全边际。",
                "how": "完成估值后，设定一个比估值低的买入价，而不是估到多少买到多少。",
                "check": "越复杂、越不确定的公司，买入折价应该越大。",
            },
        ],
        "simple": "分析不是为了算出一个神奇精确价格，而是为了知道大概价值区间和自己可能错在哪里。",
        "buffett_munger_link": "Buffett 在 Columbia 受 Graham 和 Dodd 训练，这本书是更专业的价值分析底座。",
        "action": "给一个标的做一页分析：事实、假设、结论、安全边际，四栏分开写。",
        "question": "你的估值结论依赖哪一个最脆弱的假设？",
        "source": "Benjamin Graham、David Dodd《Security Analysis》；Berkshire Hathaway 2012 年股东信推荐 1940 年版。",
    },
    {
        "book": "Poor Charlie's Almanack",
        "book_zh": "穷查理宝典",
        "author": "Charles T. Munger / Peter Kaufman 编",
        "chapter_number": 1,
        "chapter_title": "Worldly Wisdom and Inversion",
        "chapter_title_zh": "普世智慧与逆向思考",
        "main_idea": "先想清楚怎样会失败，再倒推怎样避免失败。",
        "key_points": [
            {
                "point": "逆向思考能逼你看见自己不愿看的风险。",
                "how": "每次买入前写一句：如果这笔投资亏很多，最可能是因为什么。",
                "check": "如果你写不出失败路径，通常不是风险低，而是你还没想够。",
            },
            {
                "point": "多元思维模型不是炫知识，是减少误判。",
                "how": "用至少三个角度检查同一家公司：激励、竞争、会计、心理偏差、周期位置。",
                "check": "如果所有角度都只是支持原观点，没有反向约束，就容易确认偏误。",
            },
            {
                "point": "避免愚蠢比追求聪明更可执行。",
                "how": "维护一张错误清单：高杠杆、看不懂、追热点、忽视估值、只听单一来源。",
                "check": "每次亏损复盘时，把错误归入清单，并更新下一次的检查项。",
            },
        ],
        "simple": "别先问怎么赚大钱，先问怎么不犯会让自己出局的错误。",
        "buffett_munger_link": "Munger 的核心贡献之一，是把投资判断从估值扩展到心理、激励和跨学科常识。",
        "action": "给一个想买的标的写一份失败预案：三个会让你承认判断错了的事实。",
        "question": "什么事实出现时，你会改变观点，而不是继续找理由？",
        "source": "Charles T. Munger / Peter Kaufman 编《Poor Charlie's Almanack》；芒格关于 inversion 和误判心理学的演讲。",
    },
]


CURRICULUM_START_DATE = dt.date.fromisoformat(os.environ.get("CURRICULUM_START_DATE", "2026-06-24"))



CATEGORIES = {
    "hard_signal": [
        "contract",
        "order",
        "backlog",
        "purchase agreement",
        "supply agreement",
        "power purchase",
        "ppa",
        "financing",
        "prepayment",
        "customer advance",
        "shipment",
        "production",
        "capacity",
        "lease",
    ],
    "risk_signal": [
        "delay",
        "cancel",
        "cut",
        "restriction",
        "export control",
        "inventory",
        "write-down",
        "shortage",
        "oversupply",
        "tariff",
        "margin pressure",
        "slowing",
    ],
    "ai_value_chain": [
        "gpu",
        "hbm",
        "cowos",
        "packaging",
        "optical",
        "ethernet",
        "infiniband",
        "liquid cooling",
        "data center",
        "power",
        "cloud",
        "inference",
        "agent",
        "enterprise ai",
    ],
}


def fetch_url(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ai-investment-radar/0.1 contact@example.com",
            "Accept": "application/rss+xml, application/atom+xml, text/xml, */*",
        },
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read()


def strip_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def parse_date(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed:
            return parsed.astimezone(dt.timezone.utc).isoformat()
    except Exception:
        pass
    return value.strip()


def child_text(element: ET.Element, names: list[str]) -> str:
    for name in names:
        found = element.find(name)
        if found is not None and found.text:
            return found.text.strip()
    return ""


def atom_link(entry: ET.Element) -> str:
    for link in entry.findall("{http://www.w3.org/2005/Atom}link"):
        href = link.attrib.get("href")
        if href:
            return href
    return ""


def parse_feed(feed_name: str, tags: list[str], data: bytes) -> list[dict]:
    root = ET.fromstring(data)
    items = []

    if root.tag.endswith("rss") or root.find("channel") is not None:
        for item in root.findall("./channel/item"):
            title = child_text(item, ["title"])
            link = child_text(item, ["link"])
            published = child_text(item, ["pubDate", "date"])
            summary = child_text(item, ["description", "summary"])
            items.append(build_item(feed_name, tags, title, link, published, summary))
        return items

    atom_ns = "{http://www.w3.org/2005/Atom}"
    for entry in root.findall(f"{atom_ns}entry"):
        title = child_text(entry, [f"{atom_ns}title"])
        link = atom_link(entry)
        published = child_text(entry, [f"{atom_ns}published", f"{atom_ns}updated"])
        summary = child_text(entry, [f"{atom_ns}summary", f"{atom_ns}content"])
        items.append(build_item(feed_name, tags, title, link, published, summary))
    return items


def score_text(text: str) -> dict:
    lower = text.lower()
    scores = {}
    for category, keywords in CATEGORIES.items():
        hits = [keyword for keyword in keywords if keyword in lower]
        scores[category] = hits
    return scores


def build_item(feed_name: str, tags: list[str], title: str, link: str, published: str, summary: str) -> dict:
    title = strip_html(title)
    summary = strip_html(summary)
    signals = score_text(f"{title} {summary}")
    return {
        "feed": feed_name,
        "tags": tags,
        "title": title,
        "link": link,
        "published": parse_date(published),
        "summary": summary[:500],
        "signals": signals,
        "signal_score": sum(len(values) for values in signals.values()),
    }


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def signal_text(item: dict, labels: dict[str, str] | None = None, empty_text: str = "no matched signal keywords") -> str:
    signal_bits = []
    for category, hits in item["signals"].items():
        if hits:
            label = labels.get(category, category) if labels else category
            signal_bits.append(f"{label}: {', '.join(hits[:5])}")
    return "; ".join(signal_bits) if signal_bits else empty_text


def markdown_item(item: dict) -> str:
    summary = textwrap.shorten(item["summary"], width=260, placeholder="...")
    return "\n".join(
        [
            f"### [{item['title']}]({item['link']})",
            f"- Feed: {item['feed']}",
            f"- Published: {item['published'] or 'unknown'}",
            f"- Tags: {', '.join(item['tags'])}",
            f"- Signals: {signal_text(item)}",
            f"- Summary: {summary}",
        ]
    )


def zh_keyword(value: str) -> str:
    return KEYWORD_LABELS_ZH.get(value, value)


def zh_tag(value: str) -> str:
    return TAG_LABELS_ZH.get(value, value)


def zh_list(values: list[str], mapper) -> str:
    labels = []
    for value in values:
        label = mapper(value)
        if any(label == existing or label in existing for existing in labels):
            continue
        labels = [existing for existing in labels if existing not in label]
        labels.append(label)
    return "、".join(labels)


def title_entities(title: str) -> list[str]:
    skip_words = {"AI", "GPU", "HBM", "CEO", "SEC", "US", "U.S", "NYSE", "NASDAQ", "NYSEARCA"}
    title_without_publisher = title.split(" - ", 1)[0]
    entities = []
    for token in re.findall(r"\b[A-Z][A-Z0-9]{1,7}\b", title_without_publisher):
        if token in skip_words or token in entities:
            continue
        entities.append(token)
    return entities[:4]


def title_entity_text(title: str) -> str:
    entities = title_entities(title)
    if not entities:
        return "标题"
    return f"标题点名{zh_list(entities, lambda value: value)}"


def title_based_summary(item: dict) -> str:
    title = item["title"]
    lower = title.lower()
    entity_text = title_entity_text(title)

    has_market_entity = bool(title_entities(title)) and any(word in lower for word in ["bet", "growth", "buy", "sell", "price", "capex"])
    if has_market_entity or any(word in lower for word in ["price prediction", "buy or sell", "stock", "stocks", "shares", "nyse", "nasdaq", "nysearca"]):
        subject = f"{entity_text}，更像" if entity_text != "标题" else "标题属于"
        return f"{subject}股票或 ETF 观点内容。它不是订单或业绩本身，适合用来观察市场在讨论哪些 AI 资本开支受益标的。"
    if "forecast" in lower and any(word in lower for word in ["capex", "capital expenditure", "capital spending"]):
        return "标题在讲 AI 资本开支预测变化。它更适合用来跟踪市场预期是否上修，而不是直接当成公司已经确认的订单。"
    if any(word in lower for word in ["estimate", "estimates", "raised", "raises"]) and any(
        word in lower for word in ["capex", "power", "data center"]
    ):
        return "标题提到预测或估算上调，方向集中在数据中心、电力或 AI 资本开支。需要回到原文确认预测来源和假设。"
    if any(word in lower for word in ["bottleneck", "crack", "toilet", "drought", "shortage", "tariff"]):
        return "标题带有风险或瓶颈线索，可能指向电力、内存、网络、政策或建设进度压力。它更像风险观察，不是正向订单信号。"
    if any(word in lower for word in ["announces", "unveils", "launches", "delivers"]):
        return "标题显示公司发布了产品、系统或项目进展。先把它当作公司动态，后续再看是否带来客户、收入或供应链订单。"
    if any(word in lower for word in ["8-k", "10-k", "10-q", "424b5", "fwp", "prospectus", "filing"]):
        return "这是监管文件或融资相关材料。阅读时要看文件事项、金额、用途和是否影响资本结构。"
    if any(word in lower for word in ["capex", "capital expenditure", "capital spending"]):
        return "标题围绕 AI 资本开支。重点不是标题本身，而是原文里有没有明确金额、建设周期、受益公司或支出方向。"
    return "标题没有给出可验证的硬信号。先作为背景材料保存，等后续出现订单、产能、融资、政策或价格变化再提高优先级。"


def title_based_focus(item: dict) -> str:
    title = item["title"].lower()
    has_market_entity = bool(title_entities(item["title"])) and any(word in title for word in ["bet", "growth", "buy", "sell", "price", "capex"])
    if has_market_entity or any(word in title for word in ["price prediction", "buy or sell", "stock", "stocks", "shares", "nyse", "nasdaq", "nysearca"]):
        return "看它讨论的是哪只股票或 ETF、受益逻辑是什么、估值假设是否依赖 AI 资本开支继续增长。"
    if "forecast" in title or "estimate" in title or "estimates" in title:
        return "看预测是谁给出的、上调了什么数字、假设条件是什么，以及有没有公司或订单层面的证据支撑。"
    if any(word in title for word in ["bottleneck", "crack", "toilet", "drought", "shortage", "tariff"]):
        return "看风险是否有量化数字、时间范围和受影响公司；没有量化时先不要把它当成确定性利空。"
    if any(word in title for word in ["announces", "unveils", "launches", "delivers"]):
        return "看发布内容是否包含客户、合同、出货、产能或收入线索；只有产品宣传时优先级较低。"
    if any(word in title for word in ["8-k", "10-k", "10-q", "424b5", "fwp", "prospectus", "filing"]):
        return "看文件类型、披露事项、金额和时间；SEC 文件通常比二手报道更适合做事实核验。"
    if "capex" in title or "capital expenditure" in title or "capital spending" in title:
        return "看资本开支对应哪个环节：芯片、封装、内存、光通信、电力还是数据中心建设。"
    return "看原文是否补充了数字、公司名、项目进度或政策细节；没有这些就只保留为背景。"


def chinese_summary(item: dict) -> str:
    signals = item["signals"]
    hard_hits = signals.get("hard_signal", [])
    risk_hits = signals.get("risk_signal", [])
    chain_hits = signals.get("ai_value_chain", [])
    tag_text = zh_list(item["tags"], zh_tag) if item["tags"] else "未标注"
    sentences = []

    if hard_hits and risk_hits:
        sentences.append(
            f"这条信息同时包含硬信号和风险信号：{zh_list(hard_hits, zh_keyword)}；风险点是{zh_list(risk_hits, zh_keyword)}。"
        )
    elif hard_hits:
        sentences.append(
            f"这条信息属于硬信号，出现了{zh_list(hard_hits, zh_keyword)}，说明它可能涉及采购、订单、产能、融资或交付安排。"
        )
    elif risk_hits:
        sentences.append(
            f"这条信息属于风险信号，出现了{zh_list(risk_hits, zh_keyword)}，需要留意成本、供给、政策或需求是否恶化。"
        )
    elif chain_hits:
        sentences.append(f"这条信息主要是产业链线索，涉及{zh_list(chain_hits, zh_keyword)}。")
    else:
        sentences.append(title_based_summary(item))

    if chain_hits:
        sentences.append(f"它影响的环节是{zh_list(chain_hits, zh_keyword)}。")
    sentences.append(f"来源归入「{item['feed']}」，标签是{tag_text}。")
    return "".join(sentences)


def chinese_focus(item: dict) -> str:
    signals = item["signals"]
    if signals.get("hard_signal"):
        return "看原文里是否有金额、客户、供应商、时间表、产能规模或交付节点；这些决定它是不是可验证的投资信号。"
    if signals.get("risk_signal"):
        return "看风险是否会影响成本、供给、交付、政策限制或下游需求，并留意是否有公司给出量化影响。"
    if signals.get("ai_value_chain"):
        return "先确认它对应 AI 产业链的哪个环节，再看后续是否出现订单、资本开支、产能或价格变化。"
    return title_based_focus(item)


def markdown_item_zh(item: dict) -> str:
    summary = textwrap.shorten(item["summary"], width=260, placeholder="...")
    published = item["published"] or "未知"
    tags = ", ".join(item["tags"])
    return "\n".join(
        [
            f"### [{item['title']}]({item['link']})",
            f"- 来源：{item['feed']}",
            f"- 发布时间：{published}",
            f"- 标签：{tags}",
            f"- 信号：{signal_text(item, CATEGORY_LABELS_ZH, '未命中信号关键词')}",
            f"- 中文摘要：{chinese_summary(item)}",
            f"- 阅读重点：{chinese_focus(item)}",
            f"- 原文摘要：{summary}",
        ]
    )


def fallback_curriculum_index(date_value: dt.date) -> int:
    days_elapsed = (date_value - CURRICULUM_START_DATE).days
    return days_elapsed % len(VALUE_INVESTING_CURRICULUM)


def concept_for_date(date_value: dt.date) -> dict:
    return VALUE_INVESTING_CURRICULUM[fallback_curriculum_index(date_value)]


def dated_filename(base: str, date_value: dt.date, suffix: str) -> str:
    return f"{base}-{date_value.isoformat()}{suffix}"


def progress_filename(date_value: dt.date) -> str:
    return dated_filename(PROGRESS_FILE_PREFIX, date_value, ".json")


def progress_path(date_value: dt.date | None = None) -> Path:
    if date_value is None:
        return DIST_DIR / PROGRESS_FILENAME
    return DIST_DIR / progress_filename(date_value)


def read_progress_file(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def latest_dated_progress_path() -> Path | None:
    candidates = sorted(DIST_DIR.glob(f"{PROGRESS_FILE_PREFIX}-*.json"), reverse=True)
    return candidates[0] if candidates else None


def load_learning_progress() -> dict:
    dated_path = latest_dated_progress_path()
    if dated_path is not None:
        progress = read_progress_file(dated_path)
        if progress:
            return progress

    legacy_path = progress_path()
    if legacy_path.exists():
        return read_progress_file(legacy_path)
    return {}


def remove_legacy_outputs() -> None:
    for filename in LEGACY_OUTPUT_FILENAMES:
        path = DIST_DIR / filename
        if path.exists():
            path.unlink()


def route_entry_for_book(book: str) -> dict:
    for entry in VALUE_INVESTING_ROUTE:
        if entry["book"] == book:
            return entry
    return {"book": book, "book_zh": book, "author": "", "why": ""}


def route_position_for_book(book: str) -> int:
    for index, entry in enumerate(VALUE_INVESTING_ROUTE, start=1):
        if entry["book"] == book:
            return index
    return len(VALUE_INVESTING_ROUTE) + 1


def lesson_position_in_book(curriculum_index: int) -> tuple[int, int]:
    book = VALUE_INVESTING_CURRICULUM[curriculum_index]["book"]
    book_indices = [
        index
        for index, lesson in enumerate(VALUE_INVESTING_CURRICULUM)
        if lesson["book"] == book
    ]
    return book_indices.index(curriculum_index) + 1, len(book_indices)


def completed_route_books(current_book: str) -> list[dict]:
    current_position = route_position_for_book(current_book)
    return VALUE_INVESTING_ROUTE[: max(current_position - 1, 0)]


def progress_round(previous_progress: dict, index: int, next_index: int) -> int:
    current_round = previous_progress.get("round", 1)
    if not isinstance(current_round, int) or current_round < 1:
        current_round = 1
    if next_index == 0 and index == len(VALUE_INVESTING_CURRICULUM) - 1:
        return current_round + 1
    return current_round


def concept_for_progress(date_value: dt.date, progress: dict) -> tuple[dict, dict]:
    date_text = date_value.isoformat()
    if progress.get("last_date") == date_text and isinstance(progress.get("current_index"), int):
        index = progress["current_index"] % len(VALUE_INVESTING_CURRICULUM)
    elif isinstance(progress.get("next_index"), int):
        index = progress["next_index"] % len(VALUE_INVESTING_CURRICULUM)
    else:
        index = fallback_curriculum_index(date_value)

    lesson = VALUE_INVESTING_CURRICULUM[index]
    next_index = (index + 1) % len(VALUE_INVESTING_CURRICULUM)
    next_lesson = VALUE_INVESTING_CURRICULUM[next_index]
    current_route_entry = route_entry_for_book(lesson["book"])
    next_route_entry = route_entry_for_book(next_lesson["book"])
    current_book_lesson, current_book_total_lessons = lesson_position_in_book(index)
    next_book_lesson, next_book_total_lessons = lesson_position_in_book(next_index)
    completed_books = completed_route_books(lesson["book"])

    next_progress = {
        "last_date": date_text,
        "round": progress_round(progress, index, next_index),
        "route_name": VALUE_INVESTING_ROUTE_NAME,
        "route_total_books": len(VALUE_INVESTING_ROUTE),
        "current_index": index,
        "current_book": lesson["book"],
        "current_book_zh": lesson["book_zh"],
        "current_book_author": current_route_entry["author"],
        "current_route_position": route_position_for_book(lesson["book"]),
        "current_book_lesson": current_book_lesson,
        "current_book_total_lessons": current_book_total_lessons,
        "current_chapter": lesson["chapter_number"],
        "current_chapter_title": lesson["chapter_title"],
        "current_chapter_title_zh": lesson["chapter_title_zh"],
        "next_index": next_index,
        "next_book": next_lesson["book"],
        "next_book_zh": next_lesson["book_zh"],
        "next_book_author": next_route_entry["author"],
        "next_route_position": route_position_for_book(next_lesson["book"]),
        "next_book_lesson": next_book_lesson,
        "next_book_total_lessons": next_book_total_lessons,
        "next_chapter": next_lesson["chapter_number"],
        "next_chapter_title": next_lesson["chapter_title"],
        "next_chapter_title_zh": next_lesson["chapter_title_zh"],
        "completed_books": [entry["book"] for entry in completed_books],
        "completed_books_zh": [entry["book_zh"] for entry in completed_books],
    }
    return lesson, next_progress


def write_learning_progress(progress: dict) -> None:
    date_value = dt.date.fromisoformat(progress["last_date"])
    progress_path(date_value).write_text(json.dumps(progress, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_execution_points(points: list[dict]) -> str:
    blocks = []
    for index, point in enumerate(points, start=1):
        blocks.extend(
            [
                f"### {index}. {point['point']}",
                "",
                f"- 怎么做：{point['how']}",
                f"- 怎么检查：{point['check']}",
                "",
            ]
        )
    return "\n".join(blocks).strip()


def render_daily_concept(date_value: dt.date, lesson: dict | None = None, progress: dict | None = None) -> str:
    lesson = lesson or concept_for_date(date_value)
    progress = progress or {}
    key_points = "\n".join(f"- {point['point']}" for point in lesson["key_points"])
    execution_points = render_execution_points(lesson["key_points"])
    lines = [
        f"# 每日价值投资课程 - {date_value.isoformat()}",
        "",
        "## 学习路线",
        "",
        f"路线：{progress.get('route_name', VALUE_INVESTING_ROUTE_NAME)}",
        f"当前书：第 {progress.get('current_route_position', route_position_for_book(lesson['book']))}/{len(VALUE_INVESTING_ROUTE)} 本，{lesson['book_zh']}",
        f"当前进度：本书第 {progress.get('current_book_lesson', lesson_position_in_book(VALUE_INVESTING_CURRICULUM.index(lesson))[0])}/{progress.get('current_book_total_lessons', lesson_position_in_book(VALUE_INVESTING_CURRICULUM.index(lesson))[1])} 条",
        f"下一条：{progress.get('next_book_zh', lesson['book_zh'])}，第 {progress.get('next_chapter', lesson['chapter_number'])} 章/节",
        "",
        "## 今日章节",
        "",
        f"《{lesson['book']}》（{lesson['book_zh']}）",
        f"作者：{lesson['author']}",
        f"章节：第 {lesson['chapter_number']} 章，{lesson['chapter_title_zh']}",
        f"原章名：{lesson['chapter_title']}",
        "",
        "## 学习主线",
        "",
        lesson["main_idea"],
        "",
        "## 本章要点",
        "",
        key_points,
        "",
        "## 执行要点",
        "",
        execution_points,
        "",
        "## 简单理解",
        "",
        lesson["simple"],
        "",
        "## 和 Buffett/Munger 的关系",
        "",
        lesson["buffett_munger_link"],
        "",
        "## 今天可以做",
        "",
        lesson["action"],
        "",
        "## 检查问题",
        "",
        lesson["question"],
        "",
        "## 参考来源",
        "",
        lesson["source"],
        "",
        "这不是投资建议。它是一条按书和章节推进的价值投资学习练习。",
    ]
    return "\n".join(lines)


def write_daily_concept(date_value: dt.date) -> None:
    progress = load_learning_progress()
    lesson, next_progress = concept_for_progress(date_value, progress)
    (DIST_DIR / dated_filename("daily-concept", date_value, ".zh.md")).write_text(
        render_daily_concept(date_value, lesson, next_progress), encoding="utf-8"
    )
    write_learning_progress(next_progress)
    remove_legacy_outputs()


def write_outputs(items: list[dict], errors: list[dict]) -> None:
    DIST_DIR.mkdir(exist_ok=True)
    today_date = dt.datetime.now(dt.timezone.utc).date()
    today = today_date.strftime("%Y-%m-%d")
    lookback_days = int(os.environ.get("LOOKBACK_DAYS", "14"))
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=lookback_days)
    recent_items = [item for item in items if is_recent(item.get("published", ""), cutoff)]
    sorted_items = sorted(recent_items, key=lambda item: item["signal_score"], reverse=True)

    digest_lines = [
        f"# AI Investment Radar - {today}",
        "",
        f"Lookback window: {lookback_days} days",
        f"Items fetched: {len(items)}",
        f"Items in window: {len(sorted_items)}",
        "",
        "## Top Signal Items",
        "",
    ]
    zh_digest_lines = [
        f"# AI 投资雷达 - {today}",
        "",
        f"回看窗口：{lookback_days} 天",
        f"抓取条目：{len(items)}",
        f"窗口内条目：{len(sorted_items)}",
        "",
        "## 重点信号条目",
        "",
    ]
    for item in sorted_items[:30]:
        digest_lines.append(markdown_item(item))
        digest_lines.append("")
        zh_digest_lines.append(markdown_item_zh(item))
        zh_digest_lines.append("")

    if errors:
        digest_lines.extend(["## Fetch Errors", ""])
        zh_digest_lines.extend(["## 抓取错误", ""])
        for error in errors:
            digest_lines.append(f"- {error['feed']}: {error['error']}")
            zh_digest_lines.append(f"- {error['feed']}：{error['error']}")

    (DIST_DIR / dated_filename("daily-digest", today_date, ".md")).write_text("\n".join(digest_lines), encoding="utf-8")
    (DIST_DIR / dated_filename("daily-digest", today_date, ".zh.md")).write_text("\n".join(zh_digest_lines), encoding="utf-8")
    write_daily_concept(today_date)
    (DIST_DIR / dated_filename("daily-items", today_date, ".json")).write_text(
        json.dumps(
            {"items": sorted_items, "errors": errors, "lookback_days": lookback_days},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def is_recent(value: str, cutoff: dt.datetime) -> bool:
    if not value:
        return True
    try:
        parsed = dt.datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed >= cutoff
    except Exception:
        return True


def main() -> None:
    config = load_config()
    items = []
    errors = []
    for feed in config["feeds"]:
        try:
            data = fetch_url(feed["url"])
            items.extend(parse_feed(feed["name"], feed.get("tags", []), data))
        except Exception as exc:
            errors.append({"feed": feed["name"], "url": feed["url"], "error": str(exc)})
    write_outputs(items, errors)
    print(f"Wrote {len(items)} items with {len(errors)} errors to {DIST_DIR}")


if __name__ == "__main__":
    main()

