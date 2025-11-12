# Rimworld MOD 汉化助手

自动提取 Rimworld MOD 中可汉化的内容,辅助用户进行汉化工作,并保存汉化结果(不覆盖原文件)。

## ✨ 核心功能

### 已实现功能 (v1.1 - 用户体验优化版本)

**核心功能**:
- ✅ **MOD 扫描与提取**: 自动扫描 MOD 目录,提取可翻译的 XML 内容
- ✅ **数据库管理**: SQLite 数据库存储翻译条目,支持进度追踪
- ✅ **翻译导出**: 生成标准的 ChineseSimplified 翻译文件
- ✅ **术语库**: 支持自定义术语库,确保翻译一致性
- ✅ **翻译记忆**: 智能匹配历史翻译,避免重复翻译
- ✅ **批量翻译**: 集成多种翻译 API (DeepSeek/百度/Ollama)
- ✅ **官方翻译对照**: 从游戏目录读取官方翻译作为参考
- ✅ **自动保存**: 定时自动保存翻译进度
- ✅ **会话管理**: 支持中断后继续翻译
- ✅ **GUI 图形界面**: 基于 Tkinter 的友好图形界面

**v1.1 新增功能**:
- 🆕 **批量MOD管理**: 选择MOD管理根目录,自动识别所有MOD并显示汉化状态
- 🆕 **汉化完成度检测**: 自动计算每个MOD的汉化完成度百分比
- 🆕 **配置热更新**: API密钥配置保存后立即生效,无需重启应用
- 🆕 **AI术语库集成**: DeepSeek翻译自动参考术语库,确保术语一致性
- 🆕 **双翻译引擎对比**: 编辑界面同时提供AI翻译和百度翻译,便于对比选择
- 🆕 **改进的配置界面**: 百度翻译配置添加详细说明和一键跳转获取密钥

### 待实现功能 (v2.0 - 后续版本)

- ⏳ **DLL/C# 文件支持**: 从编译文件提取可翻译内容
- ⏳ **翻译质量检查**: 自动检测翻译质量问题
- ⏳ **团队协作功能**: 支持多人协作翻译

## 🚀 快速开始

### 1. 环境要求

- Python 3.9 或更高版本
- Windows / macOS / Linux

### 2. 一键部署

在项目根目录运行部署脚本:

```powershell
# Windows
.\deploy.ps1
```

脚本会自动:
- 检查 Python 版本
- 创建虚拟环境
- 安装依赖(使用清华镜像源)
- 初始化数据库目录
- 创建配置文件
- **可选**: 部署完成后直接启动应用

### 3. 运行应用

#### 方式一: 使用快速启动脚本 (推荐)

```powershell
# 启动 GUI 模式
.\start-gui.ps1
```

#### 方式二: 手动启动

```bash
# 激活虚拟环境 (Windows)
.\venv\Scripts\activate

# 运行 GUI 模式
python src/main.py
```

## 📖 使用说明

### 基本操作流程:

1. **选择 MOD** 🆕
   - 点击"浏览"按钮
   - **方式一**: 直接选择单个MOD目录
   - **方式二**: 选择MOD管理根目录 (如 `steam/steamapps/workshop/content/294100`)
     - 应用会自动扫描所有MOD
     - 显示MOD列表,包含汉化状态(✓/✗)和完成度百分比
     - 双击选择要翻译的MOD

2. **提取 MOD**
   - 点击"提取 MOD"自动提取可翻译内容
   - 提取完成后会显示 MOD 信息和进度

3. **翻译方式**
   - **手动翻译**: 双击表格中的条目打开编辑对话框
   - **AI翻译**: 在编辑对话框中点击"AI翻译: 翻译"按钮 🆕
   - **百度翻译**: 在编辑对话框中点击"百度翻译: 翻译"按钮,与AI翻译对比 🆕
   - **批量翻译**: 选择翻译引擎后点击"批量翻译"按钮
   - **翻译记忆**: 编辑对话框中可以查询翻译记忆建议
   - **术语库查询**: 编辑对话框中可以搜索相关术语

