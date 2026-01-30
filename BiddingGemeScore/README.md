# 需求优先级打分与资源分配系统

本系统根据《FY25系统功能使用考核-节奏拉齐》规则进行需求优先级计算和资源分配。

## ✨ 主要功能

- **优先级打分**：基于需求分类、季度计划、启动状态自动计算权重。
- **资源分配**：支持 "考研/四六级/专升本" 动态配额分配与回流机制。
- **轻学特殊规则**：轻学需求优先排期，月度/季度封顶保护。
- **X类需求识别**：系统故障/阻断性问题自动标记为"X类"，不占分但最高优先级。
- **可视化报告**：生成 **Ant Design 风格** 的 HTML 报告，支持莫兰迪配色与企业级图表展示。

## 🚀 快速开始

### 1. 准备数据
请参考 `requirements_template.csv` 填写需求数据。
- **核心字段**：所属业务团队、需求标题、业务需求优先级、规划属性、紧迫度、启动状态。

### 2. 运行脚本
使用以下命令生成分析报告：

```bash
# 生成 Ant Design 风格的 HTML 报告
python3 requirement_scorer.py --input requirements_template.csv --total-score 150 --html --output output/report.html
```

**参数说明**：
- `-i, --input`: 输入文件路径 (CSV/JSON)，默认 `requirements_template_new_v2.csv` (也可使用 `requirements_template.csv`)
- `-t, --total-score`: **[必填]** 可用总分池 (例如 150)
- `-o, --output`: 输出文件路径
- `--html`: 启用 HTML 报告生成

### 3. 查看报告
生成的报告将位于 `output/` 目录下（例如 `output/report.html`）。请使用浏览器打开以获得最佳浏览体验。

## 📊 报告界面
报告采用 **Ant Design** 企业级设计规范：
- **Geek Blue** 主色调
- **8px** 网格系统布局
- 清晰的配额分配概览与进度条
- 智能标记 "真/伪" 需求与决策结果
