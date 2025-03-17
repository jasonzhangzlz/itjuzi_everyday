import re
import requests
from lxml import html
import time
import sys

# Local imports
from upload_to_feishu_form import get_access_token, append_data_to_table
from confidentials import *

CONTENT_MATCH_KEYWORDS = ['人工智能','大数据','AI','大模型','RAG', '搜索', '推荐','知识库','记忆', 'GENAI']

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


def parse_itjuzi(url):
    """
    outputs lists of itjuzi content.
    each content is a dict.
    """


    # 获取网页内容
    response = requests.get(url, headers=HEADERS)
    with open("saved_page_debug_itjuzi.html", "w", encoding="utf-8") as file:
        file.write(response.text)
    doc = html.fromstring(response.content)


    # 提取文字
    def get_text(doc_, xpath, debug_msg):
        """
        Input: 
        doc_: an html object
        xpath: (str) xpath of target content

        Extract element by xpath, then extract all text (including children, grandchildren, ...) in the element.
        
        Outputs a list of string containing all texts.
        """
        element = doc_.xpath(xpath)[0]
        # main_body_text = main_body_element.text_content()
        visible_text = [
            text.strip() 
            for text in element.xpath('.//text()') 
            if text.strip()
        ]
        with open("tmp_itjuzi_extracted", "a", encoding="utf-8") as file:
            file.write(f'\n\n*** [{debug_msg}], XPath: {xpath}***\n')
            file.write('\n'.join(visible_text))
        return visible_text
    
    # main_body_xpath = "/html/body/div[2]/div[2]/div[2]/div/div[1]/div[2]"
    domestic_xpath = '/html/body/div[2]/div[2]/div[2]/div/div[1]/div[2]/fieldset[2]/fieldset[1]'
    international_xpath = '/html/body/div[2]/div[2]/div[2]/div/div[1]/div[2]/fieldset[2]/fieldset[2]/section'
    domestic_content_list = get_text(doc, domestic_xpath,'DOMESTIC')[1:] # 首个元素是“国内投资速递”，丢弃之
    intl_content_list = get_text(doc, international_xpath, 'INTERNATIONAL')[1:]
    
    def organize_text(text_list, match_keywords=True):
        """
        Input: 
        text_list: list of str. contains itjuzi contents
        match_keywords: if set to true, then start matching keywords.

        Output: 
        A list of ITJuzi newspieces
        """

        def get_common_prefix(a, b):
            """获取两个字符串的最长公共前缀"""
            min_len = min(len(a), len(b))
            for i in range(min_len):
                if a[i] != b[i]:
                    return a[:i]
            return a[:min_len]

        # 识别序号的位置
        indices = [i for i, s in enumerate(text_list) if re.match(r'^\d+\.\s*$', s.strip())]
        
        # 分割为多个条目
        entries = []
        for i in range(len(indices)):
            start = indices[i]
            end = indices[i+1] if i < len(indices)-1 else len(text_list)
            entries.append(text_list[start:end])
        
        result = []
        for entry in entries:
            if len(entry) < 2:
                continue
            
            serial = entry[0]
            title = entry[1]
            desc_parts = []
            
            # 处理不同条目格式
            if len(entry) >= 4:
                name = entry[2]
                desc_parts = entry[3:]
            else:
                # 合并介绍部分并提取姓名
                desc_parts = entry[2:] if len(entry) >= 3 else []
                title_start = title.strip()
                desc_first = desc_parts[0].strip() if desc_parts else ''
                
                # 计算最长公共前缀
                name = get_common_prefix(title_start, desc_first)
            
            # 拼接介绍内容
            description = ''.join(desc_parts)
            def find_keywords(sentence, keywords):
                lower_sentence = sentence.lower()
                found_keywords = []
                for keyword in keywords:
                    if keyword.lower() in lower_sentence:
                        found_keywords.append(keyword)
                return found_keywords
            
            if match_keywords:
                keywords_matched_list = find_keywords(description, CONTENT_MATCH_KEYWORDS)

            else:
                keywords_matched_list = []

            result.append({
                # "序号": serial,
                "title": title,
                "name_company": name,
                "description": description,
                "keywords": keywords_matched_list,
            })
        
        return result

    domestic_organized = organize_text(domestic_content_list, match_keywords=True)
    intl_organized = organize_text(intl_content_list, match_keywords=False)

    timestamp_ms = int(time.time() * 1000)
    access_token = get_access_token()

    # 上传第一个（总列表）
    def upload_overview(original_url, input_data):
        overview_content = ''

        # Generate Overview Summary
        for i, news in enumerate(input_data,1):
            # Input data is a list of newspieces
            if len(news['keywords'])>0:
                # Matched keywords 
                joined_kw = ','.join(news['keywords'])
                str_to_append = f'{i}. **{news["title"]}, 匹配项: {joined_kw}** \n'
            else:
                str_to_append = f'{i}. {news["title"]} \n'
            overview_content += str_to_append

        # Weave content:
        data_to_upload = [
            {
                "fields": {
                        "日期": timestamp_ms,
                        "概览": overview_content,
                        "原文链接":  {
                            "link": original_url,
                            # "text": "文字"
                        }
                    }
            }
        ]

        append_data_to_table(access_token, JUZI_APP_TOKEN, JUZI_OVERVIEW_TABLE_ID, data_to_upload)
        print('Uploaded ITJUZI Overview Successfully! :)')

    upload_overview(url, domestic_organized+intl_organized)


    # 上传第二个（分列表）
    def upload_details(original_url, input_data):
        for i, piece in enumerate(input_data,1):
            if len(piece['keywords'])==0:
                # We only upload target companies (keyword-matched)
                print(f"ITJUZI Piece #{i} Skipped. Company: {piece['name_company']}")
                continue

            # Weave content:
            data_to_upload = [
                {
                    "fields": {
                            "发布日期": timestamp_ms,
                            "企业": piece['name_company'],
                            "概要": piece['description'],
                            "原文链接":  {
                                "link": original_url,
                                # "text": "文字"
                            },
                            "匹配项": ','.join(piece['keywords'])
                        }
                }
            ]
            append_data_to_table(access_token, JUZI_APP_TOKEN, JUZI_DETAIL_TABLE_ID, data_to_upload)
            print(f"Uploaded ITJuzi piece #{i} successfully! Company: {piece['name_company']}")

    upload_details(url, domestic_organized)
    return 0


if __name__ == '__main__':
    # url = "https://mp.weixin.qq.com/s?__biz=MjM5ODIwNzUyMw==&mid=2650506037&idx=1&sn=ead6ed9f98198eed84db2785a31ed232&chksm=bfdccf827c7306e696adfc5d93d994d98c9ff44cb0ade9f85b68685c41c8c5475c636ebfb4b8#rd"
    url = sys.argv[1]
    print(url)
    exit_code = parse_itjuzi(url)
    print(f'Exit code: {exit_code}')
