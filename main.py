# -*- coding: utf-8 -*-
# @Time    : 2021/1/25 16:00
# @Author  : qiuqc@mail.ustc.edu.cn
# @FileName: ustc抢课.py

import requests
import threading
import time
import json
import random
from config import *

url = "https://jw.ustc.edu.cn/ws/for-std/course-select/add-request"
drop_url = 'https://jw.ustc.edu.cn/ws/for-std/course-select/add-drop-response'
all_class_url = "https://jw.ustc.edu.cn/ws/for-std/course-select/addable-lessons"

class_dict = {}

sss = """authority: jw.ustc.edu.cn
method: POST
path: /ws/for-std/course-select/add-request
scheme: https
accept: */*
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7
cache-control: no-cache
content-type: application/x-www-form-urlencoded; charset=UTF-8
cookie: {}
origin: https://jw.ustc.edu.cn
pragma: no-cache
referer: https://jw.ustc.edu.cn/for-std/course-select/{}/turn/{}/select
sec-ch-ua: "Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"
sec-ch-ua-mobile: ?0
sec-fetch-dest: empty
sec-fetch-mode: cors
sec-fetch-site: same-origin
user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36
x-requested-with: XMLHttpRequest""".format(cookie, student_id, turn_id)
dp_row_header = """authority: jw.ustc.edu.cn
method: POST
path: /ws/for-std/course-select/add-drop-response
scheme: https
accept: */*
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7
cache-control: no-cache
content-type: application/x-www-form-urlencoded; charset=UTF-8
cookie: {}
origin: https://jw.ustc.edu.cn
pragma: no-cache
referer: https://jw.ustc.edu.cn/for-std/course-select/{}/turn/{}/select
sec-ch-ua: "Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"
sec-ch-ua-mobile: ?0
sec-fetch-dest: empty
sec-fetch-mode: cors
sec-fetch-site: same-origin
user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36
x-requested-with: XMLHttpRequest""".format(cookie, student_id, turn_id)

def deal_row(s):
    return {i.split(": ")[0].strip(): i.split(": ")[1] for i in s.split("\n")}

headers = deal_row(sss)
dp_headers = deal_row(dp_row_header)

def get_allclass():
    try:
        c = requests.post(all_class_url, headers=headers, data={"turnId": turn_id, "studentId": student_id})
        c.raise_for_status()
        all_data = json.loads(c.text)
        for each in all_data:
            class_dict[each["code"]] = each["id"], each["course"].get("nameZh", "")
        # print("可用课程：", class_dict)  # 调试：打印可用课程
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"获取课程列表失败：{e}")
        class_dict.clear()

def ppp(course_id, index):
    attempt = 0
    if course_id not in class_dict:
        print(f"错误：课程代码 {course_id} 未在可选课程中找到。")
        return False
    while True:
        try:
            form_d = """studentAssoc: {}
            lessonAssoc: {}
            courseSelectTurnAssoc: {}
            scheduleGroupAssoc: 
            virtualCost: 0""".format(student_id, class_dict[course_id][0], turn_id)
            form_data = deal_row(form_d)
            c = requests.post(url, headers=headers, data=form_data)
            c.raise_for_status()
            # print(f"课程 {course_id} 的 add-request 响应：{c.text}, HTTP 状态码：{c.status_code}")
            dp_form_row = """studentId: {}
            requestId: {}"""
            dp_form_data = deal_row(dp_form_row.format(student_id, c.text))
            d = requests.post(drop_url, headers=dp_headers, data=dp_form_data)
            d.raise_for_status()
            # print(f"课程 {course_id} 的 drop_url 响应：{d.text}, HTTP 状态码：{d.status_code}")
            try:
                data = json.loads(d.text)
                if data is None:
                    print(f"课程 {course_id} 返回 null 响应，可能是服务器限流或错误")
                    attempt += 1
                    time.sleep(random.uniform(2, 3))  # 随机延迟 2-3 秒
                    continue
                if data["success"]:
                    print("恭喜你， {}选课成功！！！！".format(class_dict[course_id][1]))
                    return True
                else:
                    print("{}选课失败 TAT : {}".format(class_dict[course_id][1], data["errorMessage"]["text"]))
                    attempt += 1
                    time.sleep(random.uniform(2, 3))
            except json.JSONDecodeError as e:
                print(f"课程 {course_id} JSON 解析错误：{e}，响应内容：{d.text}")
                attempt += 1
                time.sleep(random.uniform(2, 3))
        except requests.RequestException as e:
            print(f"课程 {course_id} 网络错误：{e}")
            attempt += 1
            time.sleep(random.uniform(2, 3))

if __name__ == "__main__":
    threads = []
    get_allclass()
    # print("要抢的课程：", course_ids)  # 调试：打印目标课程
    for i in range(len(course_ids)):
        task = threading.Thread(target=ppp, args=(course_ids[i], i))
        threads.append(task)
        task.start()
    for task in threads:
        task.join()
    print("全部抢完")