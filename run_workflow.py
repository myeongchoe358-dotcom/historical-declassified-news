import os
import random
import json
import sys
import smtplib
from email.mime.text import MIMEText
import requests

# ==================== 1. 抓取维基百科未解之谜 API ====================
def fetch_wikipedia_mystery():
    """从维基百科 API 获取随机未解之谜/悬疑条目"""
    url = "https://zh.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
        "generator": "categorymembers",
        "gcmtitle": "Category:未解之谜",
        "gcmlimit": "20"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GitHubActionsMysteryBot/1.0"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            pages = data.get('query', {}).get('pages', {})
            mysteries = []
            for page_id, page_info in pages.items():
                title = page_info.get("title", "")
                extract = page_info.get("extract", "")
                # 过滤掉内容太短或无关的页面
                if len(extract) > 100:
                    mysteries.append({"title": title, "summary": extract})
            
            if mysteries:
                selected = random.choice(mysteries)
                print(f"✅ 成功从维基百科 API 抓取选题：{selected['title']}")
                return selected
    except Exception as e:
        print(f"⚠️ 维基百科 API 请求失败: {e}")
    
    return None

# ==================== 2. 本地 Fallback 备用读取 ====================
def get_fallback_mystery():
    """当 API 抓取失败时，读取本地预设的经典悬案"""
    json_path = os.path.join("scripts", "fallback_mysteries.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data:
                    selected = random.choice(data)
                    print(f"📦 触发本地 Fallback 备用选题：{selected['title']}")
                    return selected
        except Exception as e:
            print(f"⚠️ 读取本地 JSON 失败: {e}")
            
    # 极端保底硬编码
    return {
        "title": "D.B. 库珀劫机案",
        "summary": "1971年，一名自称 D.B. 库珀的男子劫持客机跳伞潜逃，成为美国历史上唯一的未破劫机悬案。"
    }

# ==================== 3. 生成中长视频脚本框架 ====================
def generate_video_script(item):
    """将案件素材转化为中长视频（5-10分钟）爆款脚本框架"""
    title = item['title']
    summary = item['summary']

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .card {{ border: 1px solid #ddd; padding: 20px; border-radius: 8px; max-width: 700px; margin: 0 auto; }}
            .title {{ color: #1a73e8; font-size: 22px; font-weight: bold; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }}
            .section {{ margin-top: 15px; }}
            .section-title {{ font-weight: bold; color: #d93025; font-size: 16px; }}
            .code-box {{ background-color: #f5f5f5; padding: 12px; border-left: 4px solid #1a73e8; font-size: 14px; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="title">🎬 中长视频每日选题推送：{title}</div>
            
            <div class="section">
                <div class="section-title">📌 事件背景与梗概</div>
                <p>{summary}</p>
            </div>

            <div class="section">
                <div class="section-title">💡 建议黄金叙事结构 (5-10分钟)</div>
                <div class="code-box">
                    <b>[00:00 - 00:30] 悬念开局：</b> 直接展现最离奇的结果或细节，抛出核心矛盾。<br>
                    <b>[00:30 - 03:00] 事件起因：</b> 还原事件发生当天的经过，建立沉浸感。<br>
                    <b>[03:00 - 06:00] 关键转折：</b> 梳理警方/调查人员发现的关键线索与死胡同。<br>
                    <b>[06:00 - 08:30] 假说与推演：</b> 列举主流的几种假说（如人为、意外、阴谋论）并逐一剖析。<br>
                    <b>[08:30 - 结尾] 升华与互动：</b> 留下引发观众讨论的问题，引导评论区留言。
                </div>
            </div>

            <div class="section">
                <div class="section-title">🎯 推荐检索视频素材关键词</div>
                <p><code>{title}</code>、<code>{title} 档案照片</code>、<code>未解之谜 纪录片</code></p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

# ==================== 4. 发送邮件逻辑 ====================
def send_email(subject, html_body):
    email_address = os.environ.get("EMAIL_ADDRESS")
    smtp_password = os.environ.get("SMTP_PASSWORD")

    if not email_address or not smtp_password:
        print("❌ 缺失 EMAIL_ADDRESS 或 SMTP_PASSWORD 环境变量！")
        sys.exit(1)

    msg = MIMEText(html_body, 'html', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = email_address
    msg['To'] = email_address

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(email_address, smtp_password)
        server.send_message(msg)
        server.quit()
        print("✅ 邮件推送成功！")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        sys.exit(1)

# ==================== 主入口 ====================
if __name__ == "__main__":
    # 1. 尝试从 API 抓取
    mystery_item = fetch_wikipedia_mystery()
    
    # 2. 如果抓取失败，自动使用本地 Fallback
    if not mystery_item:
        mystery_item = get_fallback_mystery()

    # 3. 生成 HTML 邮件文案
    email_html = generate_video_script(mystery_item)
    
    # 4. 发送邮件
    send_email(f"【中长视频选题灵感】{mystery_item['title']}", email_html)
