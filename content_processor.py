"""
内容处理模块 - 生成字幕文案和提取事件时间线
"""
import re
import sqlite3
import json
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentProcessor:
    """内容处理器类"""
    
    def __init__(self):
        self.db_file = 'declassified_news.db'
        self.date_patterns = [
            r'(\d{4}年\d{1,2}月\d{1,2}日)',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{1,2}-\d{1,2})',
        ]
        self.location_keywords = ['中国', '美国', '俄罗斯', '欧洲', '日本', '韩国', '英国', '法国', '印度', '越南']
    
    def generate_subtitle(self, article_id: str, original_text: str) -> str:
        """生成短视频字幕文案"""
        try:
            sentences = self._extract_key_sentences(original_text, max_sentences=3)
            subtitle = '【历史解密】\n'
            for sentence in sentences:
                if len(subtitle) < 150:
                    subtitle += sentence + '\n'
            
            subtitle = re.sub(r'<[^>]+>', '', subtitle)
            subtitle = re.sub(r'\n+', '\n', subtitle).strip()
            
            logger.info(f"为文章 {article_id} 生成字幕")
            return subtitle
        except Exception as e:
            logger.error(f"生成字幕失败: {e}")
            return original_text[:150]
    
    def extract_timeline(self, original_text: str) -> Dict:
        """提取事件时间线"""
        timeline = {
            'dates': [],
            'locations': [],
            'key_events': []
        }
        
        try:
            timeline['dates'] = self._extract_dates(original_text)
            timeline['locations'] = self._extract_locations(original_text)
            timeline['key_events'] = self._extract_key_events(original_text)
            logger.info(f"提取时间线: {len(timeline['dates'])} 个日期")
        except Exception as e:
            logger.error(f"提取时间线失败: {e}")
        
        return timeline
    
    def _extract_dates(self, text: str) -> List[str]:
        """提取日期信息"""
        dates = []
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        return list(set(dates))[:5]
    
    def _extract_locations(self, text: str) -> List[str]:
        """提取地点信息"""
        locations = []
        for location in self.location_keywords:
            if location in text:
                locations.append(location)
        return list(set(locations))
    
    def _extract_key_sentences(self, text: str, max_sentences: int = 3) -> List[str]:
        """提取关键句子"""
        sentences = re.split(r'[。！？\.\!\?]', text)
        valid_sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        key_sentences = sorted(valid_sentences, key=len, reverse=True)[:max_sentences]
        return key_sentences
    
    def _extract_key_events(self, text: str) -> List[Dict]:
        """提取关键事件"""
        events = []
        event_keywords = ['战争', '签署', '宣布', '发生', '爆发', '结束', '建立', '成立']
        
        for keyword in event_keywords:
            if keyword in text:
                sentences = re.split(r'[。！？]', text)
                for sentence in sentences:
                    if keyword in sentence:
                        event = {
                            'event': sentence.strip()[:100],
                            'keyword': keyword,
                        }
                        events.append(event)
                        break
        
        return events[:5]
    
    def save_processed_content(self, article_id: str, subtitle: str, timeline: Dict) -> bool:
        """保存处理后的内容"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''INSERT OR REPLACE INTO processed_articles
                (id, article_id, subtitle_text, timeline)
                VALUES (?, ?, ?, ?)''', (
                article_id,
                article_id,
                subtitle,
                json.dumps(timeline, ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"保存处理内容失败: {e}")
            return False
    
    def process_article(self, article_id: str, original_text: str, title: str) -> Dict:
        """完整处理一篇文章"""
        subtitle = self.generate_subtitle(article_id, original_text)
        timeline = self.extract_timeline(original_text)
        self.save_processed_content(article_id, subtitle, timeline)
        
        return {
            'article_id': article_id,
            'title': title,
            'subtitle': subtitle,
            'timeline': timeline,
            'processed_at': datetime.now().isoformat()
        }
