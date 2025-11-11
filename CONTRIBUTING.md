# 贡献指南

感谢您对 Rimworld MOD 汉化助手的关注!

## 如何贡献

### 报告 Bug

如果您发现了 Bug,请:
1. 在 Issues 中搜索是否已有相同问题
2. 如果没有,创建新 Issue 并提供:
   - 详细的问题描述
   - 复现步骤
   - 您的环境信息 (操作系统、Python 版本等)
   - 相关的错误日志

### 提交功能建议

如果您有好的想法:
1. 在 Issues 中创建 Feature Request
2. 详细描述功能需求和使用场景
3. 如果可能,提供实现思路

### 提交代码

1. **Fork 项目**
   ```bash
   # Fork 到您的账号后 clone
   git clone https://gitee.com/YOUR_USERNAME/rimworld-mod-localization-assistant.git
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **遵循代码规范**
   - 使用 snake_case 命名 (函数、变量、文件名)
   - 添加必要的注释和文档字符串
   - 遵循 PEP 8 规范

4. **测试您的代码**
   - 确保现有功能正常工作
   - 为新功能添加测试

5. **提交代码**
   ```bash
   git add .
   git commit -m "feat: 添加某某功能"
   ```

6. **推送并创建 Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

### 提交信息规范

使用约定式提交 (Conventional Commits):

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/配置相关

示例:
```
feat: 添加批量翻译进度条
fix: 修复术语库查询错误
docs: 更新 README 安装说明
```

## 开发环境设置

1. **安装依赖**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **配置开发环境**
   ```bash
   # 复制配置模板
   cp config/translation_api.json.example config/translation_api.json
   # 编辑配置文件,添加您的 API 密钥
   ```

3. **运行测试**
   ```bash
   pytest tests/
   ```

## 代码审查

所有 Pull Request 都需要经过审查才能合并。审查重点:
- 代码质量和可读性
- 是否遵循项目架构规范
- 功能完整性和正确性
- 是否包含必要的文档和测试

## 许可证

通过提交代码,您同意您的贡献将以 MIT 许可证发布。

---

再次感谢您的贡献! 🎉
