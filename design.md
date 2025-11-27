# 批量域名生成与注册查询工具 – 设计文档（design.md）

## 1. 项目简介

**项目名称**：`domain-batch-tool`  
**运行环境**：Ubuntu Server (推荐 20.04 / 22.04 + Python 3.10+)  

本项目实现一个在 Ubuntu 服务器上运行的 **批量域名生成 + 批量注册状态查询** 的工具，分为两大部分：

1. **域名生成器（Generator）**：  
   根据配置批量生成候选域名，支持多种组合规则（字母、数字、拼音、声母/韵母、邮编区号、城市简写、豹子/顺子等）。
2. **域名查询器（Checker）**：  
   对生成的域名进行是否已注册 / 可注册的查询，支持并发、断点续查以及多种输出格式。

提供统一的命令行工具，方便在服务器上脚本化调用和自动化任务集成。

---

## 2. 功能需求

### 2.1 总体流程

典型使用场景：

1. 用户配置要生成的 **域名后缀**（如 `.com`, `.cn`, `.net` 等）。
2. 用户选择一种或多种 **生成规则**（字母组合、数字组合、拼音组合、豹子、顺子等）。
3. 工具批量生成域名，并：
   - 直接写入文件，供其他工具使用；或
   - 直接流式传给查询器，边生成边查询。
4. 查询器并发查询域名是否已经注册，输出结果（CSV / JSON / 纯文本），并支持中断后继续。

支持三种主要模式：

- `generate-only`：只生成，不查询。
- `check-only`：只查询（读取已有域名列表）。
- `pipeline`：生成 + 查询 一条龙，流式处理。

---

### 2.2 域名生成器需求

#### 2.2.1 基本要求

- 可配置 **域名后缀** 列表（`tlds`），例如：`.com`, `.net`, `.cn`, `.xyz`。
- 可配置 **生成规则组合**，可同时开启多种生成方式。
- 支持输出：
  - 标准输出（stdout）
  - 文件输出（如：`domains.txt`）
- 支持去重与过滤（黑名单，长度限制，字符集限制等）。
- 控制生成数量：
  - 可设置最大生成数量 `--max-count`
  - 可设置起始/结束范围（比如数字从 `1000` 到 `9999`）。

#### 2.2.2 支持的生成类型（完善后的列表）

下面每一项都设计为一个“生成器插件”，可单独启用或组合启用。

1. **字母组合（letters）**
   - 小写字母：`a-z`
   - 可选大写：`A-Z`
   - 可配置长度范围：`--letters-len 2-4`（表示 2~4 位）
   - 可配置是否允许混合大小写。

2. **数字组合（digits）**
   - 数字：`0-9`
   - 可配置长度范围：`--digits-len 2-6`

3. **数字（无 04）（digits-no04）**
   - 在数字组合的基础上增加限制：
     - 不包含连续子串 `"04"`，或
     - 可选配置为不包含字符 `'0'` 和 `'4'`（通过配置项控制）。
   - 可配置：`--digits-no04-mode substring|exclude-chars`。

4. **声母（initials）**
   - 使用常见汉语拼音声母表，如：`b p m f d t n l g k h j q x zh ch sh r z c s y w`。
   - 支持：
     - 单个声母：`b.com`
     - 声母+韵母组合模式由拼音类生成器处理（见后面）。

5. **韵母（finals）**
   - 常用韵母表，如：`a o e i u ü ai ei ao ou an en ang eng ong ia ...`。
   - 本身可作为独立组合，也可在拼音组合中使用。

6. **常见单词（common-words）**
   - 从词库中读取，例如：
     - 高频英文单词：`good`, `best`, `top`, `vip`, `shop`, `cloud`...
   - 支持按词性细分（通过不同词库）：

7. **名词 / 动词 / 形容词（nouns / verbs / adjectives）**
   - 设计为三类词库：
     - `nouns.txt`
     - `verbs.txt`
     - `adjectives.txt`
   - 可以选择只用某一种或几种：  
     `--use-nouns --use-verbs --use-adjectives`

8. **邮编（zip-codes）**
   - 例如中国邮政编码（6 位数字），数据来自 `zipcodes_cn.txt`。
   - 可选择指定国家的邮编词库。

9. **区号（area-codes）**
   - 常见电话区号，如 `010`（北京）、`021`（上海）。
   - 从 `area_codes.txt` 加载。

10. **拼音长度组合（pinyin-2, pinyin-3-4, pinyin-5-6）**
    - 使用一个全量/常用汉字拼音词库：
      - 2 位拼音：如 `ba`, `he`, `li`。
      - 3-4 位拼音片段：如 `bei`, `shang`, `shou`。
      - 5-6 位拼音：如 `beiji`, `shanghai` 的片段等。
    - 生成策略：
      - 直接从词库中读出。
      - 或根据声母+韵母组合规则合成。

