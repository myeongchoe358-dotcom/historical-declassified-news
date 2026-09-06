"""
邮件发送模块 - 每日推送解密历史信息
"""
import smtplib
import sqlite3
from datetime import datetime
from typing import List, Dict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_CONFIG, CONTENT_DISTRIBUTION
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailSender:
    """邮件发送器类"""
    
    def __init__(self):
        self.db_file = 'declassified_news.db'
        self.config = EMAIL_CONFIG
    
    def get_daily_articles(self) -> List[Dict]:
        """获取今日推送的文章"""
        articles = []
        
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            for category, count in CONTENT_DISTRIBUTION.items():
                cursor.execute('''SELECT a.id, a.title, a.url, a.source, a.original_text, a.publish_date,
                        pa.subtitle_text, pa.timeline
                    FROM articles a
                    LEFT JOIN processed_articles pa ON a.id = pa.article_id
                    WHERE a.category = ?
                    ORDER BY RANDOM()
                    LIMIT ?''', (category, count))
                
                rows = cursor.fetchall()
                for row in rows:
                    article = {
                        'id': row[0],
                        'title': row[1],
                        'url': row[2],
                        'source': row[3],
                        'original_text': row[4][:500] if row[4] else '',
                        'publish_date': row[5],
                        'subtitle': row[6] or '未生成',
                        'timeline': row[7] or '{}',
                        'category': category
                    }
                    articles.append(article)
            
            conn.close()
            logger.info(f"获取到 {len(articles)} 篇文章用于今日推送")
        except Exception as e:
            logger.error(f"获取文章失败: {e}")
        
        return articles
    
    def generate_email_body(self, articles: List[Dict]) -> str:
        """生成邮件正文"""
        email_body = f"""
        <html><head><meta charset="UTF-8"><style>
        body {{ font-family: Arial, sans-serif; color: #333; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
        .article {{ margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; background: #f9f9f9; }}
        .article-title {{ font-size: 16px; font-weight: bold; color: #007bff; margin-bottom: 10px; }}
        .article-meta {{ font-size: 12px; color: #666; margin: 5px 0; }}
        .article-link {{ color: #007bff; text-decoration: none; }}
        .category-tag {{ display: inline-block; background: #007bff; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; }}
        </style></head><body><div class="container">
        <h1>🌍 全球历史解密日报 - {datetime.now().strftime('%Y年%m月%d日')}</h1>
        """
        
        for article in articles:
            email_body += f"""
            <div class="article">
                <span class="category-tag">{article['category']}</span>
                <div class="article-title">{article['title']}</div>
                <div class="article-meta">
                    📍 来源: {article['source']}<br>
                    📅 日期: {article['publish_date']}<br>
                    🔗 链接: <a href="{article['url']}" class="article-link" target="_blank">查看原文</a>
                </div>
                <div style="margin: 10px 0; line-height: 1.6;">{article['original_text']}</div>
                <div style="background: #e7f3ff; padding: 10px; margin: 10px 0; border-radius: 5px;">
                    <strong>📝 字幕:</strong><br>{article['subtitle']}
                </div>
            </div>
            """
        
        email_body += """</div></body></html>"""
        return email_body
    
    def send_email(self, articles: List[Dict]) -> bool:
        """发送邮件"""
        if not articles or not self.config['sender_email']:
            logger.warning("没有文章或邮件配置不完整")
            return False
        
        try:
            email_body = self.generate_email_body(articles)
            
            message = MIMEMultipart('alternative')
            message['Subject'] = f"全球历史解密日报 - {datetime.now().strftime('%Y年%m月%d日')}"
            message['From'] = self.config['sender_email']
            message['To'] = self.config['recipient_email']
            
            html_part = MIMEText(email_body, 'html', 'utf-8')
            message.attach(html_part)
            
            logger.info(f"正在发送邮件到 {self.config['recipient_email']}...")
            
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls()
                server.login(self.config['sender_email'], self.config['smtp_password'])
                server.send_message(message)
            
            logger.info(f"邮件发送成功")
            return True
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False
    
    def send_daily_digest(self) -> bool:
        """发送每日摘要"""
        logger.info("开始生成并发送每日摘要...")
        articles = self.get_daily_articles()
        return self.send_email(articles)


if __name__ == '__main__':
    sender = EmailSender()
    sender.send_daily_digest()
