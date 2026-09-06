import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 1. 检查并读取环境变量
email = os.environ.get('EMAIL_ADDRESS')
password = os.environ.get('SMTP_PASSWORD')

if not email or not password:
    print('❌ 错误：未获取到 EMAIL_ADDRESS 或 SMTP_PASSWORD 环境变量！')
    sys.exit(1)

# 写入 .env 供项目内部其他模块读取
with open('.env', 'w', encoding='utf-8') as f:
    f.write(f'EMAIL_ADDRESS={email}\nSMTP_PASSWORD={password}\n')

# 2. 执行爬虫逻辑并记录日志
log_messages = []
print('--- 正在运行爬虫 ---')

try:
    import data_crawler
    crawler = data_crawler.DataCrawler()
    if hasattr(crawler, 'init_db'):
        crawler.init_db()
    
    # 执行抓取
    if hasattr(crawler, 'run'):
        crawler.run()
    elif hasattr(crawler, 'crawl'):
        crawler.crawl()
    log_messages.append('<p style="color:green;">✅ 爬虫模块运行成功！</p>')
except Exception as e:
    err_info = f'❌ 爬虫模块运行报错: {e}'
    print(err_info)
    log_messages.append(f'<p style="color:red;">{err_info}</p>')

# 3. 执行内容处理逻辑
news_html = ''
try:
    import content_processor
    processor = content_processor.ContentProcessor()
    if hasattr(processor, 'get_latest_news_html'):
        news_html = processor.get_latest_news_html()
    elif hasattr(processor, 'get_latest_news'):
        news_html = processor.get_latest_news()
except Exception as e:
    err_info = f'❌ 内容生成模块报错: {e}'
    print(err_info)
    log_messages.append(f'<p style="color:red;">{err_info}</p>')

# 构造最终邮件正文（确保绝对不为空）
debug_info = "".join(log_messages)
if news_html:
    final_body = f'<h2>📰 今日新闻播报</h2>{news_html}<hr><h3>运行日志：</h3>{debug_info}'
else:
    final_body = f'<h2>⚠️ 自动推送诊断提醒</h2><p>新闻内容为空，以下是运行过程中的真实报错：</p>{debug_info}'

# 4. 强制使用 smtplib 直连发送
try:
    msg = MIMEMultipart()
    msg['From'] = email
    msg['To'] = email
    msg['Subject'] = '📬 每日新闻自动化推送（含诊断信息）'
    msg.attach(MIMEText(final_body, 'html', 'utf-8'))

    print('正在连接 Gmail SMTP...')
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email, password)
    server.sendmail(email, email, msg.as_string())
    server.quit()
    print('✅ 邮件已成功通过 smtplib 强制投递！')
except Exception as e:
    print('❌ SMTP 发送环节失败:', e)
    sys.exit(1)
