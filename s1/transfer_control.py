# -*- encoding: utf-8 -*-
'''
@File    : transfer_control.py
@Time    : 2020/04/26 09:54:37
@Author  : Jesse Chang
@Contact : jessechang2358@gmail.com
@Version : 0.1
@License : Apache License Version 2.0, January 2004
@Desc    : 转移控制权
'''


from faker import Faker
from functools import wraps


# 预激协程装饰器
def coroutine(func):
    @wraps(func)
    def wrapper(*args, **kw):
        g = func(*args, **kw)
        next(g)
        return g

    return wrapper


# 子生成器函数这个生成器是真正做事的生成器
def sub_coro():
    sub_list = []  # 创建空列表
    while True:
        value = yield  # 调用方使用send方法发送数据并赋值给value变量
        if value == "CLOSE":  # 如果调用方发送的数据是CLOSE，终止循环
            break
        sub_list.append(value)  # 向列表添加数据
    return sorted(sub_list)  # 返回排序后的列表


# 使用预激协程装饰器
# 创建带有yield from 语句的父生成器函数
@coroutine
def sup_coro():
    # while True 可以多次循环，每次循环会创建一个新的子生成器()
    # 这里while只循环一次，创建两次sub_coro生成器
    # 这是由调用方，也就是main函数决定的
    # 这里之所以使用while循环，是因为避免父生成器终止并触发StopIteration异常
    while True:
        # yield from会自动预激子生成器sub_coro()
        # 所以sub_coro在定义时不可以使用预激协程装饰器
        # yield from将捕获子生成器终止时触发的StopIteration异常
        # 并将异常的value属性值赋值给等号前面的变量l
        # 也就是l变量的值等于sub_coro函数的return值
        # yield from 还实现了一个重要功能
        # 就是父生成器的send方法将发送值给子生成器
        # 并赋值给子生成器中yield语句等号前面的变量l
        sup_list = yield from sub_coro()
        print("排序后的列表 ", sup_list)
        print("--------------------------------")


# 调用父生成器的函数，也就调用方
def main():
    # 生成随机国家代号的方法
    fake = Faker().country_code
    # 嵌套列表，每个子列表中有三个随机国家代号（字符串）
    nest_country_list = [[fake() for i in range(3)] for j in range(3)]
    for country_list in nest_country_list:
        print("国家代号列表", country_list)
        c = sup_coro()  # 创建父生成器
        for country in country_list:
            c.send(country)  # 父生成器的send方法将国家代号发送给子生成器
        # CLOSE将终止子生成器中的while循环
        # 子生成器的return值将赋值给父生成器 yield from语句中等号前面的变量l
        c.send("CLOSE")


if __name__ == "__main__":
    main()
