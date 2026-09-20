import os
import random
import json
import sys
import smtplib
from email.mime.text import MIMEText
import requests

# ==================== 1. 抓取维基百科未解之谜 API (原文 + 来源链接) ====================
def fetch_wikipedia_mystery():
    """抓取维基百科条目的完整原文及其外部参考来源链接"""
    url = "https://zh.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts|extlinks",  # 同时获取全文 (extracts) 和 外部来源链接 (extlinks)
        "explaintext": True,
        "elimit": "10",              # 最多获取 10 个外部参考链接
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
                extlinks = page_info.get("extlinks", [])
                
                # 提取完整的链接地址
                sources = []
                for link in extlinks:
                    link_url = link.get("*", "")
                    if link_url.startswith("//"):
                        link_url = "https:" + link_url
                    if link_url.startswith("http"):
                        sources.append(link_url)

                # 拼接维基百科原条目链接
                wiki_url = f"https://zh.wikipedia.org/wiki/{requests.utils.quote(title)}"

                if len(extract) > 300:
                    mysteries.append({
                        "title": title,
                        "full_text": extract,
                        "wiki_url": wiki_url,
                        "sources": sources[:5]  # 保留前5个权威外部报道/文献链接
                    })
            
            if mysteries:
                selected = random.choice(mysteries)
                print(f"✅ 成功抓取选题：{selected['title']}（字数：{len(selected['full_text'])}，来源链接数：{len(selected['sources'])}）")
                return selected
    except Exception as e:
        print(f"⚠️ 维基百科 API 请求失败: {e}")
    
    return None

# ==================== 2. 本地 Fallback 备用读取 ====================
def get_fallback_mystery():
    """API 失败时的保底方案"""
    return {
        "title": "D.B. 库珀劫机案",
        "full_text": "1971年11月24日，一名自称 D.B. 库珀（D. B. Cooper）的男子劫持了一架波音727客机，在索要了20万美元勒索金和4顶降落伞后，于波特兰上空从三万英尺的高空跳伞潜逃。尽管美国联邦调查局（FBI）进行了大规模的搜捕与长达数十年的调查，至今仍未找到他的下落，生不见人死不见尸。这成为了美国历史上唯一未破的干线客机劫持悬案。",
        "wiki_url": "https://zh.wikipedia.org/wiki/D%C2%B7B%C2%B7%E5%BA%93%E6%B3%8A",
        "sources": [
            "https://www.fbi.gov/history/famous-cases/db-cooper-hijacking"
        ]
    }

# ==================== 3. 生成包含完整原文和来源链接的 HTML 页面 ====================
def generate_video_script(item):
    """生成排版精美的邮件 HTML"""
    title = item['title']
    full_text = item['full_text']
    wiki_url = item['wiki_url']
    sources = item.get('sources', [])

    # 将正文段落格式化
    formatted_paragraphs = "".join([f"<p>{p.strip()}</p>" for p in full_text.split("\n") if p.strip()])
    
    # 格式化来源链接列表
    source_links_html = f'<li><a href="{wiki_url}" target="_blank">维基百科完整条目页面</a></li>'
    for idx, src in enumerate(sources, 1):
        source_links_html += f'<li><a href="{src}" target="_blank">外部参考报道/文献来源 #{idx}</a></li>'

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif; line-height: 1.8; color: #2b2b2b; background-color: #f9f9f9; padding: 20px; }}
            .card {{ background: #ffffff; border: 1px solid #e1e4e8; border-radius: 8px; padding: 30px; max-width: 800px; margin: 0 auto; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
            .title {{ color: #1a73e8; font-size: 24px; font-weight: bold; border-bottom: 2px solid #1a73e8; padding-bottom: 12px; margin-bottom: 20px; }}
            .content {{ font-size: 15px; text-align: justify; border-bottom: 1px solid #eee; padding-bottom: 20px; }}
            .content p {{ margin-bottom: 16px; text-indent: 2em; }}
            .sources-box {{ background-color: #f8f9fa; padding: 15px; border-radius: 6px; margin-top: 20px; border-left: 4px solid #34a853; }}
            .sources-title {{ font-weight: bold; color: #2d7d32; font-size: 16px; margin-bottom: 8px; }}
            .sources-list {{ padding-left: 20px; margin: 0; font-size: 14px; word-break: break-all; }}
            .sources-list li {{ margin-bottom: 6px; }}
            .sources-list a {{ color: #1a73e8; text-decoration: none; }}
            .sources-list a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="title">📄 档案/案件详细原文：{title}</div>
            
            <div class="content">
                {formatted_paragraphs}
            </div>

            <div class="sources-box">
                <div class="sources-title">🔗 详细原文出处与参考报道链接：</div>
                <ul class="sources-list">
                    {source_links_html}
                </ul>
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
    mystery_item = fetch_wikipedia_mystery()
    if not mystery_item:
        mystery_item = get_fallback_mystery()

    email_html = generate_video_script(mystery_item)
    send_email(f"【档案详细原文及来源链接】{mystery_item['title']}", email_html)