11. **城市名称 / 城市拼音（cities, city-pinyin）**
    - 数据文件：
      - `cities_cn.txt`：中文城市名
      - `cities_pinyin.txt`：对应拼音，不带声调。
    - 生成模式：
      - 完整拼音：`beijing.com`
      - 城市名+后缀拼接：`beijingvip.com`（可作为扩展）

12. **汉字拼音（hanzi-pinyin）**
    - 从「常用汉字表」中抽取拼音（不含声调）。
    - 生成规则：
      - 单字拼音：`li.com`
      - 多字拼音连写：`wangwei.com`（可配置最大字数）。

13. **双拼（shuangpin）**
    - 支持某种双拼方案（如自然码、小鹤等），从配置中选择。
    - 将汉字拼音映射为双拼码：如 “你(n i)” → “ni” 的双拼形式。
    - 用于生成短域名：`ni`, `wo`, `ta` 等的双拼变化。

14. **城市简写（city-abbr）**
    - 例如：北京 → `bj`，上海 → `sh`，广州 → `gz` 等。
    - 数据文件：`city_abbr.txt`

15. **省份简写（province-abbr）**
    - 如：`bj`（北京）、`sd`（山东）、`gd`（广东）。
    - 数据文件：`province_abbr.txt`

16. **豹子（2-6位豹子，repeat-pattern）**
    - 2~6 位同一字符重复：
      - 例如：`aa`, `bbb`, `8888`, `zzzzz`。
    - 字符集合可配置：
      - 默认数字 `0-9`
      - 或字母 `a-z`/`A-Z`
      - 或自定义字符集合。

17. **顺子（3-6位数字顺子，sequence-pattern）**
    - 数字递增或递减序列：
      - 升序：`123`, `4567`, `6789`
      - 降序（可选）：`321`, `9876`
    - 可配置是否允许循环顺子（如 `7890`）。

18. **A/B 模式串（pattern-AB）**
    - 用户提到的模式，例如：
      - `A`  
      - `AA`  
      - `AB`  
      - `AAA`  
      - `AAB`  
      - `ABB`  
      - `ABA`  
      - `AAAA`  
      - `ABAB`  
      - `AABB`  
      - `AAAB`  
      - `ABBB`  
      - `ABAA`  
      - `AABA`  
      - ...  
    - 设计思路：
      - **A/B** 本质上是“占位符组”：
        - A、B 各自绑定一个字符集（如 A=数字，B=字母；或者 A=字母，B=字母）。
      - 同一个字母代表同一个字符：
        - 模式 `AAB`：  
          - 第1位 = 第2位  
          - 第3位 ≠ 第1位  
        - 模式 `ABAB`：  
          - 第1位 = 第3位  
          - 第2位 = 第4位  
          - 且 A≠B
      - 用户在命令行中指定：
        - `--pattern AB,ABA,AABB`  
        - `--set A=digits --set B=letters-lower`
      - 工具根据模式及字符集生成对应所有组合。

#### 2.2.3 组合与过滤规则

- 可以组合多个生成器：
  - 例如：`城市简写 + 2位数字` → `bj88.com`, `sh01.com`。
  - 例如：`拼音 + 数字豹子` → `li888.com`
- 提供统一的过滤器链：
  - 长度过滤：`min_len`, `max_len`
  - 字符过滤：只允许 `[a-z0-9-]`
  - 禁用某些前缀/后缀/子串（比如 `test`, `demo` 等）。
- 去重：
  - 相同域名只能出现一次（使用 `set` 或外部缓存）。

---

### 2.3 域名查询器需求

#### 2.3.1 查询目标

- 判断域名是否 **已注册** / **未注册（可能可注册）**。
- 输出结果包括：
  - 域名
  - 状态：`registered` / `available` / `unknown`
  - 查询方式：`whois` / `dns` / `http`
  - 备注信息（如 WHOIS 返回的 registrar 信息、过期时间等）。

> 说明：  
> - 严格意义上的“是否可注册”取决于具体注册商和注册规则，本工具只能基于 WHOIS/DNS 做高概率判断，结果需用户自行复核。

#### 2.3.2 查询方式（可插拔）

1. **WHOIS 查询（默认严格模式）**
   - 调用系统 `whois` 命令，或使用 Python 的 `whois` 库。
   - 解析返回文本中的关键字：
     - 如 “No match for domain”、“NOT FOUND”、“Status: free”等。
   - 按 TLD 适配不同的判定规则（通过配置文件 `tlds.yaml`）。

2. **DNS 查询（快速模式）**
   - 使用 `dig` / `dns.resolver` 查询 A/NS 记录：
     - 有记录：大概率已注册。
     - 无记录：不一定未注册（可能没解析）。
   - 可作为快速预过滤器，减少 WHOIS 调用。

