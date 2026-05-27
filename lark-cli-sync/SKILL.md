---
name: "lark-cli-sync"
description: "使用飞书官方 CLI (lark-cli) 同步文档、创建云文档、知识库等。相比旧版更稳定，支持 Oauth 用户级授权。当用户要求用官方 CLI 同步飞书文档时调用。"
---

# Lark CLI Sync (飞书官方文档同步助手)

这是一个使用飞书官方命令行工具 (`@larksuite/cli`) 来同步文档的技能。相比于自建 Python 脚本，它具备更稳定的鉴权体系（支持用户级别的 OAuth 登录，不再需要各种企业应用的 `folder_token` 提权），同时支持创建云文档、知识库等更多功能。

## 何时使用 (When to use)
- 当用户要求“用官方 CLI 把文档同步到飞书”。
- 当用户要求“把这篇文档同步到我的飞书文件夹”，且希望使用最稳定的官方链路。
- 替代旧版的 `feishu-doc-sync`。

⚠️ **重要拦截规则 (Crucial Rule)**：
- 必须先将草拟的正文展示给用户确认，当用户明确同意后再执行上传。

## 技能工作流 (Workflow)

### 1. 首次使用：配置与鉴权 (Initialization)
由于使用了官方工具，首次使用需要初始化配置并进行授权。
执行以下命令：
```bash
# 1. 自动创建一个新的飞书应用配置
npx @larksuite/cli@latest config init --new

# 2. 引导用户进行登录并授权
# 这一步会输出一个链接，请将链接发送给用户，用户在浏览器中确认后，终端会自动继续
npx @larksuite/cli@latest auth login --recommend
```

### 2. 配置目标文件夹 (Target Folder)
为了保障信息安全，目标文件夹 Token 不应硬编码在指令中。请将你的目标文件夹配置在 `.trae/skills/lark-cli-sync/config.json` 中，例如：
```json
{
  "folder_token": "你的文件夹Token"
}
```

### 3. 同步文档 (Syncing Document)
将需要同步的文本内容（Markdown 格式）保存到临时文件（例如 `.postplus/feishu/temp_doc.md`）。

**AI 执行同步前，请先读取 `config.json` 获取 `folder_token`。**
然后使用以下命令上传：

```bash
# 1. 自动在用户的“我的空间”创建文档 (如果 config.json 中没有配置 folder_token)
npx @larksuite/cli@latest docs +create \
  --title "【文档标题】" \
  --markdown @.postplus/feishu/temp_doc.md

# 2. 同步到 config.json 指定的文件夹 (推荐)
npx @larksuite/cli@latest docs +create \
  --title "【文档标题】" \
  --folder-token "<从 config.json 中读取到的 folder_token>" \
  --markdown @.postplus/feishu/temp_doc.md
```

## 注意事项
1. `@larksuite/cli` 的命令支持 `--dry-run` 来预览请求，不确定时可先预览。
2. 对于 AI 来说，在执行 `auth login --recommend` 时，终端会被挂起，AI 应该使用 `RunCommand` 并把 `blocking` 设为 `false`，或者提取返回的 JSON 中的 `device_code` 并将其写入 `config.json` 中作为临时状态保存。
