#!/usr/bin/python3
# -- coding: utf-8 --
# @Time : 2023/4/8 10:23
# -------------------------------
# cron "30 5 * * *" script-path=xxx.py,tag=匹配cron用
# const $ = new Env('阿里云盘签到');

import json
import requests
import os

# 变量export ali_refresh_token=''
ali_refresh_token = os.getenv("ali_refresh_token").split('&')
# refresh_token是一成不变的呢，我们使用它来更新签到需要的access_token
# refresh_token获取教程：https://github.com/bighammer-link/Common-scripts/wiki/%E9%98%BF%E9%87%8C%E4%BA%91%E7%9B%98refresh_token%E8%8E%B7%E5%8F%96%E6%96%B9%E6%B3%95
# 推送加
plustoken = os.getenv("plustoken")

# 日志函数
def log(message):
    print(message)

# 推送函数
def Push(contents):
    if not contents:
        log("无内容可推送")
        return
    try:
        headers = {'Content-Type': 'application/json'}
        data = {"token": plustoken, 'title': 'aliyun签到', 'content': contents.replace('\n', '<br>'), "template": "json"}
        resp = requests.post(f'http://www.pushplus.plus/send', json=data, headers=headers).json()
        log('push+推送成功' if resp.get('code') == 200 else 'push+推送失败')
    except Exception as e:
        log(f"推送时出现异常: {e}")

# 签到函数
def daily_check(access_token):
    try:
        url = 'https://member.aliyundrive.com/v1/activity/sign_in_list'
        headers = {
            'Authorization': access_token,
            'Content-Type': 'application/json'
        }
        response = requests.post(url=url, headers=headers, json={})
        response.raise_for_status()  # 检查请求是否成功
        result = response.json()
        sign_days = result['result']['signInCount']
        data = {
            'signInDay': sign_days
        }
        url_reward = 'https://member.aliyundrive.com/v1/activity/sign_in_reward'
        resp2 = requests.post(url=url_reward, headers=headers, data=json.dumps(data))
        resp2.raise_for_status()  # 检查请求是否成功
        result2 = resp2.json()
        if 'success' in result:
            log('签到成功')
            for i, j in enumerate(result['result']['signInLogs']):
                if j['status'] == 'miss':
                    day_json = result['result']['signInLogs'][i - 1]
                    if not day_json['isReward']:
                        contents = '签到成功，今日未获得奖励'
                    else:
                        contents = '本月累计签到{}天,今日签到获得{}{}'.format(
                            result['result']['signInCount'],
                            day_json['reward']['name'],
                            day_json['reward']['description']
                        )
                    log(contents)
                    return contents
    except requests.RequestException as e:
        log(f"签到请求出现异常: {e}")
    except (KeyError, json.JSONDecodeError) as e:
        log(f"解析响应数据时出现异常: {e}")
    return None

# 使用refresh_token更新access_token
def update_token(refresh_token):
    try:
        url = 'https://auth.aliyundrive.com/v2/account/token'
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        response = requests.post(url=url, json=data)
        response.raise_for_status()  # 检查请求是否成功
        access_token = response.json()['access_token']
        log('获取的access_token为{}'.format(access_token))
        return access_token
    except requests.RequestException as e:
        log(f"更新token请求出现异常: {e}")
    except (KeyError, json.JSONDecodeError) as e:
        log(f"解析响应数据时出现异常: {e}")
    return None

def main():
    for i, token in enumerate(ali_refresh_token, start=1):
        log(f'开始帐号{i}签到')
        log('更新access_token')
        access_token = update_token(token)
        if access_token:
            log('更新成功，开始进行签到')
            content = daily_check(access_token)
            if plustoken and content:
                Push(content)

if __name__ == '__main__':
    main()