4. **管理功能**
   - **术语库**: 点击"术语库"按钮管理专有名词翻译
   - **翻译记忆**: 点击"翻译记忆"按钮查看和管理历史翻译
   - **自动保存**: 应用会每30秒自动保存进度
   - **会话恢复**: 下次启动时自动提示恢复未完成的会话
   - **设置**: 配置翻译API密钥,保存后立即生效 🆕

5. **导出翻译**
   - 点击"导出翻译"生成 ChineseSimplified 翻译文件
   - 文件会保存到 MOD 的 Languages 目录下

### 术语库 CSV 格式

```csv
term_en,term_zh,category,priority,note
silver,银,material,10,游戏货币
steel,钢,material,10,基础建筑材料
colonist,殖民者,character,10,玩家控制的角色
```

## 📂 项目结构

```
rimworld-mod-localization-assistant/
├── src/                      # 源代码
│   ├── ui/                   # 界面层 (GUI)
│   ├── services/             # 服务层 (业务协调)
│   ├── logic/                # 业务逻辑层 (提取器+翻译器+批量翻译)
│   ├── data/                 # 数据访问层 (Repositories)
│   ├── storage/              # 存储层 (数据库+文件)
│   ├── models/               # 数据模型
│   ├── providers/            # 翻译提供商 (DeepSeek/百度/Ollama)
│   ├── utils/                # 工具函数
│   └── main.py               # 主程序入口
├── data/                     # 数据目录
│   ├── translations.db       # SQLite 数据库
│   └── backups/              # 数据库备份
├── config/                   # 配置目录
│   ├── translation_api.json  # API 配置
│   └── glossary.csv          # 默认术语库
├── docs/                     # 文档
├── tests/                    # 测试文件
├── requirements.txt          # 依赖清单
├── deploy.ps1                # 一键部署脚本
├── start-gui.ps1             # 快速启动 GUI
└── README.md                 # 本文件
```

## 🔧 配置说明

### 首次配置

1. **复制配置模板**
   ```bash
   # 将模板文件复制为实际配置文件
   cp config/translation_api.json.example config/translation_api.json
   ```

2. **配置翻译 API**

   在 GUI 界面中点击"设置"按钮,或手动编辑 `config/translation_api.json`:

   ```json
   {
     "default_provider": "deepseek",
     "providers": {
       "deepseek": {
         "enabled": true,
         "api_key": "YOUR_DEEPSEEK_API_KEY_HERE",
         "base_url": "https://api.deepseek.com/v1",
         "model": "deepseek-chat"
       },
       "baidu": {
         "enabled": false,
         "api_key": "YOUR_BAIDU_API_KEY_HERE",
         "secret_key": "YOUR_BAIDU_SECRET_KEY_HERE"
       },
       "ollama": {
         "enabled": false,
         "model": "qwen2.5:7b",
         "base_url": "http://localhost:11434"
       }
     },
     "rimworld_path": "",
     "auto_save_interval": 30
   }
   ```

### 支持的翻译引擎

