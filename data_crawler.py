"""
数据爬虫模块 - 从多个来源收集公开解密历史文件
"""
import requests
import sqlite3
import hashlib
from datetime import datetime
from typing import List, Dict
from bs4 import BeautifulSoup
import feedparser
import logging
from config import DATA_SOURCES, CRAWLER_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCrawler:
    """数据爬虫类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': CRAWLER_CONFIG['user_agent']})
        self.db_file = CRAWLER_CONFIG['db_file']
        self.init_database()
    
    def init_database(self):
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            content TEXT,
            source TEXT,
            category TEXT,
            publish_date TEXT,
            fetch_date TEXT,
            original_text TEXT,
            data_source TEXT
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS processed_articles (
            id TEXT PRIMARY KEY,
            article_id TEXT,
            subtitle_text TEXT,
            timeline TEXT,
            email_sent BOOLEAN DEFAULT 0,
            sent_date TEXT,
            FOREIGN KEY(article_id) REFERENCES articles(id)
        )''')
        
        conn.commit()
        conn.close()
    
    def fetch_from_source(self, source_key: str) -> List[Dict]:
        """从特定数据源获取文章"""
        source = DATA_SOURCES.get(source_key)
        if not source or not source['enabled']:
            return []
        
        logger.info(f"正在从 {source['name']} 获取数据...")
        articles = []
        
        try:
            if source_key == 'us_foia':
                articles = self._crawl_foia()
            elif source_key == 'bbc_history':
                articles = self._crawl_bbc()
            elif source_key == 'history_com':
                articles = self._crawl_history_com()
        except Exception as e:
            logger.error(f"从 {source['name']} 获取数据失败: {e}")
        
        return articles
    
    def _crawl_foia(self) -> List[Dict]:
        """爬取美国FOIA档案库"""
        articles = []
        try:
            url = "https://www.foia.gov/rss/all.xml"
            feed = feedparser.parse(url)
            
            for entry in feed.entries[:20]:
                article = {
                    'title': entry.get('title', ''),
                    'url': entry.get('link', ''),
                    'content': entry.get('summary', ''),
                    'source': 'FOIA',
                    'category': 'politics',
                    'original_text': entry.get('summary', ''),
                    'data_source': 'us_foia',
                    'publish_date': entry.get('published', datetime.now().isoformat()),
                }
                articles.append(article)
        except Exception as e:
            logger.error(f"爬取FOIA数据失败: {e}")
        
        return articles
    
    def _crawl_bbc(self) -> List[Dict]:
        """爬取BBC历史档案"""
        articles = []
        try:
            url = "https://www.bbc.com/history/"
            response = self.session.get(url, timeout=CRAWLER_CONFIG['timeout'])
            soup = BeautifulSoup(response.content, 'lxml')
            
            for item in soup.find_all('article')[:10]:
                title_elem = item.find('h2') or item.find('h3')
                link_elem = item.find('a')
                
                if title_elem and link_elem:
                    article = {
                        'title': title_elem.get_text(strip=True),
                        'url': link_elem.get('href', ''),
                        'source': 'BBC',
                        'category': 'society',
                        'original_text': item.get_text(strip=True)[:500],
                        'data_source': 'bbc_history',
                        'publish_date': datetime.now().isoformat(),
                    }
                    articles.append(article)
        except Exception as e:
            logger.error(f"爬取BBC数据失败: {e}")
        
        return articles
    
    def _crawl_history_com(self) -> List[Dict]:
        """爬取History.com解密档案"""
        articles = []
        try:
            url = "https://www.history.com/topics/world"
            response = self.session.get(url, timeout=CRAWLER_CONFIG['timeout'])
            soup = BeautifulSoup(response.content, 'lxml')
            
            for item in soup.find_all('div', class_='card')[:10]:
                title_elem = item.find('h3')
                link_elem = item.find('a')
                
                if title_elem and link_elem:
                    article = {
                        'title': title_elem.get_text(strip=True),
                        'url': link_elem.get('href', ''),
                        'source': 'History.com',
                        'category': 'war',
                        'original_text': item.get_text(strip=True)[:500],
                        'data_source': 'history_com',
                        'publish_date': datetime.now().isoformat(),
                    }
                    articles.append(article)
        except Exception as e:
            logger.error(f"爬取History.com数据失败: {e}")
        
        return articles
    
    def save_articles(self, articles: List[Dict]) -> int:
        """保存文章到数据库"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        saved_count = 0
        
        for article in articles:
            try:
                article_id = hashlib.md5(article['url'].encode()).hexdigest()
                
                cursor.execute('''INSERT OR IGNORE INTO articles 
                    (id, title, url, content, source, category, publish_date, fetch_date, original_text, data_source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                    article_id,
                    article.get('title', ''),
                    article.get('url', ''),
                    article.get('content', ''),
                    article.get('source', ''),
                    article.get('category', ''),
                    article.get('publish_date', ''),
                    datetime.now().isoformat(),
                    article.get('original_text', ''),
                    article.get('data_source', ''),
                ))
                saved_count += 1
            except Exception as e:
                logger.error(f"保存文章失败: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"成功保存 {saved_count} 篇文章")
        return saved_count


def crawl_all_sources():
    """爬取所有启用的数据源"""
    crawler = DataCrawler()
    
    for source_key in DATA_SOURCES.keys():
        articles = crawler.fetch_from_source(source_key)
        crawler.save_articles(articles)
    
    logger.info("所有数据源爬取完成")


if __name__ == '__main__':
    crawl_all_sources()
