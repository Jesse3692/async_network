import asyncio
import functools
import time


def loop_stop(loop, future):  # 函数的最后一个参数须为future/task
    loop.stop()  # 停止事件循环，stop后仍可重新运行


async def work(t):
    print('Start')
    await asyncio.sleep(t)
    print('after {}s stop'.format(t))


def main():
    loop = asyncio.get_event_loop()  # 创建事件循环
    # 创建任务收集器，参数为任意数量的协程，任务收集器本身也是task/future对象
    tasks = asyncio.gather(work(1), work(2))  # 创建任务，该任务会自动加入事件循环
    # 任务收集器的add_done_callback方法添加回调函数
    # 当所有任务完成后，自动运行此回调函数
    # 注意，add_done_callback方法的参数是回调函数
    # 这里使用functools.partial方法创建偏函数以便将loop作为参数加入
    tasks.add_done_callback(functools.partial(loop_stop, loop))
    loop.run_forever()  # 无限运行事件循环，直至loop.stop停止
    loop.close()  # 关闭事件循环，只有loop处于停止状态才会执行


if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    print('运行耗时：{:.4f}'.format(end - start))
