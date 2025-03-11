import requests

# 飞书应用的App ID和App Secret
APP_ID = "cli_a74c7e36f0fe101c"
# APP_SECRET = "vXTakPKzgiQ5ofSPf2S2Gg70WEPjvTfy" # Dummy Secret, deprecated.
from confidentials import *

# 数据表的唯一标识
SPREADSHEET_TOKEN = "PLACEHOLDER_TOKEN"

TABLE_ID = 'tbl2mh1ztAHQv2W4'

# 获取访问令牌
def get_access_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }
    data = {
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        if result.get("code") == 0:
            return result.get("tenant_access_token")
    return None

# 上传数据到数据表
# def upload_data(access_token, data, spreadsheet_token):
    url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values_batch_update"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    # 假设数据从A1单元格开始写入
    request_body = {
        "value_input_option": "USER_ENTERED",
        "data": [
            {
                "range": "Sheet1!A1",
                "values": data
            }
        ]
    }
    response = requests.post(url, headers=headers, json=request_body)
    if response.status_code == 200:
        result = response.json()
        if result.get("code") == 0:
            print("数据上传成功")
        else:
            print(f"数据上传失败，错误信息：{result.get('msg')}")
    else:
        print(f"请求失败，状态码：{response.status_code}")


def append_data_to_table(app_access_token, app_token, table_id, data):
    """
    在飞书多维表格的数据表末尾按行追加数据

    :param app_access_token: 飞书应用的访问令牌
    :param table_id: 多维表格的数据表 ID
    :param data: 要追加的数据，格式为列表，每个元素是一个字典，表示一行数据
    :return: 响应结果
    """
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"

    headers = {
        "Authorization": f"Bearer {app_access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    payload = {
        "records": data
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # 检查响应状态码
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求出错: {e}")
        return None
    except ValueError as e:
        print(f"解析响应 JSON 出错: {e}")
        return None



# if __name__ == "__main__":
#     # 获取访问令牌
#     access_token = get_access_token()
#     if access_token:
#         # 示例数据
#         data = [
#             ["姓名", "年龄", "性别"],
#             ["张三", 25, "男"],
#             ["李四", 30, "女"]
#         ]
#         # 上传数据
#         upload_data(access_token, data, SPREADSHEET_TOKEN)
#     else:
#         print("获取访问令牌失败")

if __name__ == "__main__":
    # Get Access Token
    access_token = get_access_token()

    if access_token:
        # 定义要上传的三行数据
        data_to_append = [
            {
                "fields": {
                    "日期": 1740969600000,
                    "概览": "这是第一天的概览信息",
                    "原文链接":  {
                        "link": "https://example.com/day1",
                        # "text": "原文链接d1"
                    }
                }
            },
            {
                "fields": {
                    "日期": 1740969600,
                    "概览": "这是第二天的概览信息",
                    "原文链接": {
                        "link": "https://example.com/day2",
                        # "text": "原文链接d2"
                    }
                }
            },
            {
                "fields": {
                    "日期": 1735689600,
                    "概览": "这是第三天的概览信息",
                    "原文链接": {
                        "link": "https://example.com/day3",
                        # "text": "原文链接d3"
                    }
                }
            }
        ]
    app_token = 'X2S9bPrtMaaRX0srpZact0WTnNd'
    result = append_data_to_table(access_token, app_token, TABLE_ID, data_to_append)
    if result:
        print("数据追加成功:", result)
    else:
        print("数据追加失败")