3. **HTTP 检查（可选）**
   - 对 `http://domain` 或 `https://domain` 发起 HEAD/GET：
     - 能连接：大概率已注册并解析。
     - 连接失败：不代表未注册。

4. **多 Backends 支持**
   - 采用策略模式：
     - `WhoisChecker`
     - `DnsChecker`
     - `HttpChecker`
   - 可配置查询链：例如先 DNS，再 WHOIS，减少负载与封禁风险。

#### 2.3.3 并发与性能

- 使用异步 IO 或线程池：
  - Python `asyncio` + `aiohttp`（用于 HTTP）
  - `concurrent.futures.ThreadPoolExecutor`（用于调用阻塞的 `whois` / `dig` 命令）。
- 可配置并发度：`--concurrency N`
- 失败重试：
  - 网络错误 / 超时可重试 `N` 次。
- Rate limiting（节流）：
  - 防止对同一 whois 服务器请求过快被封锁。
  - 简单实现：对每个 TLD 的查询间隔控制。

#### 2.3.4 输出与存储

- 输出格式：
  - `--format text`：`domain status`
  - `--format csv`：`domain,status,extra`
  - `--format json`：每行一个 JSON 对象。
- 结果写入：
  - 标准输出（默认）
  - 文件：`--output result.csv`
  - （可选扩展）SQLite 数据库，支持后续统计分析。

#### 2.3.5 断点续查 & 缓存

- 支持生成过程中记录已查询域名：
  - 查询前看缓存：
    - 如果已查过，直接使用缓存结果。
- 缓存实现：
  - 简易：本地 CSV/JSON 文件 + 内存 set。
  - 高级：本地 SQLite / LevelDB。
- 支持 `--resume` 参数：
  - 从上次结果文件继续，对未查询的行进行查询。

---

### 2.4 命令行接口设计（CLI）

采用单一可执行入口（例如 `domain-tool`），使用子命令：

#### 2.4.1 示例命令

1. **只生成域名：**

```bash
domain-tool generate \
  --tlds .com,.net \
  --letters-len 3 \
  --digits-no04-len 2 \
  --pattern-AB AAA,AAB \
  --set A=digits --set B=letters-lower \
  --output domains.txt \
  --max-count 100000
```

2. **只查询现有域名列表：**

```bash
domain-tool check \
  --input domains.txt \
  --checker whois,dns \
  --concurrency 50 \
  --format csv \
  --output result.csv
```

3. **生成 + 查询流水线：**

```bash
domain-tool pipeline \
  --tlds .com \
  --city-abbr \
  --digits-len 2 \
  --checker whois \
  --concurrency 20 \
  --format csv \
  --output result.csv
```

#### 2.4.2 常用参数概览

- 通用：
  - `--tlds`：域名后缀列表
  - `--max-count`：最大生成数量
  - `--min-len` / `--max-len`：域名主体长度限制（不含后缀）
- 生成相关：
  - `--letters-len`
  - `--digits-len`
  - `--digits-no04-len`
  - `--use-nouns` / `--use-verbs` / `--use-adjectives`
  - `--zip-codes`
  - `--area-codes`
  - `--pinyin-2` / `--pinyin-3-4` / `--pinyin-5-6`
  - `--city-pinyin` / `--city-abbr` / `--province-abbr`
  - `--repeat-len 2-6`（豹子）
  - `--sequence-len 3-6`（顺子）
  - `--pattern-AB` + `--set A=... --set B=...`
- 查询相关：
  - `--checker whois,dns,http`
  - `--concurrency`
  - `--timeout`
  - `--retry`
  - `--resume`
  - `--cache-file`

---

## 3. 非功能需求

### 3.1 可维护性与扩展性

- 每个生成规则、查询方式都以“插件（class)”形式存在，便于后续增加新规则。
- 使用配置文件（`config/default.yaml`）管理：
  - TLD 对应的 WHOIS 解析规则。
  - 词库路径。
  - 默认并发数、超时等。

### 3.2 兼容性

- 在 Ubuntu Server 上通过：
  - `python3 -m venv venv`
  - 安装依赖后运行。
- 对于 `whois` / `dig` 等命令，需在文档中说明：
  - 需要 `sudo apt install whois dnsutils`。

### 3.3 性能与规模

- 面向几十万到数百万级别的域名查询量：
  - 通过流水线 + 并发 + 缓存提高效率。
- 建议提供简单的进度显示（如每 N 条日志输出一次）。

### 3.4 日志与监控

- 标准日志输出到 stderr：
  - INFO：流程信息
  - WARNING：网络异常、重试信息
  - ERROR：无法恢复的错误
- 可选：支持 `--log-file` 写入文件。

---

## 4. 系统设计与模块划分

### 4.1 技术栈

