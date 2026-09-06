"""
配置文件 - 数据源和内容比例设置
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============= 邮件配置 =============
EMAIL_CONFIG = {
    'sender_email': os.getenv('EMAIL_ADDRESS'),
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
    'smtp_password': os.getenv('SMTP_PASSWORD'),
    'recipient_email': os.getenv('EMAIL_ADDRESS'),
}

# ============= 内容分布配置 =============
CONTENT_DISTRIBUTION = {
    'politics': 5,      # 政治：5条
    'war': 5,          # 战争：5条
    'economy': 3,      # 经济：3条
    'society': 1,      # 社会：1条
    'technology': 1,   # 科技：1条
}

TOTAL_DAILY_ITEMS = sum(CONTENT_DISTRIBUTION.values())  # 总共15条

# ============= 数据源配置 =============
DATA_SOURCES = {
    'us_state_dept': {
        'name': '美国国务院解密文件库',
        'url': 'https://foia.state.gov/Search/Results.aspx',
        'enabled': True,
        'categories': ['politics', 'war', 'economy'],
    },
    'us_foia': {
        'name': '美国FOIA档案库',
        'url': 'https://www.foia.gov/',
        'enabled': True,
        'categories': ['politics', 'war', 'technology'],
    },
    'cia_foia': {
        'name': 'CIA解密文件库',
        'url': 'https://www.cia.gov/information-freedom/',
        'enabled': True,
        'categories': ['politics', 'war'],
    },
    'nsa_declassified': {
        'name': 'NSA解密文件库',
        'url': 'https://www.nsa.gov/news-features/declassified-documents/',
        'enabled': True,
        'categories': ['war', 'technology'],
    },
    'bbc_history': {
        'name': 'BBC历史档案',
        'url': 'https://www.bbc.com/history/',
        'enabled': True,
        'categories': ['politics', 'war', 'society'],
    },
    'history_com': {
        'name': 'History.com解密档案',
        'url': 'https://www.history.com/topics/world',
        'enabled': True,
        'categories': ['politics', 'war', 'society'],
    },
}

# ============= 爬虫配置 =============
CRAWLER_CONFIG = {
    'timeout': 30,
    'retry_count': 3,
    'retry_delay': 5,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'cache_dir': 'cache',
    'db_file': 'declassified_news.db',
}

# ============= 字幕生成配置 =============
SUBTITLE_CONFIG = {
    'max_length': 150,
    'model': 'gpt-3.5-turbo',
    'temperature': 0.7,
    'language': 'zh',
}

# ============= 时间线提取配置 =============
TIMELINE_CONFIG = {
    'extract_dates': True,
    'date_formats': ['YYYY-MM-DD', 'YYYY年MM月DD日', 'DD/MM/YYYY'],
    'extract_locations': True,
    'extract_persons': True,
}
