import asyncio
import time


async def work(id, t):
    print('Working...')
    await asyncio.sleep(t)
    # time.sleep(t)
    print('Work {} done'.format(id))


def main():
    loop = asyncio.get_event_loop()
    coroutines = [work(i, i) for i in range(1, 4)]
    try:
        loop.run_until_complete(asyncio.gather(*coroutines))
    except KeyboardInterrupt:
        print()
        # 每个线程里只能有一个事件循环
        # 此方法可以获得事件循环中的所有任务的集合
        # 任务的状态有 PENDING和FINISHED两种
        tasks = asyncio.Task.all_tasks()
        for i in tasks:
            # 任务的cancel方法可以取消未完成的任务
            # 取消成功返回True，已完成的任务返回取消失败
            print('取消任务： {}'.format(i), i._state)
            print('取消状态: {}'.format(i.cancel()), i._state)
        
    finally:
        loop.close()


if __name__ == "__main__":
    main()
