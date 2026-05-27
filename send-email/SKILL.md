---
name: "send-email"
description: "通过 Python 脚本自动化发送电子邮件。当用户要求“发送邮件”、“发邮件给某人”或确认发出生成的 Cold Email 时调用此技能。"
---

# Send Email (商务邮件发送器)

这是一个**行动型 (Action-based) 技能**，结合底层的 Python 脚本，直接将你生成的营销文案、Cold Email 或工作汇报发送到目标客户/同事的邮箱。此版本已升级为**标准商务富文本邮件引擎**。

## 何时使用 (When to use)
- 当用户要求“把这封邮件发给 xxx@example.com”。
- 当你调用 `cold-email` 生成了陌拜邮件，并经过用户确认后，用户明确指示“好的，帮我发出去”或“帮我存到草稿箱”。

⚠️ **重要拦截规则 (Crucial Rule)**：
- 如果用户**仅仅是要求“写一封邮件”、“起草邮件”、“帮我写一个首次拜访邮件”**，你**绝不能**私自调用发送或存草稿的底层脚本。
- 你必须先将草拟的邮件正文展示给用户，并主动询问：“*这版文案您看可以吗？如果没问题，请告诉我‘确认发送’或‘存入草稿箱’，我再为您执行动作。*”
- 只有在收到用户**明确的发送或存草稿指令**后，才能触发底层动作。

## 商务排版规范 (Business Formatting Rules)
为了确保发出的邮件具有极高的专业度，你在撰写邮件正文（保存为 markdown）时，必须遵循以下排版规范：
1. **正式称呼**：使用“尊敬的 [姓名] [职务]：”或“[姓名] [职务]，您好！”开头。
2. **模块层级**：邮件正文的核心模块，必须采用中文数字编号（如：“一、会议总结”、“二、核心需求探讨”），让用户清晰看到整体内容结构。
3. **时间明确化**：如果文中提到相对时间（如“明天”、“本周内”），必须在括号内明确标注具体日期。例如：“明天内（05月21日）”、“本周内（05月24日截止）”。（注意根据当前真实日期进行推算）。
4. **列表与分行**：如果有 1/2/3 或 bullet points 等列表，必须确保**列表的上一行是一个空行**，且每个列表项单独占一行，以确保引擎正确渲染出标准邮件列表格式。
5. **表格规范**：如果采用网格/表格内容，必须使用标准的 Markdown 表格语法（`|---|---|`），底层脚本会自动将其渲染为带有边框和背景色的商务 HTML 表格。
6. **重点加粗**：合理使用 Markdown 的加粗语法 `**加粗文本**` 标出核心痛点、数据或收益，底层脚本会自动将其渲染为 HTML 的高亮粗体。
7. **无需手动落款**：正文结束后直接结束，**严禁写“顺颂商祺”、“祝工作顺利”等结束语，也绝对不要手动写签名档**（底层脚本会自动从 `config.json` 注入统一的商务签名）。

## 技能工作流 (Workflow)
1. **确认配置**：检查 `.trae/skills/send-email/config.json` 是否已填写正确的 SMTP/IMAP 账号信息。支持在 config 中配置 `"default_to_draft": true`，这样默认所有邮件都会先保存到草稿箱。
2. **安全落盘**：将邮件正文保存到临时文件 `.postplus/emails/temp_email.md`。
3. **确认附件（可选）**：如果用户要求发送附件，确认附件文件的绝对路径或相对路径。
4. **执行发送**：调用系统终端执行配套的 Python 脚本。脚本会自动将 Markdown 转为带 CSS 样式的富文本 HTML 并根据配置执行发送或存入草稿箱。

## 脚本调用示例
```bash
# 直接发送邮件
python3 .trae/skills/send-email/send_email_helper.py \
  --to "target@example.com" \
  --subject "【薪人薪事】关于近期连锁门店排班方案的沟通" \
  --body ".postplus/emails/temp_email.md"

# 仅保存到草稿箱（不发送，让用户手动检查后再发）
python3 .trae/skills/send-email/send_email_helper.py \
  --to "target@example.com" \
  --subject "【草稿】关于近期连锁门店排班方案的沟通" \
  --body ".postplus/emails/temp_email.md" \
  --draft

# 带有附件发送（支持多个附件，用空格分隔）
python3 .trae/skills/send-email/send_email_helper.py \
  --to "target@example.com" \
  --subject "【资料】连锁餐饮排班方案" \
  --body ".postplus/emails/temp_email.md" \
  --attachments "/path/to/proposal.pdf" "/path/to/pricing.xlsx"
```