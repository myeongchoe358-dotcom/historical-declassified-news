import os
import sys

# 1. 自动生成 .env 配置
email = os.environ.get('EMAIL_ADDRESS')
password = os.environ.get('SMTP_PASSWORD')

if not email or not password:
    print('❌ 错误：未读取到 EMAIL_ADDRESS 或 SMTP_PASSWORD 环境变量！')
    sys.exit(1)

with open('.env', 'w', encoding='utf-8') as f:
    f.write(f'EMAIL_ADDRESS={email}\nSMTP_PASSWORD={password}\n')

# 2. 导入项目模块
try:
    import data_crawler
    import content_processor
    from email_sender import EmailSender
except Exception as e:
    print(f'❌ 导入模块失败: {e}')
    sys.exit(1)

print('--- 开始执行爬虫 ---')
try:
    crawler = data_crawler.DataCrawler()
    if hasattr(crawler, 'init_db'):
        crawler.init_db()
    
    # 动态匹配抓取函数
    for method in ['crawl', 'run', 'start', 'fetch_all', 'get_news']:
        if hasattr(crawler, method):
            print(f'调用爬虫方法: {method}()')
            getattr(crawler, method)()
            break
except Exception as e:
    print(f'⚠️ 爬虫过程抛出异常（继续尝试发信）: {e}')

print('--- 开始生成邮件内容 ---')
news_content = ''
try:
    processor = content_processor.ContentProcessor()
    for method in ['get_latest_news_html', 'get_latest_news', 'process', 'generate_html']:
        if hasattr(processor, method):
            print(f'调用内容处理方法: {method}()')
            news_content = getattr(processor, method)()
            break
except Exception as e:
    print(f'⚠️ 内容生成异常: {e}')

# 保底内容
if not news_content:
    news_content = '<h2>今日新闻播报</h2><p>爬虫已运行完毕，但未获取到新内容。</p>'

print('--- 开始发送邮件 ---')
sender = EmailSender()
sender.send_email(news_content)
print('✅ 邮件发送完毕！')
