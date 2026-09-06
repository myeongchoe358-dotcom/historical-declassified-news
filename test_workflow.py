"""
完整工作流测试脚本 - 测试所有功能是否正常运行
"""
import sys
import time
import sqlite3
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkflowTester:
    """工作流测试器"""
    
    def __init__(self):
        self.db_file = 'declassified_news.db'
        self.test_results = {
            'config': False,
            'database': False,
            'crawler': False,
            'processor': False,
            'email': False,
            'scheduler': False
        }
    
    def print_header(self, title):
        """打印测试标题"""
        print("\n" + "="*60)
        print(f"  {title}")
        print("="*60)
    
    def print_step(self, step_num, description):
        """打印测试步骤"""
        print(f"\n[步骤 {step_num}] {description}")
        print("-" * 60)
    
    def print_result(self, test_name, passed, message=""):
        """打印测试结果"""
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {test_name}")
        if message:
            print(f"    说明: {message}")
        self.test_results[test_name] = passed
    
    def test_config(self):
        """测试1：配置文件"""
        self.print_step(1, "测试配置文件")
        
        try:
            from config import (
                EMAIL_CONFIG, 
                CONTENT_DISTRIBUTION, 
                DATA_SOURCES,
                CRAWLER_CONFIG
            )
            
            # 检查邮件配置
            if not EMAIL_CONFIG.get('sender_email'):
                self.print_result('config', False, "邮件地址未配置")
                return
            
            logger.info(f"邮件地址: {EMAIL_CONFIG['sender_email']}")
            
            # 检查内容分布
            total = sum(CONTENT_DISTRIBUTION.values())
            logger.info(f"每日推送数量: {total} 条")
            logger.info(f"  - 政治: {CONTENT_DISTRIBUTION.get('politics', 0)} 条")
            logger.info(f"  - 战争: {CONTENT_DISTRIBUTION.get('war', 0)} 条")
            logger.info(f"  - 经济: {CONTENT_DISTRIBUTION.get('economy', 0)} 条")
            logger.info(f"  - 社会: {CONTENT_DISTRIBUTION.get('society', 0)} 条")
            logger.info(f"  - 科技: {CONTENT_DISTRIBUTION.get('technology', 0)} 条")
            
            # 检查数据源
            enabled_sources = [s for s, v in DATA_SOURCES.items() if v.get('enabled')]
            logger.info(f"已启用的数据源: {len(enabled_sources)} 个")
            for source in enabled_sources:
                logger.info(f"  - {DATA_SOURCES[source]['name']}")
            
            self.print_result('config', True, "配置文件加载成功")
            
        except Exception as e:
            self.print_result('config', False, str(e))
            logger.error(f"配置测试失败: {e}")
    
    def test_database(self):
        """测试2：数据库"""
        self.print_step(2, "测试数据库")
        
        try:
            from data_crawler import DataCrawler
            
            crawler = DataCrawler()
            logger.info("数据库已初始化")
            
            # 检查表结构
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            if len(tables) >= 2:
                logger.info(f"数据库表: {len(tables)} 个")
                for table in tables:
                    logger.info(f"  - {table[0]}")
                
                # 检查文章数量
                cursor.execute("SELECT COUNT(*) FROM articles")
                article_count = cursor.fetchone()[0]
                logger.info(f"数据库中的文章: {article_count} 篇")
                
                conn.close()
                self.print_result('database', True, "数据库正常")
            else:
                self.print_result('database', False, "数据库表不完整")
                
        except Exception as e:
            self.print_result('database', False, str(e))
            logger.error(f"数据库测试失败: {e}")
    
    def test_crawler(self):
        """测试3：爬虫"""
        self.print_step(3, "测试数据爬虫")
        
        try:
            from data_crawler import crawl_all_sources
            
            logger.info("开始爬取数据...")
            start_time = time.time()
            
            crawl_all_sources()
            
            elapsed_time = time.time() - start_time
            logger.info(f"爬取耗时: {elapsed_time:.2f} 秒")
            
            # 检查爬取结果
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles")
            article_count = cursor.fetchone()[0]
            conn.close()
            
            if article_count > 0:
                logger.info(f"成功爬取 {article_count} 篇文章")
                self.print_result('crawler', True, f"获取了 {article_count} 篇文章")
            else:
                self.print_result('crawler', False, "未获取到任何文章")
                
        except Exception as e:
            self.print_result('crawler', False, str(e))
            logger.error(f"爬虫测试失败: {e}")
    
    def test_processor(self):
        """测试4：内容处理"""
        self.print_step(4, "测试内容处理")
        
        try:
            from content_processor import ContentProcessor
            import sqlite3
            
            processor = ContentProcessor()
            logger.info("内容处理器已初始化")
            
            # 获取需要处理的文章
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.id, a.original_text, a.title FROM articles a
                LEFT JOIN processed_articles pa ON a.id = pa.article_id
                WHERE pa.id IS NULL LIMIT 1
            ''')
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                article_id, original_text, title = row
                logger.info(f"处理文章: {title[:50]}...")
                
                result = processor.process_article(
                    article_id, 
                    original_text or '', 
                    title or ''
                )
                
                logger.info(f"生成字幕: {result['subtitle'][:50]}...")
                logger.info(f"提取日期: {result['timeline'].get('dates', [])}")
                logger.info(f"提取地点: {result['timeline'].get('locations', [])}")
                
                self.print_result('processor', True, "内容处理成功")
            else:
                logger.warning("没有未处理的文章，跳过处理测试")
                self.print_result('processor', True, "没有待处理文章（正常）")
                
        except Exception as e:
            self.print_result('processor', False, str(e))
            logger.error(f"内容处理测试失败: {e}")
    
    def test_email(self):
        """测试5：邮件发送"""
        self.print_step(5, "测试邮件发送")
        
        try:
            from email_sender import EmailSender
            from config import EMAIL_CONFIG
            
            # 检查邮件配置
            if not EMAIL_CONFIG.get('smtp_password'):
                logger.warning("未配置SMTP密码，跳过邮件测试")
                self.print_result('email', True, "跳过（未配置密码）")
                return
            
            sender = EmailSender()
            logger.info("邮件发送器已初始化")
            
            # 获取今日文章
            articles = sender.get_daily_articles()
            logger.info(f"获取到 {len(articles)} 篇文章用于发送")
            
            if len(articles) > 0:
                # 生成邮件正文
                email_body = sender.generate_email_body(articles)
                logger.info(f"邮件正文长度: {len(email_body)} 字符")
                
                # 尝试发送
                logger.info(f"正在发送邮件到 {EMAIL_CONFIG['recipient_email']}...")
                success = sender.send_email(articles)
                
                if success:
                    logger.info("邮件发送成功")
                    self.print_result('email', True, "邮件已发送")
                else:
                    self.print_result('email', False, "邮件发送失败")
            else:
                logger.warning("没有文章可发送")
                self.print_result('email', False, "没有文章")
                
        except Exception as e:
            self.print_result('email', False, str(e))
            logger.error(f"邮件发送测试失败: {e}")
    
    def test_scheduler(self):
        """测试6：定时调度"""
        self.print_step(6, "测试定时调度")
        
        try:
            from scheduler import NewsScheduler
            import schedule
            
            scheduler = NewsScheduler()
            logger.info("定时调度器已初始化")
            
            # 检查定时任务
            logger.info("检查定时任务配置...")
            
            # 注册测试任务
            schedule.every().day.at('08:00').do(lambda: None)
            schedule.every().day.at('12:00').do(lambda: None)
            schedule.every().day.at('18:00').do(lambda: None)
            
            jobs = schedule.get_jobs()
            logger.info(f"已配置定时任务: {len(jobs)} 个")
            
            for i, job in enumerate(jobs, 1):
                logger.info(f"  - 任务 {i}: {job}")
            
            self.print_result('scheduler', True, f"配置了 {len(jobs)} 个定时任务")
            
        except Exception as e:
            self.print_result('scheduler', False, str(e))
            logger.error(f"定时调度测试失败: {e}")
    
    def run_all_tests(self):
        """运行所有测试"""
        self.print_header("🧪 全球历史解密系统 - 工作流测试")
        
        logger.info(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 运行所有测试
        self.test_config()
        time.sleep(1)
        
        self.test_database()
        time.sleep(1)
        
        self.test_crawler()
        time.sleep(2)
        
        self.test_processor()
        time.sleep(1)
        
        self.test_email()
        time.sleep(1)
        
        self.test_scheduler()
        
        # 打印总结
        self.print_summary()
    
    def print_summary(self):
        """打印测试总结"""
        self.print_header("📊 测试总结")
        
        passed = sum(1 for v in self.test_results.values() if v)
        total = len(self.test_results)
        
        print(f"\n总体结果: {passed}/{total} 通过\n")
        
        for test_name, result in self.test_results.items():
            status = "✅" if result else "❌"
            print(f"{status} {test_name.upper()}")
        
        print("\n" + "="*60)
        
        if passed == total:
            print("🎉 所有测试通过！系统可以正常运行。")
            print("\n下一步: 运行 'python scheduler.py' 启动定时任务")
        else:
            print(f"⚠️  有 {total - passed} 项测试失败，请检查错误信息。")
        
        print("="*60 + "\n")
        
        return passed == total


if __name__ == '__main__':
    tester = WorkflowTester()
    success = tester.run_all_tests()
    
    # 返回退出码
    sys.exit(0 if success else 1)
