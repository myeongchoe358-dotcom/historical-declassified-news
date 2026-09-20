import os
import random
import json
import sys
import smtplib
from email.mime.text import MIMEText
import requests

# 专注悬疑、硬核解密、极限挑战分类
CATEGORIES = [
    "Category:未解之谜",
    "Category:悬案",
    "Category:密码学",
    "Category:解密文件",
    "Category:科学未解之谜"
]

# ==================== 1. 抓取选题与基本资料 ====================
def fetch_topic():
    """从维基百科抓取符合条件的选题"""
    url = "https://zh.wikipedia.org/w/api.php"
    selected_category = random.choice(CATEGORIES)
    
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts|extlinks",
        "explaintext": True,
        "elimit": "5",
        "generator": "categorymembers",
        "gcmtitle": selected_category,
        "gcmlimit": "25"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GitHubActionsBot/1.0"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            pages = response.json().get('query', {}).get('pages', {})
            topics = []
            for page_id, page_info in pages.items():
                title = page_info.get("title", "")
                extract = page_info.get("extract", "")
                extlinks = page_info.get("extlinks", [])
                
                # 过滤人物传记
                if any(k in title for k in ["传", "生平", "作家", "演员", "教授", "总统"]):
                    continue
                
                sources = []
                for link in extlinks:
                    l = link.get("*", "")
                    if l.startswith("//"): l = "https:" + l
                    if l.startswith("http"): sources.append(l)

                wiki_url = f"https://zh.wikipedia.org/wiki/{requests.utils.quote(title)}"

                if len(extract) > 200:
                    topics.append({
                        "title": title,
                        "raw_info": extract[:1500],  # 截取基础信息给 AI
                        "wiki_url": wiki_url,
                        "sources": sources[:5]
                    })
            if topics:
                return random.choice(topics)
    except Exception as e:
        print(f"⚠️ 抓取失败: {e}")
    return None

# ==================== 2. 调用 Gemini API 扩写为完整长文文案 ====================
def expand_article_with_llm(topic_item):
    """使用 Gemini 大模型将资料扩展为 2000 字以上的完整详细报道/视频文案"""
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    
    # 如果没有配置 GEMINI_API_KEY，直接返回原始提取内容
    if not gemini_api_key:
        print("💡 未检测到 GEMINI_API_KEY，使用原文拼接模式。")
        return topic_item.get("raw_info", "")

    title = topic_item["title"]
    raw_info = topic_item["raw_info"]

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key}"
    
    prompt = f"""
    请你作为一名顶尖的悬疑/硬核解密纪录片编剧，针对选题【{title}】，撰写一篇字数在 1500-2500 字左右的【完整详细报道与中长视频脚本文案】。
    
    已知参考资料：
    {raw_info}

    撰写要求：
    1. 严禁概括或简写！必须给出最完整、最细致的案情/事件过程描述。
    2. 结构必须清晰，包含以下模块：
       - 【序幕：悬念开场】（抛出事件最离奇的矛盾点）
       - 【第一章：事件完整经过与起因】（时间、地点、人物、详细细节）
       - 【第二章：关键证据与现场调查】（调查人员发现的关键线索、尸检/档案/密码细节）
       - 【第三章：核心疑点与主流假说】（逐一剖析各种假说与破解尝试）
       - 【尾声：未解之谜与历史影响】
    3. 风格沉浸、客观、硬核，非常适合作为中长视频的旁白朗读文案。
    """

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        res = requests.post(url, json=payload, timeout=30)
        if res.status_code == 200:
            result = res.json()
            full_text = result['candidates'][0]['content']['parts'][0]['text']
            print("✅ 成功通过 LLM 生成完整详细长文文案！")
            return full_text
    except Exception as e:
        print(f"⚠️ LLM 生成失败: {e}")

    return raw_info

# ==================== 3. 渲染 HTML 页面 ====================
def generate_email_html(item, full_article_text):
    title = item['title']
    wiki_url = item['wiki_url']
    sources = item.get('sources', [])

    # 格式化文本换行
    paragraphs = full_article_text.split("\n")
    formatted_body = ""
    for p in paragraphs:
        p_str = p.strip()
        if not p_str:
            continue
        if p_str.startswith("【") or p_str.startswith("###") or p_str.startswith("#"):
            formatted_body += f"<h3 style='color: #1a73e8; margin-top: 20px;'>{p_str.replace('#', '')}</h3>"
        else:
            formatted_body += f"<p style='margin-bottom: 12px; text-indent: 2em;'>{p_str}</p>"

    source_links_html = f'<li><a href="{wiki_url}" target="_blank">维基百科完整条目</a></li>'
    for idx, src in enumerate(sources, 1):
        source_links_html += f'<li><a href="{src}" target="_blank">外部参考报道/文献 #{idx}</a></li>'

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'PingFang SC', Arial, sans-serif; line-height: 1.8; color: #222; background-color: #f4f5f7; padding: 20px; }}
            .card {{ background: #fff; border-radius: 8px; padding: 30px; max-width: 800px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
            .title {{ font-size: 24px; font-weight: bold; color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; margin-bottom: 20px; }}
            .content {{ font-size: 15px; text-align: justify; }}
            .sources-box {{ background-color: #f8f9fa; padding: 15px; border-radius: 6px; margin-top: 25px; border-left: 4px solid #34a853; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="title">🎬 完整中长视频文案档案：{title}</div>
            
            <div class="content">
                {formatted_body}
            </div>

            <div class="sources-box">
                <b>🔗 详细原文出处与参考报道链接：</b>
                <ul style="padding-left: 20px; margin-top: 8px;">
                    {source_links_html}
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

# ==================== 4. 发送邮件 ====================
def send_email(subject, html_body):
    email_address = os.environ.get("EMAIL_ADDRESS")
    smtp_password = os.environ.get("SMTP_PASSWORD")

    if not email_address or not smtp_password:
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
    topic_item = fetch_topic()
    if not topic_item:
        topic_item = {
            "title": "伏尼契手稿 (Voynich Manuscript)",
            "raw_info": "伏尼契手稿是一本成书于大约1404年－1438年间的神秘书卷，全书使用未知文字和未知的语言编写...",
            "wiki_url": "https://zh.wikipedia.org/wiki/伏尼契手稿",
            "sources": []
        }

    # 1. 扩写为完整长文
    full_text = expand_article_with_llm(topic_item)
    
    # 2. 生成 HTML
    email_html = generate_email_html(topic_item, full_text)
    
    # 3. 发送邮件
    send_email(f"【完整解密文案档案】{topic_item['title']}", email_html)
