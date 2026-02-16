# GitHub Actions CI/CD 配置说明

本目录包含 RedBookContentGen 项目的 CI/CD 工作流配置。

## 📋 工作流列表

### 1. CI 工作流 (`ci.yml`)

**触发条件**:
- 推送到 `main` 或 `develop` 分支
- 针对 `main` 或 `develop` 分支的 Pull Request
- 手动触发

**包含的检查**:
1. **代码质量检查** (`code-quality`)
   - Flake8 代码风格检查
   - Pylint 代码质量检查
   - 失败不阻止构建（仅警告）

2. **类型检查** (`type-check`) ⚠️ **关键步骤**
   - mypy 类型检查
   - **失败将导致构建失败**
   - 必须通过才能继续后续步骤

3. **单元测试** (`test`)
   - 运行 `tests/unit/` 下的所有单元测试
   - 生成测试覆盖率报告
   - 上传覆盖率到 Codecov
   - 依赖类型检查通过

4. **集成测试** (`integration-test`)
   - 仅在推送到 `main` 分支时运行
   - 运行不需要 API Key 的集成测试
   - 失败不阻止构建

5. **构建检查** (`build`)
   - 检查模块导入
   - 检查配置管理器初始化
   - 依赖类型检查和单元测试通过

### 2. 类型检查工作流 (`type-check.yml`)

**触发条件**:
- 推送包含 Python 文件、mypy.ini 或 requirements.txt 的更改
- 针对 `main` 或 `develop` 分支的 Pull Request（包含相关文件更改）
- 手动触发

**功能**:
- 专门用于 mypy 类型检查
- 生成 HTML 格式的类型检查报告
- 上传报告为构建产物（保留 30 天）
- **失败将导致构建失败**

## 🔍 类型检查说明

### 为什么类型检查失败会导致构建失败？

类型检查是代码质量的重要保障：
- ✅ 在编译时发现潜在的类型错误
- ✅ 提高代码可维护性和可读性
- ✅ 减少运行时错误
- ✅ 改善 IDE 代码提示和自动补全

### 本地运行类型检查

在提交代码前，建议先在本地运行类型检查：

```bash
# 运行 mypy 类型检查
mypy src/ --config-file=mypy.ini

# 生成 HTML 报告
mypy src/ --config-file=mypy.ini --html-report mypy-report
```

### 类型检查配置

类型检查配置位于 `mypy.ini` 文件中：
- 核心模块（`src/core/`）启用严格类型检查
- 业务模块采用渐进式类型检查
- 第三方库忽略类型检查

详细配置说明请参考 `mypy.ini` 文件中的注释。

## 📊 查看构建状态

### 在 GitHub 上查看

1. 进入项目的 GitHub 页面
2. 点击 "Actions" 标签
3. 查看最近的工作流运行记录

### 构建徽章

可以在 README.md 中添加构建状态徽章：

```markdown
![CI](https://github.com/your-username/RedBookContentGen/workflows/CI/badge.svg)
![Type Check](https://github.com/your-username/RedBookContentGen/workflows/Type%20Check/badge.svg)
```

## 🔧 配置 Secrets

某些工作流可能需要配置 GitHub Secrets：

1. 进入项目的 Settings > Secrets and variables > Actions
2. 添加以下 Secrets（如需要）：
   - `OPENAI_API_KEY`: OpenAI API 密钥（用于集成测试）
   - `CODECOV_TOKEN`: Codecov 上传令牌（可选）

## 📝 工作流依赖关系

```
code-quality (可选)
       ↓
  type-check (必须通过) ⚠️
       ↓
     test (必须通过)
       ↓
integration-test (可选)
       ↓
     build (必须通过)
```

## 🚀 最佳实践

1. **提交前检查**: 在提交代码前运行本地类型检查和测试
2. **小步提交**: 频繁提交小的更改，便于快速定位问题
3. **修复类型错误**: 不要忽略类型检查错误，及时修复
4. **查看报告**: 定期查看类型检查报告，了解代码质量趋势
5. **更新配置**: 随着项目发展，逐步提高类型检查的严格程度

## 🐛 常见问题

### Q: 类型检查失败怎么办？

A: 
1. 查看 Actions 日志中的错误信息
2. 在本地运行 `mypy src/ --config-file=mypy.ini` 复现问题
3. 根据错误提示修复类型注解
4. 如果是第三方库的问题，在 `mypy.ini` 中添加忽略规则

### Q: 如何跳过某个检查？

A: 
- 代码质量检查（Flake8/Pylint）失败不会阻止构建
- 类型检查失败**会**阻止构建，这是设计行为
- 如果确实需要临时跳过，可以在代码中添加 `# type: ignore` 注释

### Q: 如何查看类型检查报告？

A:
1. 进入 Actions 页面
2. 点击对应的工作流运行
3. 在 "Artifacts" 部分下载 `mypy-report`
4. 解压后用浏览器打开 `index.html`

## 📚 相关文档

- [mypy 官方文档](https://mypy.readthedocs.io/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [pytest 文档](https://docs.pytest.org/)
- [项目测试指南](../docs/TESTING.md)
- [mypy 配置说明](../MYPY_SETUP_SUMMARY.md)

---

**最后更新**: 2026-02-13  
**维护者**: RedBookContentGen 开发团队
