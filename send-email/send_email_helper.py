import smtplib
import argparse
import os
import json
import re
import imaplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
from email.header import Header
import mimetypes

# 尝试导入 markdown 库，用于将 md 转换为富文本 HTML 邮件
try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False

def send_email(to_addr, subject, body_content, is_html=False, cc_addr=None, save_draft=False, attachments=None):
    # 读取同级目录下的配置文件
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        print(f"❌ 错误: 找不到配置文件 {config_path}")
        return False
        
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        
    smtp_server = config.get("smtp_server")
    smtp_port = config.get("smtp_port", 465)
    username = config.get("username")
    password = config.get("password")
    from_addr = config.get("from_addr", username)
    sender_name = config.get("sender_name", "")
    signature = config.get("signature", "")
    
    # 结合命令行参数和配置文件判断是否仅存入草稿箱
    # 命令行如果显式传入 --draft 则为 True；否则读取 config.json 中的 default_to_draft 配置
    is_draft_mode = save_draft or config.get("default_to_draft", False)
    
    if not password or password == "your_auth_code_here":
        print("❌ 错误: 请在 config.json 中配置真实的邮件密码/授权码！")
        return False

    # 自动识别 "一、xxx" 格式并转换为 Markdown 二级标题，方便 CSS 放大渲染
    body_content = re.sub(r'^(?:##\s*)?([一二三四五六七八九十]、.*)$', r'## \1', body_content, flags=re.MULTILINE)

    # 构建发件人名称格式，并对中文名称进行标准 RFC 编码，避免新浪等邮箱 553 报错
    if sender_name:
        from_display = formataddr((str(Header(sender_name, 'utf-8')), from_addr))
    else:
        from_display = from_addr

    # 追加签名档 (如果有)
    if signature:
        body_with_sig = f"{body_content}\n\n<br>\n{signature}"
    else:
        body_with_sig = body_content

    # 组装 Multipart 邮件（同时包含纯文本和 HTML，符合标准商务邮件规范）
    msg = MIMEMultipart('alternative')
    msg['From'] = from_display
    msg['To'] = to_addr
    if cc_addr:
        msg['Cc'] = cc_addr
    msg['Subject'] = subject
    
    # 1. 挂载纯文本版本 (供不支持 HTML 的老旧客户端或反垃圾邮件扫描器读取)
    msg.attach(MIMEText(body_with_sig, 'plain', 'utf-8'))
    
    # 2. 挂载 HTML 版本 (富文本排版)
    if HAS_MARKDOWN:
        # 将 Markdown 转换为 HTML，开启 tables(表格) 和 sane_lists(更聪明的列表解析) 等扩展
        html_body = markdown.markdown(body_with_sig, extensions=['extra', 'sane_lists'])
        
        # 注入标准商务邮件 CSS 样式
        html_content = f"""
        <html>
        <head>
        <style>
            body {{
                font-family: 'Microsoft YaHei', 'PingFang SC', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.6;
                color: #333333;
                max-width: 800px;
            }}
            h2 {{
                font-size: 16px;
                font-weight: bold;
                color: #1a1a1a;
                margin-top: 24px;
                margin-bottom: 12px;
                border-bottom: 1px solid #eeeeee;
                padding-bottom: 6px;
            }}
            p {{ margin-bottom: 12px; }}
            strong {{ color: #1a1a1a; }}
            hr {{ border: 0; border-top: 1px solid #eeeeee; margin: 20px 0; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 16px; font-size: 13px; }}
            th, td {{ border: 1px solid #e0e0e0; padding: 10px 12px; text-align: left; }}
            th {{ background-color: #f8f9fa; font-weight: bold; color: #333; }}
            tr:nth-child(even) {{ background-color: #fafafa; }}
            ul, ol {{ margin-top: 0; margin-bottom: 12px; padding-left: 20px; }}
            li {{ margin-bottom: 4px; }}
            .signature {{
                font-size: 14px;
                color: #000000;
                line-height: 1.8;
                margin-top: 40px;
                font-family: 'Microsoft YaHei', 'PingFang SC', Arial, sans-serif;
            }}
            .signature a {{
                color: #1a73e8;
                text-decoration: none;
            }}
        </style>
        </head>
        <body>
        {html_body}
        </body>
        </html>
        """
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    elif is_html:
        # 如果没有安装 markdown 库，但强行指定了 HTML
        msg.attach(MIMEText(body_with_sig, 'html', 'utf-8'))

    # 3. 挂载附件
    if attachments:
        for filepath in attachments:
            if not os.path.isfile(filepath):
                print(f"⚠️ 警告: 附件文件不存在，已跳过: {filepath}")
                continue
            
            try:
                # 判断文件类型
                ctype, encoding = mimetypes.guess_type(filepath)
                if ctype is None or encoding is not None:
                    ctype = 'application/octet-stream'
                maintype, subtype = ctype.split('/', 1)
                
                # 读取文件并构建 MIMEBase
                with open(filepath, 'rb') as f:
                    part = MIMEBase(maintype, subtype)
                    part.set_payload(f.read())
                    
                # base64 编码
                encoders.encode_base64(part)
                
                # 设置 Content-Disposition 头，处理中文文件名
                filename = os.path.basename(filepath)
                # 使用 Header 编码文件名，避免中文乱码
                part.add_header('Content-Disposition', 'attachment', filename=str(Header(filename, 'utf-8')))
                msg.attach(part)
                print(f"📎 成功添加附件: {filename}")
            except Exception as e:
                print(f"❌ 添加附件失败 {filepath}: {e}")

    # 如果是保存草稿模式，则调用 IMAP
    if is_draft_mode:
        imap_server = config.get("imap_server", smtp_server.replace("smtp", "imap"))
        imap_port = config.get("imap_port", 993)
        try:
            print(f"正在连接 IMAP 服务器 {imap_server}:{imap_port} 保存草稿...")
            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
            mail.login(username, password)
            
            # 常见邮箱草稿箱名称（Drafts, 新浪/网易草稿箱, QQ Drafts）
            folders_to_try = ['Drafts', '草稿箱', '&g0l6P3ux-', 'Draft']
            success = False
            for folder in folders_to_try:
                try:
                    typ, _ = mail.append(folder, '\\Draft', imaplib.Time2Internaldate(time.time()), msg.as_bytes())
                    if typ == 'OK':
                        success = True
                        print(f"✅ 成功: 邮件已保存至草稿箱 [{folder}]，请前往邮箱客户端查看并发送。")
                        break
                except Exception:
                    continue
            
            mail.logout()
            if not success:
                print("❌ 保存草稿失败: 无法找到匹配的草稿箱文件夹，请检查邮箱 IMAP 设置。")
                return False
            return True
        except Exception as e:
            print(f"❌ 保存草稿失败: {e}")
            return False

    # 否则连接 SMTP 服务器并发送
    try:
        print(f"正在连接 SMTP 服务器 {smtp_server}:{smtp_port} ...")
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            
        server.login(username, password)
        
        # 处理发件列表（包含 To 和 Cc）
        recipients = [to_addr]
        if cc_addr:
            recipients.extend([email.strip() for email in cc_addr.split(',')])
            
        server.send_message(msg, from_addr=from_addr, to_addrs=recipients)
        server.quit()
        print(f"✅ 成功: 商务排版邮件已发送至 {to_addr}")
        if cc_addr:
            print(f"         已抄送至 {cc_addr}")
        return True
    except Exception as e:
        print(f"❌ 发送失败: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="发送电子邮件助手")
    parser.add_argument("--to", required=True, help="收件人邮箱地址")
    parser.add_argument("--cc", required=False, help="抄送人邮箱地址，多个地址用逗号分隔")
    parser.add_argument("--subject", required=True, help="邮件主题")
    parser.add_argument("--body", required=True, help="邮件正文内容或 md 文件路径")
    parser.add_argument("--html", action="store_true", help="是否以 HTML 格式发送")
    parser.add_argument("--draft", action="store_true", help="是否仅保存到草稿箱而不发送")
    parser.add_argument("--attachments", nargs='*', help="要发送的附件文件路径列表（支持多个）")
    
    args = parser.parse_args()
    
    body_content = args.body
    if os.path.exists(body_content) and os.path.isfile(body_content):
        with open(body_content, 'r', encoding='utf-8') as f:
            body_content = f.read()
            
    send_email(args.to, args.subject, body_content, args.html, args.cc, args.draft, args.attachments)
