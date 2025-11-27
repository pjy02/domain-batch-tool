# domain-batch-tool

批量生成域名并检测是否已被注册的命令行工具。设计细节请参见 `design.md`。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 使用默认配置运行生成+查询流水线
python -m domain_batch_tool.cli --config config/default.yaml

# 仅生成域名主体
python -m domain_batch_tool.cli generate --config config/default.yaml --max-count 10

# 对已有域名列表执行查询
python -m domain_batch_tool.cli check domains.txt --config config/default.yaml
```

默认配置会使用字母生成器（2~3 位）并为每个生成的 label 加上 `.com/.net/.cn` 后缀，然后通过 DNS 检测是否已有解析记录。

## 配置

- `config/default.yaml`：主配置文件，包含模式（generate / check / pipeline）、输出格式、并发度、生成器、过滤器和检查器的开关。
- `config/tlds.yaml`：WHOIS 解析模板占位文件，可按需扩展。

## 功能概览

- 可插拔生成器：字母、数字、数字无 04、词库等，可通过配置自由组合（笛卡尔积拼接）。
- 过滤器：长度、字符集、黑名单。
- 检查器：DNS（内置），WHOIS（占位，可按需实现）。
- 并发执行与输出格式化（text / csv / json）。

更多设计规划请阅读 `design.md`，项目现有能力概览见 `ANALYSIS.md`。
