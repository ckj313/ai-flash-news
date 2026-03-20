#!/usr/bin/env python3
"""生成 AI快报 GitHub Pages 网站"""

import json
import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from collections import defaultdict

RSS_URL = "https://tech.armyja-online.uk/rss"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FILE = os.path.join(OUTPUT_DIR, "template.html")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")
STATE_FILE = os.path.join(OUTPUT_DIR, "state.json")
TZ = timezone(timedelta(hours=8))


def fetch_rss(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8')


def parse_rss(xml_content):
    root = ET.fromstring(xml_content)
    articles = []
    for item in root.findall('.//item'):
        title = item.find('title')
        link = item.find('link')
        desc = item.find('description')
        pub_date = item.find('pubDate')
        
        # 解析日期
        date_str = pub_date.text if pub_date is not None else ''
        try:
            dt = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
            date_key = dt.astimezone(TZ).strftime('%Y-%m-%d')
        except:
            date_key = datetime.now(TZ).strftime('%Y-%m-%d')
        
        article = {
            'title': title.text.replace('<![CDATA[', '').replace(']]>', '') if title is not None else '',
            'link': link.text if link is not None else '',
            'description': desc.text.replace('<![CDATA[', '').replace(']]>', '') if desc is not None else '',
            'date': date_key
        }
        articles.append(article)
    return articles


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {'articles': [], 'last_update': ''}


def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def generate_html(articles_by_date):
    """生成 HTML 内容"""
    content_parts = []
    
    # 按日期倒序排列，只显示最近7天
    sorted_dates = sorted(articles_by_date.keys(), reverse=True)[:7]
    
    for date in sorted_dates:
        articles = articles_by_date[date]
        count = len(articles)
        
        # 日期格式化
        dt = datetime.strptime(date, '%Y-%m-%d')
        date_display = dt.strftime('%m月%d日 (%a)')
        date_display = date_display.replace('Mon', '一').replace('Tue', '二').replace('Wed', '三')
        date_display = date_display.replace('Thu', '四').replace('Fri', '五').replace('Sat', '六').replace('Sun', '日')
        
        articles_html = []
        for article in articles[:15]:  # 每天最多15篇
            desc = article['description'][:200] + '...' if len(article['description']) > 200 else article['description']
            articles_html.append(f'''
            <div class="article">
                <div class="article-title">
                    <a href="{article['link']}" target="_blank" rel="noopener">{article['title']}</a>
                </div>
                <div class="article-desc">{desc}</div>
            </div>''')
        
        content_parts.append(f'''
        <div class="day-section">
            <div class="day-header">
                <span class="day-date">{date_display}</span>
                <span class="day-count">{count} 篇</span>
            </div>
            {''.join(articles_html)}
        </div>''')
    
    return '\n'.join(content_parts)


def main():
    print(f"[{datetime.now(TZ).strftime('%Y-%m-%d %H:%M')}] 开始生成 AI快报...")
    
    # 获取 RSS
    try:
        xml_content = fetch_rss(RSS_URL)
    except Exception as e:
        print(f"获取RSS失败: {e}")
        return
    
    # 解析文章
    articles = parse_rss(xml_content)
    print(f"获取到 {len(articles)} 篇文章")
    
    # 加载状态
    state = load_state()
    existing_links = {a['link'] for a in state.get('articles', [])}
    
    # 合并新旧文章
    all_articles = state.get('articles', [])
    for article in articles:
        if article['link'] not in existing_links:
            all_articles.append(article)
    
    # 只保留最近30天
    cutoff = (datetime.now(TZ) - timedelta(days=30)).strftime('%Y-%m-%d')
    all_articles = [a for a in all_articles if a['date'] >= cutoff]
    
    # 按日期分组
    articles_by_date = defaultdict(list)
    for article in all_articles:
        articles_by_date[article['date']].append(article)
    
    # 生成 HTML
    content_html = generate_html(articles_by_date)
    update_time = datetime.now(TZ).strftime('%Y-%m-%d %H:%M')
    
    # 读取模板
    with open(TEMPLATE_FILE, 'r') as f:
        template = f.read()
    
    # 替换占位符
    html = template.replace('{{CONTENT}}', content_html)
    html = html.replace('{{UPDATE_TIME}}', update_time)
    
    # 写入文件
    with open(OUTPUT_FILE, 'w') as f:
        f.write(html)
    
    # 保存状态
    state['articles'] = all_articles
    state['last_update'] = update_time
    save_state(state)
    
    print(f"生成完成！更新时间: {update_time}")


if __name__ == "__main__":
    main()