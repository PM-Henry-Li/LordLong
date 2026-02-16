# 异步并行图片生成使用指南

## 概述

异步并行图片生成功能通过 `asyncio` 和 `aiohttp` 实现，可以显著提升图片生成效率，性能提升约 60%。

## 快速开始

### 基本用法

```bash
# 使用异步并行模式（默认3并发）
python run.py --image-mode api --async-mode

# 指定并发数
python run.py --image-mode api --async-mode --max-concurrent 5

# 完整示例
python run.py --mode file --image-mode api --async-mode --max-concurrent 3
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--async-mode` | 启用异步并行模式 | 关闭 |
| `--max-concurrent` | 最大并发数 | 3 |
| `--image-mode` | 图片生成模式（api/template） | template |

## 性能对比

### 串行模式（原有方式）

```bash
python run.py --image-mode api
```

- 5张图片：约 5分钟
- 10张图片：约 10分钟

### 异步并行模式（新方式）

```bash
python run.py --image-mode api --async-mode --max-concurrent 3
```

- 5张图片：约 2分钟（提升 60%）
- 10张图片：约 4分钟（提升 60%）

## 并发数选择

### 推荐配置

| 场景 | 并发数 | 说明 |
|------|--------|------|
| 保守 | 1-2 | API配额有限，追求稳定 |
| 推荐 | 3 | 平衡性能和稳定性 |
| 激进 | 4-5 | API配额充足，追求速度 |

### 注意事项

1. **API限流**：阿里云API有速率限制，过高并发可能触发限流
2. **网络稳定性**：并发越高，对网络稳定性要求越高
3. **内存占用**：并发会增加内存使用

## 使用场景

### 场景1：日常内容生成

```bash
# 使用默认配置（3并发）
python run.py --mode file --image-mode api --async-mode
```

适合：
- 日常内容生成
- 网络条件良好
- API配额充足

### 场景2：批量生成

```bash
# 提高并发数加速批量生成
python run.py --mode topic --topic "老北京文化" --image-mode api --async-mode --max-concurrent 5
```

适合：
- 批量生成大量内容
- 时间紧迫
- API配额充足

### 场景3：保守模式

```bash
# 降低并发数确保稳定
python run.py --image-mode api --async-mode --max-concurrent 1
```

适合：
- API配额有限
- 网络不稳定
- 追求稳定性

## 错误处理

### 自动重试

异步模式内置智能重试机制：
- 最多重试 3 次
- 内容审核失败会自动简化提示词
- 网络错误会自动等待后重试

### 错误隔离

单张图片失败不影响其他图片：
- 失败的图片会记录错误信息
- 成功的图片正常保存
- 最后显示统计信息

### 示例输出

```
✅ 封面 生成成功
✅ 图1 生成成功
❌ 图2 生成失败: 内容审核未通过
✅ 图3 生成成功
✅ 图4 生成成功

📊 生成统计: 成功 4/5, 失败 1/5
```

## 配置文件

### 在 config.json 中配置

```json
{
  "image_generation": {
    "max_concurrent": 3,
    "max_wait_time": 180,
    "poll_interval": 5,
    "max_retries": 3
  }
}
```

### 参数说明

- `max_concurrent`: 默认并发数
- `max_wait_time`: 单张图片最大等待时间（秒）
- `poll_interval`: 任务状态轮询间隔（秒）
- `max_retries`: 失败重试次数

## 编程接口

### 直接使用 AsyncImageService

```python
import asyncio
from src.async_image_service import AsyncImageService
from src.core.config_manager import ConfigManager

# 初始化
config = ConfigManager()
service = AsyncImageService(config)

# 准备提示词
prompts = [
    {'prompt': '老北京胡同', 'index': 1, 'is_cover': False},
    {'prompt': '故宫红墙', 'index': 2, 'is_cover': False},
    {'prompt': '天坛祈年殿', 'index': 3, 'is_cover': False},
]

# 异步生成
async def main():
    results = await service.generate_batch_images_async(
        prompts=prompts,
        max_concurrent=3
    )
    
    for result in results:
        if result.success:
            print(f"✅ 图{result.index}: {result.image_url}")
        else:
            print(f"❌ 图{result.index}: {result.error}")

# 运行
asyncio.run(main())
```

## 故障排查

### 问题1：ModuleNotFoundError: No module named 'aiohttp'

**解决方案**：
```bash
pip install aiohttp>=3.9.0
```

### 问题2：并发数过高导致限流

**症状**：
- 大量图片生成失败
- 错误信息包含 "rate limit" 或 "too many requests"

**解决方案**：
```bash
# 降低并发数
python run.py --image-mode api --async-mode --max-concurrent 2
```

### 问题3：网络不稳定导致超时

**症状**：
- 部分图片超时失败
- 错误信息包含 "timeout"

**解决方案**：
1. 检查网络连接
2. 增加超时时间（在 config.json 中配置）
3. 降低并发数

## 最佳实践

### 1. 首次使用

```bash
# 使用默认配置测试
python run.py --image-mode api --async-mode
```

### 2. 根据结果调优

- 如果全部成功：可以尝试提高并发数
- 如果有失败：降低并发数或检查网络

### 3. 监控性能

观察以下指标：
- 总耗时
- 成功率
- 失败原因

### 4. 生产环境

```bash
# 推荐配置
python run.py --image-mode api --async-mode --max-concurrent 3
```

## 与串行模式对比

| 特性 | 串行模式 | 异步并行模式 |
|------|---------|-------------|
| 性能 | 基准 | 提升 60% |
| 稳定性 | 高 | 中-高 |
| 资源占用 | 低 | 中 |
| 错误隔离 | 无 | 有 |
| 适用场景 | 保守、稳定 | 高效、批量 |

## 常见问题

### Q: 异步模式是否会影响图片质量？

A: 不会。异步模式只是改变了生成顺序，不影响图片质量。

### Q: 可以在模板模式下使用异步吗？

A: 不可以。异步模式仅支持 API 模式（`--image-mode api`）。

### Q: 并发数越高越好吗？

A: 不是。过高的并发数可能导致：
- API 限流
- 网络拥塞
- 内存占用过高

推荐使用 3-5 的并发数。

### Q: 如何查看详细的生成日志？

A: 查看 `logs/app.log` 文件，包含详细的生成日志。

## 技术细节

### 实现原理

1. **异步任务创建**：使用 `asyncio.create_task()` 创建多个并发任务
2. **并发控制**：使用 `asyncio.Semaphore` 限制并发数
3. **错误隔离**：使用 `asyncio.gather(..., return_exceptions=True)` 捕获异常
4. **连接复用**：使用 `aiohttp.ClientSession` 管理连接池

### 性能优化

1. **连接池**：复用 HTTP 连接，减少握手开销
2. **并发控制**：避免过度并发导致的资源竞争
3. **智能重试**：失败自动重试，提高成功率
4. **超时控制**：避免长时间等待

## 更新日志

### v1.0.0 (2026-02-13)

- ✅ 初始版本发布
- ✅ 支持异步并行生成
- ✅ 支持并发数配置
- ✅ 实现错误隔离
- ✅ 实现智能重试
- ✅ 集成到 run.py

## 反馈与支持

如有问题或建议，请查看：
- 性能报告：`PERFORMANCE_REPORT.md`
- 测试代码：`tests/test_image_generation_performance.py`
- 源代码：`src/async_image_service.py`

---

**最后更新**: 2026-02-13  
**版本**: 1.0.0