- 语言：**Python 3.10+**
- CLI 框架：`click` 或 `typer`
- DNS：`dnspython` 或 调用系统 `dig`
- WHOIS：
  - 调用系统 `whois` 命令，或
  - `python-whois` 类库（视实际情况选用）
- 并发：`asyncio` + `aiohttp` / `ThreadPoolExecutor`

### 4.2 目录结构（建议）

```text
domain-batch-tool/
  ├── domain_tool/
  │   ├── __init__.py
  │   ├── cli.py                 # 命令行入口
  │   ├── generator/             # 各类生成器
  │   │   ├── __init__.py
  │   │   ├── base.py
  │   │   ├── letters.py
  │   │   ├── digits.py
  │   │   ├── digits_no04.py
  │   │   ├── pinyin.py
  │   │   ├── wordlist.py
  │   │   ├── pattern_ab.py
  │   │   ├── repeat.py          # 豹子
  │   │   ├── sequence.py        # 顺子
  │   │   ├── city.py
  │   │   └── province.py
  │   ├── checker/               # 查询器
  │   │   ├── __init__.py
  │   │   ├── base.py
  │   │   ├── whois_checker.py
  │   │   ├── dns_checker.py
  │   │   └── http_checker.py
  │   ├── filters/
  │   │   ├── __init__.py
  │   │   ├── base.py
  │   │   ├── length_filter.py
  │   │   ├── charset_filter.py
  │   │   └── blacklist_filter.py
  │   ├── pipeline.py            # 生成 + 查询流水线
  │   ├── config.py              # 加载配置文件
  │   └── utils.py               # 公共工具函数
  ├── wordlists/                 # 词库
  │   ├── initials_zh.txt
  │   ├── finals_zh.txt
  │   ├── nouns.txt
  │   ├── verbs.txt
  │   ├── adjectives.txt
  │   ├── zipcodes_cn.txt
  │   ├── area_codes_cn.txt
  │   ├── cities_cn.txt
  │   ├── cities_pinyin.txt
  │   ├── city_abbr.txt
  │   └── province_abbr.txt
  ├── config/
  │   ├── default.yaml           # 默认配置
  │   └── tlds.yaml              # 各 TLD 的 WHOIS 规则
  ├── README.md
  └── design.md                  # 本设计文档
```

### 4.3 核心类与接口（概要）

#### 4.3.1 生成器基类

```python
class BaseGenerator:
    def __init__(self, config):
        self.config = config

    def generate(self):
        """
        返回一个迭代器/生成器，逐个产出不带后缀的域名主体字符串。
        """
        raise NotImplementedError
```

所有具体生成器，如 `LettersGenerator`, `DigitsGenerator`, `PatternABGenerator` 都继承该基类。

#### 4.3.2 查询器基类

```python
class BaseChecker:
    def __init__(self, config):
        self.config = config

    def check(self, domain: str) -> dict:
        """
        输入完整域名，返回结构化结果：
        {
          "domain": domain,
          "status": "registered|available|unknown",
          "backend": "whois|dns|http",
          "extra": { ... }
        }
        """
        raise NotImplementedError
```

多个 Checker 可以被组合成链式调用。

#### 4.3.3 流水线控制

```python
class Pipeline:
    def __init__(self, generators, checkers, filters, config):
        ...

    async def run(self):
        """
        负责调度：
        1. 从 generators 中拿域名主体
        2. 加上 TLD 形成完整域名
        3. 过滤
        4. 并发调用 checkers
        5. 输出结果
        """
```

---

## 5. 典型流程示例（逻辑）

以“城市简写 + 2 位数字（无 04） + .com”为例：

1. 从 `city_abbr.txt` 读取城市简写，如 `bj`, `sh`, `gz`。
2. 数字生成器生成所有 2 位数字：`00-99`。
3. `digits-no04` 过滤 `04`（如 `04`, `14`, `40` 等）视配置规则剔除。
4. 笛卡尔积组合：`bj00`, `bj01`, ..., `sh00`, ...。
5. 加上后缀 `.com` → `bj00.com`。
6. 送入查询器（DNS → WHOIS）：
   - DNS 无记录 → 进一步 WHOIS；
   - WHOIS 返回 “NOT FOUND” → 标记为 `available`。
7. 结果写入 `result.csv`。

---

## 6. 后续扩展方向

- 增加更多语言的词库（英文名、人名、品牌词等）。
- 接入具体注册商 API（如某些 Registrar 提供的可用性查询接口），提高准确度与速度。
- 提供 Web 管理界面（单独服务），调用本工具作为后端。
- 增加统计分析功能，例如：
  - 各类型组合的可用率
  - 不同 TLD 的注册情况对比

---

如果你愿意，下一步我可以按照这个设计，从目录结构和 `cli.py` 开始，逐步把可运行的原型代码写出来（包括基础生成器和一个简单的 WHOIS 查询器）。
