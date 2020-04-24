# -*- encoding: utf-8 -*-
'''
@File    : thread.py
@Time    : 2020/04/24 14:42:13
@Author  : Jesse Chang
@Contact : jessechang2358@gmail.com
@Version : 0.1
@License : Apache License Version 2.0, January 2004
@Desc    : None
'''

import time
import threading


def crawl_url():  # 模拟爬虫操作
    time.sleep(0.2)  # 模拟网络的I/O


def main1():
    # 模拟单线程
    for i in range(100):
        crawl_url()


def main2():
    # 模拟多线程
    thread_list = []
    for _ in range(100):
        t = threading.Thread(target=crawl_url)
        t.start()
        thread_list.append(t)
    for t in thread_list:
        t.join()


if __name__ == "__main__":
    start = time.time()
    main1()
    end = time.time()
    print("单线程爬虫耗时：{:.4f}".format(end - start))

    start = time.time()
    main2()
    end = time.time()
    print("多线程爬虫耗时：{:.4f}".format(end - start))
