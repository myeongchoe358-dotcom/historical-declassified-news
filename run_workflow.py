import os
import random
import json
import sys
import smtplib
from email.mime.text import MIMEText
import requests

# ==================== 1. 抓取维基百科未解之谜 API (完整原文) ====================
def fetch_wikipedia_mystery():
    """从维基百科 API 获取完整的未解之谜/悬疑条目全文内容"""
    url = "https://zh.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "explaintext": True,        # 提取纯文本，去除 HTML 标签
        # 注意：这里删除了 "exintro": True，从而抓取整篇维基文章的详细内容，而不仅是开头的摘要
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
                # 筛选出内容足够丰富、字数较长的文章（大于 300 字）
                if len(extract) > 300:
                    mysteries.append({"title": title, "full_text": extract})
            
            if mysteries:
                selected = random.choice(mysteries)
                print(f"✅ 成功抓取完整原文选题：{selected['title']}（字数：{len(selected['full_text'])}）")
                return selected
    except Exception as e:
        print(f"⚠️ 维基百科 API 请求失败: {e}")
    
    return None

# ==================== 2. 本地 Fallback 备用读取 ====================
def get_fallback_mystery():
    """当 API 抓取失败时，读取本地预设的经典悬案"""
    json_path = "fallback_mysteries.json"
    if not os.path.exists(json_path):
        json_path = os.path.join("scripts", "fallback_mysteries.json")
        
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data:
                    selected = random.choice(data)
                    print(f"📦 触发本地 Fallback 备用选题：{selected['title']}")
                    return {"title": selected['title'], "full_text": selected.get('summary', '')}
        except Exception as e:
            print(f"⚠️ 读取本地 JSON 失败: {e}")
            
    return {
        "title": "D.B. 库珀劫机案",
        "full_text": "1971年11月24日，一名自称 D.B. 库珀（D. B. Cooper）的男子劫持了一架波音727客机，在索要了20万美元勒索金和4顶降落伞后，于波特兰上空从三万英尺的高空跳伞潜逃。尽管美国联邦调查局（FBI）进行了大规模的搜捕与长达数十年的调查，至今仍未找到他的下落，生不见人死不见尸。这成为了美国历史上唯一未破的干线客机劫持悬案。"
    }

# ==================== 3. 生成完整原文邮件页面 ====================
def generate_video_script(item):
    """将案件完整原文整理为排版整洁的邮件文案"""
    title = item['title']
    full_text = item['full_text']

    # 将维基百科全文换行转换为 HTML 段落
    formatted_paragraphs = "".join([f"<p>{p.strip()}</p>" for p in full_text.split("\n") if p.strip()])

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif; line-height: 1.8; color: #2b2b2b; background-color: #f9f9f9; padding: 20px; }}
            .card {{ background: #ffffff; border: 1px solid #e1e4e8; border-radius: 8px; padding: 30px; max-width: 800px; margin: 0 auto; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
            .title {{ color: #1a73e8; font-size: 24px; font-weight: bold; border-bottom: 2px solid #1a73e8; padding-bottom: 12px; margin-bottom: 20px; }}
            .content {{ font-size: 15px; text-align: justify; white-space: pre-line; }}
            .content p {{ margin-bottom: 16px; text-indent: 2em; }}
            .footer {{ margin-top: 30px; padding-top: 15px; border-top: 1px solid #eee; font-size: 13px; color: #666; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="title">📄 档案/案件完整原文推送：{title}</div>
            
            <div class="content">
                {formatted_paragraphs}
            </div>

            <div class="footer">
                💡 提示：以上内容为自动化抓取的完整档案/条目原文，可直接用于中长视频脚本素材提炼与文案二次创作。
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
    # 1. 尝试从 API 抓取完整原文
    mystery_item = fetch_wikipedia_mystery()
    
    # 2. 如果抓取失败，使用本地保底
    if not mystery_item:
        mystery_item = get_fallback_mystery()

    # 3. 生成包含完整原文的 HTML 邮件
    email_html = generate_video_script(mystery_item)
    
    # 4. 发送邮件
    send_email(f"【详细档案原文】{mystery_item['title']}", email_html)
