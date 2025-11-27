import re
import requests
from lxml import html
import time
from bs4 import BeautifulSoup
from datetime import datetime

# Local imports
from upload_to_feishu_form import get_access_token, append_data_to_table
from confidentials import *

ALBUM_URL = 'https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MjM5OTE0ODA2MQ==&action=getalbum&album_id=3349853949226418182'

# 自定义Headers，否则会触发风控
# 这里的Headers复制自Firefox
HEADERS = {
    # "Host": "mp.weixin.qq.com",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "DNT": "1",
    "Sec-GPC": "1",
    "Connection": "keep-alive",
    "Cookie": "rewardsn=; wxtokenkey=777",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    # "If-Modified-Since": "Tue, 11 Mar 2025 17:11:07 +0800",
    "Priority": "u=0, i"
}


def parse_tencent(url):
    """
    This function outputs content in everyday's document.
    Outputs a list that includes every piece of news
    Every piece of news is a dict.
    A dict consists of:
        title: str, title of news, w/o indices
        summaries: list of str, content of news (typically 3 paragraphs)
        link: link to original WeChat public article
    """

    # main_body_xpath = "/html/body/div[2]/div[2]/div[2]/div/div[1]/div[2]"  # 替换为实际的正文元素XPath
    main_body_xpath = "/html/body/div[2]/div[2]/div[2]/div/div[1]/div[3]" 
    # 获取网页内容
    response = requests.get(url, headers=HEADERS)
    with open("saved_page_debug.html", "w", encoding="utf-8") as file:
        file.write(response.text)
    doc = html.fromstring(response.content)
    
    # 定位正文元素
    main_body_element = doc.xpath(main_body_xpath)[0]
    current_news = None
    results = []
    
    # 预编译正则表达式
    title_pattern = re.compile(r'^[一二三四五六七八九十]、?\s*') # 匹配小标题。小标题以汉字序号开头
    num_pattern = re.compile(r'^\d+\.\s*') # 匹配摘要。这个公众号的摘要每段以阿拉伯数字序号开头
    url_pattern = re.compile(r'https?://mp\.weixin\.qq\.com/s/[\w-]+') # 匹配微信原文URL
    
    for element in main_body_element.xpath('./*'):
        visible_text = ''.join(element.itertext())
        
        if title_pattern.match(visible_text):
            current_news = {
                'title': re.sub(r'^[一二三四五六七八九十]、?\s*', '', visible_text),
                'summaries': [],
                'link': None
            }
        elif num_pattern.match(visible_text):
            current_news['summaries'].append(visible_text)
        elif url_pattern.match(visible_text):
            current_news['link'] = visible_text
            results.append(current_news)
            current_news = None
        
    return results

def gen_tencent_today_summary(news_list):
    # 整理标题并添加序号
    titles_with_numbers = ""
    for i, news in enumerate(news_list, 1):  # 从1开始计数
        titles_with_numbers += f"{i}. {news['title']}\n"

    # 获取当前时间的Unix时间戳（毫秒级）
    timestamp_ms = int(time.time() * 1000)
    # print(titles_with_numbers)
    return timestamp_ms, titles_with_numbers

def upload_tencent_overview(timestamp, overview_content, original_url):
    # Weave content:
    data_to_upload = [
        {
            "fields": {
                    "日期": timestamp,
                    "概览": overview_content,
                    "原文链接":  {
                        "link": original_url,
                        # "text": "文字"
                    }
                }
        }
    ]

    access_token = get_access_token()
    append_data_to_table(access_token, APP_TOKEN, OVERVIEW_TABLE_ID, data_to_upload)
    print('Uploaded overview successfully!')

def upload_tencent_details(timestamp, news_pieces):
    access_token = get_access_token()
    for i, piece in enumerate(news_pieces):
        # Weave content:
        data_to_upload = [
            {
                "fields": {
                        "提交日期": timestamp,
                        "标题": piece['title'],
                        "摘要": "".join(piece['summaries']),
                        "原文链接":  {
                            "link": piece['link'],
                            # "text": "文字"
                        }
                    }
            }
        ]

        append_data_to_table(access_token, APP_TOKEN, DETAIL_TABLE_ID, data_to_upload)
        print(f"Uploaded Tencent Newspiece #{i+1} successfully!")

def get_url_from_album():
    """
    获取今日的腾讯研究院推送，使用Album。
    Returns a string. 内容是今日推送的URL。
    """
    
    def get_today_date():
        # 获取当前日期
        today = datetime.now()
        # 格式化为YYYYMMDD
        date_str = today.strftime('%Y%m%d')
        return date_str
    
    today_date = get_today_date()
    target_string = f"腾讯研究院AI速递 {today_date}"
    target_string_else = f"腾讯研究院AI速递\xa0{today_date}"

    # 发送HTTP请求获取网页内容
    response = requests.get(url=ALBUM_URL, headers=HEADERS)
    response.raise_for_status()  # 检查请求是否成功
    html_content = response.text
    # with open("output.html", "w", encoding="utf-8") as file:
    #     file.write(response.text)

    # 使用BeautifulSoup解析HTML内容
    soup = BeautifulSoup(html_content, "html.parser")

    # 查找符合条件的所有元素
    elements = soup.find_all(attrs={"data-title": target_string})
    if len(elements) == 0:
        elements = soup.find_all(attrs={"data-title": target_string_else})
    target_element = elements[0] # 网页中的今日推送
    today_url_raw = target_element.get('data-link') 
    return today_url_raw
    
    # def decode_html(input_string):
    #     from html import unescape   
    #     output_string = unescape(input_string)
    #     return output_string
    
    # today_url_clean = decode_html(today_url_raw)
    # return today_url_clean

    # # 输出匹配到的元素
    # for element in elements:
    #     print(element)


if __name__ == "__main__":
    # target_url = "https://mp.weixin.qq.com/s?__biz=MjM5OTE0ODA2MQ==&mid=2650986350&idx=1&sn=176ae4573b7cb53fc01e3f27fba64b48&chksm=bcc9981c8bbe110a96ce69d217ee7504ee7b5b248107d865e3c50a7a4151cd7c58bfa3c8edab&scene=178&cur_album_id=3349853949226418182#rd"
    target_url = get_url_from_album()
    daily_news = parse_tencent(target_url)
    timestamp, titles_overview = gen_tencent_today_summary(daily_news)
    upload_tencent_overview(timestamp, titles_overview, target_url)
    upload_tencent_details(timestamp, daily_news)
    # print(daily_news)