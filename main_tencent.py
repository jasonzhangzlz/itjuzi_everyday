import re
import requests
from lxml import html

def parse_tencent(url):
    main_body_xpath = "/html/body/div[2]/div[2]/div[2]/div/div[1]/div[2]"  # 替换为实际的正文元素XPath
    # 获取网页内容
    response = requests.get(url)
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

# 使用示例
if __name__ == "__main__":
    target_url = "https://mp.weixin.qq.com/s?__biz=MjM5OTE0ODA2MQ==&mid=2650986350&idx=1&sn=176ae4573b7cb53fc01e3f27fba64b48&chksm=bcc9981c8bbe110a96ce69d217ee7504ee7b5b248107d865e3c50a7a4151cd7c58bfa3c8edab&scene=178&cur_album_id=3349853949226418182#rd"
    daily_news = parse_tencent(target_url)
    print(daily_news)