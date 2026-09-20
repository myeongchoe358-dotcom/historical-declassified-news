import os
import random
import json
import sys
import smtplib
from email.mime.text import MIMEText
import requests

# 专注三大核心分类（排除了人物志/传记）
CATEGORIES = [
    "Category:未解之谜",
    "Category:悬案",
    "Category:密码学",
    "Category:破译",
    "Category:解密文件",
    "Category:科学未解之谜"
]

# ==================== 1. 抓取详细原文与来源链接 ====================
def fetch_mystery_article():
    """抓取悬疑/未解之谜/硬核解密类的完整原文及其参考链接"""
    url = "https://zh.wikipedia.org/w/api.php"
    
    # 随机挑选一个分类抓取
    selected_category = random.choice(CATEGORIES)
    print(f"🔍 正在从分类抓取: {selected_category}")

    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts|extlinks",  # 抓取全文与外部参考链接
        "explaintext": True,
        "elimit": "10",              # 获取前 10 个外部来源链接
        "generator": "categorymembers",
        "gcmtitle": selected_category,
        "gcmlimit": "30"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GitHubActionsMysteryBot/1.0"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=12)
        if response.status_code == 200:
            data = response.json()
            pages = data.get('query', {}).get('pages', {})
            articles = []
            
            for page_id, page_info in pages.items():
                title = page_info.get("title", "")
                extract = page_info.get("extract", "")
                extlinks = page_info.get("extlinks", [])
                
                # 排除传记/人物相关分类及关键词（过滤人物志）
                if any(k in title for k in ["传", "生平", "作家", "演员", "教授", "总统", "总理"]):
                    continue

                # 提取外部参考报道链接
                sources = []
                for link in extlinks:
                    link_url = link.get("*", "")
                    if link_url.startswith("//"):
                        link_url = "https:" + link_url
                    if link_url.startswith("http"):
                        sources.append(link_url)

                wiki_url = f"https://zh.wikipedia.org/wiki/{requests.utils.quote(title)}"

                # 确保提取的是字数丰富的完整文章（> 300字）
                if len(extract) > 300:
                    articles.append({
                        "title": title,
                        "full_text": extract,
                        "wiki_url": wiki_url,
                        "sources": sources[:5]  # 保留前5个外部新闻/档案参考链接
                    })
            
            if articles:
                selected = random.choice(articles)
                print(f"✅ 成功抓取选题：{selected['title']}（字数：{len(selected['full_text'])}，来源链接数：{len(selected['sources'])}）")
                return selected
    except Exception as e:
        print(f"⚠️ 维基百科 API 请求失败: {e}")
    
    return None

# ==================== 2. 本地 Fallback 保底数据 ====================
def get_fallback_article():
    """保底选题（无人物传记，全为悬案/硬核解密）"""
    fallbacks = [
        {
            "title": "D.B. 库珀劫机案",
            "full_text": "1971年11月24日，一名自称 D.B. 库珀的男子劫持了一架波音727客机，索要20万美元勒索金及4顶降落伞后，在三万英尺高空跳伞潜逃。尽管美联邦调查局展开了数十年的大规模搜捕与调查，至今仍未找到其下落，生不见人死不见尸，成为美国历史上唯一的未破劫机悬案。",
            "wiki_url": "https://zh.wikipedia.org/wiki/D%C2%B7B%C2%B7%E5%BA%93%E6%B3%8A",
            "sources": ["https://www.fbi.gov/history/famous-cases/db-cooper-hijacking"]
        },
        {
            "title": "伏尼契手稿 (Voynich Manuscript)",
            "full_text": "伏尼契手稿是一本成书于大约1404年－1438年间的神秘书卷，全书使用未知文字和未知的语言编写，并附有大量奇特的植物、天文与炼金术插图。从冷战时期的顶尖密码学家到最强AI模型，至今无人能成功破译其真正含义。",
            "wiki_url": "https://zh.wikipedia.org/wiki/%E4%BC%8F%E5%B0%BC%E契%E6%89%8B%E7%A8%BF",
            "sources": ["https://beinecke.library.yale.edu/collections/highlights/voynich-manuscript"]
        }
    ]
    return random.choice(fallbacks)

# ==================== 3. 渲染邮件 HTML ====================
def generate_email_html(item):
    title = item['title']
    full_text = item['full_text']
    wiki_url = item['wiki_url']
    sources = item.get('sources', [])

    # 转化为排版段落
    formatted_paragraphs = "".join([f"<p>{p.strip()}</p>" for p in full_text.split("\n") if p.strip()])
    
    # 构建外部报道/参考链接
    source_links_html = f'<li><a href="{wiki_url}" target="_blank">维基百科完整条目页面</a></li>'
    for idx, src in enumerate(sources, 1):
        source_links_html += f'<li><a href="{src}" target="_blank">外部参考报道/解密文献源 #{idx}</a></li>'

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif; line-height: 1.8; color: #2b2b2b; background-color: #f9f9f9; padding: 20px; }}
            .card {{ background: #ffffff; border: 1px solid #e1e4e8; border-radius: 8px; padding: 30px; max-width: 800px; margin: 0 auto; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
            .tag {{ display: inline-block; background-color: #e8f0fe; color: #1a73e8; padding: 4px 10px; border-radius: 4px; font-size: 13px; font-weight: bold; margin-bottom: 10px; }}
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
            <div class="tag">🎬 中长视频素材库 (悬疑 / 硬核解密 / 极限未解)</div>
            <div class="title">📄 详细原文报道：{title}</div>
            
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
    article_item = fetch_mystery_article()
    if not article_item:
        article_item = get_fallback_article()

    email_html = generate_email_html(article_item)
    send_email(f"【悬案/硬核解密原文报道】{article_item['title']}", email_html)
