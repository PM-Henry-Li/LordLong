# HTML报告使用说明

## 功能特点

HTML报告提供了美观的网页界面展示，包含：

- ✅ **现代化设计**：渐变背景、卡片式布局、响应式设计
- ✅ **统计概览**：直观的数据卡片展示
- ✅ **进度条可视化**：资源使用情况一目了然
- ✅ **表格交互**：悬停高亮、清晰的分组
- ✅ **颜色标识**：入选/待办状态用不同颜色区分
- ✅ **打印友好**：支持打印输出

## 使用方法

### 生成HTML报告

```bash
# 基本用法
python3 requirement_scorer.py -i requirements_template_new.csv -t 150 -o output/report.html --html

# 自动检测文件格式
python3 requirement_scorer.py -i requirements.csv -t 150 --html

# 指定JSON文件
python3 requirement_scorer.py -i requirements.json -t 1000 -o output/report.html --html
```

### 查看报告

生成HTML报告后，可以通过以下方式查看：

1. **直接在浏览器中打开**
   ```bash
   # macOS
   open output/report.html
   
   # Linux
   xdg-open output/report.html
   
   # Windows
   start output/report.html
   ```

2. **复制文件路径到浏览器**
   - 脚本运行后会显示文件路径，如：`file:///Users/henry/Documents/LordLong/BiddingGemeScore/output/report.html`
   - 复制到浏览器地址栏即可打开

3. **拖拽文件到浏览器**
   - 直接将HTML文件拖拽到浏览器窗口

## 报告内容

### 1. 统计概览卡片

显示四个关键指标：
- 总需求数
- 入选需求数
- 待办需求数
- X类需求数

### 2. 配额分配概览

表格展示各业务线的：
- 初始比例
- 是否触发回流（带颜色标识）
- 最终可用配额

### 3. X类紧急通道

红色高亮显示系统故障/阻断性问题需求

### 4. 最终排期决策表

详细的需求列表，包含：
- 优先级排序
- 业务线标识（紫色高亮）
- 需求名称
- A/B/C得分
- 原始得分和分配得分
- 决策结果（绿色=入选，橙色=待办）

### 5. 分析总结

- **资源使用情况**：带进度条的可视化展示
- **高优待办需求建议**：按得分排序的前3个待办需求

## 样式说明

### 颜色标识

- **绿色** (`✓ 入选`)：需求已入选，将执行
- **橙色** (`⏸ 待办`)：需求待办，超出配额
- **紫色**：业务线名称和得分高亮
- **红色**：X类紧急需求

### 进度条

资源使用情况通过进度条直观展示：
- 进度条长度 = 使用率百分比
- 渐变紫色填充

## 浏览器兼容性

- ✅ Chrome/Edge（推荐）
- ✅ Firefox
- ✅ Safari
- ✅ 移动端浏览器

## 打印支持

HTML报告支持打印，打印时会自动优化样式：
- 移除背景渐变
- 优化表格布局
- 保持所有数据完整

## 示例

```bash
# 生成HTML报告
python3 requirement_scorer.py -i requirements_template_new.csv -t 150 -o output/report.html --html

# 输出：
# HTML报告已生成: output/report.html
# 请在浏览器中打开查看: file:///Users/henry/Documents/LordLong/BiddingGemeScore/output/report.html
```

## 注意事项

1. HTML报告是独立的单文件，包含所有样式和数据
2. 可以直接分享HTML文件给团队成员查看
3. 不需要服务器，本地文件即可在浏览器中打开
4. 建议使用现代浏览器以获得最佳显示效果
