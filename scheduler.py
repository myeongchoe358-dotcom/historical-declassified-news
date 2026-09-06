"""
定时任务调度器 - 每天定时收集和发送
"""
import schedule
import time
import logging
from datetime import datetime
from data_crawler import crawl_all_sources, DataCrawler
from content_processor import ContentProcessor
from email_sender import EmailSender

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewsScheduler:
    """新闻定时调度器"""
    
    def __init__(self):
        self.crawler = DataCrawler()
        self.processor = ContentProcessor()
        self.email_sender = EmailSender()
    
    def crawl_job(self):
        """爬虫任务"""
        logger.info("="*50)
        logger.info("开始执行数据爬虫任务")
        logger.info("="*50)
        
        try:
            crawl_all_sources()
            logger.info("数据爬虫任务完成")
        except Exception as e:
            logger.error(f"爬虫任务执行失败: {e}")
    
    def process_job(self):
        """内容处理任务"""
        logger.info("="*50)
        logger.info("开始执行内容处理任务")
        logger.info("="*50)
        
        try:
            import sqlite3
            conn = sqlite3.connect(self.crawler.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''SELECT a.id, a.original_text, a.title FROM articles a
                LEFT JOIN processed_articles pa ON a.id = pa.article_id
                WHERE pa.id IS NULL LIMIT 50''')
            
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                article_id, original_text, title = row
                self.processor.process_article(article_id, original_text or '', title or '')
            
            logger.info(f"内容处理任务完成，处理了 {len(rows)} 篇文章")
        except Exception as e:
            logger.error(f"内容处理任务执行失败: {e}")
    
    def email_job(self):
        """邮件发送任务"""
        logger.info("="*50)
        logger.info("开始执行邮件发送任务")
        logger.info("="*50)
        
        try:
            success = self.email_sender.send_daily_digest()
            if success:
                logger.info("邮件发送任务完成")
            else:
                logger.warning("邮件发送失败")
        except Exception as e:
            logger.error(f"邮件发送任务执行失败: {e}")
    
    def start(self, crawl_time='08:00', process_time='12:00', email_time='18:00'):
        """启动定时任务调度"""
        logger.info("="*50)
        logger.info("全球历史解密信息系统启动")
        logger.info("="*50)
        logger.info(f"爬虫任务: 每天 {crawl_time}")
        logger.info(f"处理任务: 每天 {process_time}")
        logger.info(f"邮件任务: 每天 {email_time}")
        logger.info("="*50)
        
        schedule.every().day.at(crawl_time).do(self.crawl_job)
        schedule.every().day.at(process_time).do(self.process_job)
        schedule.every().day.at(email_time).do(self.email_job)
        
        logger.info("定时调度器已启动，等待任务触发...")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("定时调度器已停止")
    
    def run_once(self):
        """手动执行一次所有任务（用于测试）"""
        logger.info("执行手动测试运行...")
        self.crawl_job()
        time.sleep(2)
        self.process_job()
        time.sleep(2)
        self.email_job()
        logger.info("手动测试运行完成")


if __name__ == '__main__':
    scheduler = NewsScheduler()
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        print("运行测试模式...")
        scheduler.run_once()
    else:
        scheduler.start(
            crawl_time='08:00',
            process_time='12:00',
            email_time='18:00'
        )