| 引擎 | 类型 | 费用 | 优点 | 获取方式 |
|------|------|------|------|----------|
| **DeepSeek** | 云端AI | 按量付费 | 翻译质量高,速度快,自动参考术语库🆕 | [DeepSeek官网](https://platform.deepseek.com/) |
| **百度翻译** | 云端API | 免费额度200万字/月 | 免费额度充足,配置简单🆕 | [百度翻译开放平台](https://fanyi-api.baidu.com/) |
| **Ollama** | 本地AI | 完全免费 | 隐私保护,无限使用 | [Ollama官网](https://ollama.ai/) |

#### 百度翻译API配置指南 🆕

1. 访问 [百度翻译开放平台](https://fanyi-api.baidu.com/)
2. 登录并进入"管理控制台"
3. 在"开发者信息"页面获取:
   - **APP ID**: 一串数字 (如: `20150910000012345`)
   - **密钥**: 32位字符串 (如: `abcdefgh12345678...`)
4. 在应用"设置"中填写这两个密钥
5. 免费额度: 每月200万字符,完全够用!

**提示**: 设置界面的蓝色帮助文字可以点击,直接跳转到密钥获取页面。

### Rimworld 游戏路径

设置游戏路径后可以:
- 导入官方术语库
- 参考官方翻译
- 自动扫描所有DLC

默认路径: `D:\Softwares\Steam\steamapps\common\RimWorld`

### 隐私保护

⚠️ **重要**: `config/translation_api.json` 包含您的 API 密钥,已被 `.gitignore` 排除,不会上传到版本控制。

- ✅ 模板文件: `config/translation_api.json.example` (可以上传)
- ❌ 配置文件: `config/translation_api.json` (包含密钥,不要上传!)

## ⚠️ 注意事项

1. **不覆盖原文件**: 所有翻译文件生成到 `Languages/ChineseSimplified/` 目录,不会修改原始 MOD 文件
2. **编码格式**: 所有 XML 文件使用 UTF-8 编码
3. **备份建议**: 建议在翻译前备份 MOD 文件
4. **路径格式**: Windows 路径可以使用 `/` 或 `\`,程序会自动处理

## 🔮 开发路线图

### v1.1 (当前版本 - 用户体验优化) ✅
- ✅ 批量MOD管理和汉化状态检测
- ✅ API配置热更新,无需重启
- ✅ AI翻译集成术语库,提升翻译一致性
- ✅ 双翻译引擎对比功能
- ✅ 改进的配置界面和帮助文档

### v1.0 (基础版本) ✅
- ✅ 完整的 GUI 图形界面
- ✅ 自动保存和会话恢复
- ✅ 批量翻译、翻译记忆、会话管理功能

### v2.0 (未来计划)
- ⏳ 支持从 DLL/C# 文件提取可翻译内容
- ⏳ 翻译质量检查和自动校对
- ⏳ 团队协作功能
- ⏳ 完整的测试覆盖和性能优化
- ⏳ 更多翻译引擎支持

## 📄 许可证

本项目遵循 MIT 许可证。

## 🙏 鸣谢

- Rimworld 游戏及其 MOD 社区
- lxml - 强大的 XML 处理库
- Claude Code - AI 辅助开发工具

---

**当前版本**: v1.1 - 用户体验优化版本! 🎉

**版本更新日志**:
- **v1.1 (2025-01-12)**: 用户体验全面优化
  - 🆕 批量MOD管理: 一次性查看所有MOD的汉化状态
  - 🆕 配置热更新: API密钥修改后立即生效
  - 🆕 术语库集成: AI翻译自动参考术语库
  - 🆕 双引擎对比: 同时提供AI翻译和百度翻译
  - 🆕 改进配置界面: 更友好的帮助文档和引导

- **v1.0 (2024)**: 基础功能完整实现
  - ✅ 完整的 GUI 界面
  - ✅ 多翻译引擎支持
  - ✅ 翻译记忆和术语库
  - ✅ 自动保存和会话恢复

**开发进度**:
- ✅ 阶段一: 基础设施搭建
- ✅ 阶段二: Storage层和Service层实现
- ✅ 阶段三: 高级功能(翻译记忆、批量翻译、官方对照、会话管理)
- ✅ 阶段四: GUI界面开发
- ✅ 阶段五: 用户体验优化 (v1.1)
- ⏳ 阶段六: 测试覆盖和性能优化 (v1.2)

**功能亮点**:
- 🖥️ 友好的 GUI 图形界面
- 🤖 AI 翻译集成: DeepSeek/百度/Ollama 多种引擎
- 🧠 智能翻译记忆: 自动匹配历史翻译
- 📚 术语库管理: 确保专有名词一致性,AI翻译自动参考 🆕
- 💾 自动保存: 30秒间隔,永不丢失进度
- 🔄 会话恢复: 随时中断,随时继续
- 📂 批量MOD管理: 一键查看所有MOD汉化状态 🆕
- ⚡ 配置热更新: 修改配置无需重启 🆕

如有问题或建议,欢迎提交 Issue!

