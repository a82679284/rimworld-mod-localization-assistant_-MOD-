# 上传到 Gitee 前的检查清单

## ✅ 必须完成的检查项

### 1. 隐私数据清理
- [ ] 确认 `config/translation_api.json` 已被 `.gitignore` 排除
- [ ] 检查所有代码文件中是否有硬编码的 API Key
- [ ] 检查数据库文件是否已被 `.gitignore` 排除
- [ ] 确认 `data/` 目录下的数据库不会被上传

### 2. 配置文件检查
- [ ] 确认存在 `config/translation_api.json.example` 模板文件
- [ ] 模板文件中的 API Key 都是占位符 (YOUR_*_API_KEY_HERE)
- [ ] 模板文件中没有真实的游戏路径

### 3. 文档完整性
- [ ] README.md 包含完整的使用说明
- [ ] README.md 包含配置说明和隐私保护提示
- [ ] LICENSE 文件存在
- [ ] CONTRIBUTING.md 贡献指南存在

### 4. 代码质量
- [ ] 移除所有调试用的 print 语句或改为日志
- [ ] 移除所有 traceback.print_exc() 调试代码
- [ ] 确认所有功能正常工作
- [ ] 没有遗留的测试代码或注释掉的代码

### 5. .gitignore 检查
- [ ] 包含 `config/translation_api.json`
- [ ] 包含 `data/*.db` 和 `*.db-journal`
- [ ] 包含 `venv/` 和虚拟环境相关目录
- [ ] 包含 IDE 配置目录 (.vscode/, .idea/, .claude/)
- [ ] 包含临时文件 (*.log, *.tmp, *.bak)

### 6. 依赖和部署
- [ ] requirements.txt 包含所有必要的依赖
- [ ] deploy.ps1 脚本可以正常运行
- [ ] start-gui.ps1 和 start-cli.ps1 脚本可用

## 🔍 推荐检查项

### 代码审查
- [ ] 所有函数都有文档字符串
- [ ] 遵循 PEP 8 代码规范
- [ ] 没有重复代码

### 用户体验
- [ ] 所有错误信息都是中文且友好
- [ ] 进度提示清晰明确
- [ ] 界面布局合理

### 性能优化
- [ ] 没有明显的性能问题
- [ ] 批量操作有进度提示
- [ ] 大文件处理没有内存泄漏

## 🚀 上传步骤

1. **初始化 Git 仓库** (如果还没有)
   ```bash
   git init
   git add .
   git commit -m "feat: 初始提交 - Rimworld MOD 汉化助手 v1.0"
   ```

2. **关联远程仓库**
   ```bash
   git remote add origin https://gitee.com/YOUR_USERNAME/rimworld-mod-localization-assistant.git
   ```

3. **推送代码**
   ```bash
   git push -u origin master
   ```

4. **验证上传结果**
   - 在 Gitee 上检查所有文件是否正确上传
   - 确认 `config/translation_api.json` 没有被上传
   - 确认 `.gitignore` 正常工作

## ⚠️ 紧急情况处理

### 如果不小心上传了 API Key:

1. **立即删除泄露的密钥**
   - 登录 API 提供商控制台
   - 删除或重置 API Key

2. **清理 Git 历史**
   ```bash
   # 方法1: 使用 git filter-branch (危险操作!)
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch config/translation_api.json" \
     --prune-empty --tag-name-filter cat -- --all

   # 方法2: 使用 BFG Repo-Cleaner
   bfg --delete-files config/translation_api.json
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   ```

3. **强制推送**
   ```bash
   git push origin --force --all
   ```

4. **通知协作者**
   - 告知其他开发者更新本地仓库

---

**最后提醒**: 上传前务必完成所有检查项,确保没有泄露隐私数据!
