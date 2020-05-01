import time
import asyncio
import functools


def four():
    start = time.time()
    async def corowork(name, t):
        print('[corowork] Start coroutine', name)
        # await asyncio.sleep(t)
        time.sleep(t)
        print('[corowork] Stop coroutine', name)
        return 'Coroutine {} OK'.format(name)
    
    loop = asyncio.get_event_loop()
    coroutine1 = corowork('ONE', 3)
    coroutine2 = corowork('TWO', 1)
    task1 = loop.create_task(coroutine1)
    task2 = loop.create_task(coroutine2)
    gather = asyncio.gather(task1, task2)
    result = loop.run_until_complete(gather)
    # print('[task1]', task1.result())
    # print('[task2]', task2.result())
    print(result)

    end = time.time()
    print('运行耗时：{:.4f}'.format(end - start))


if __name__ == '__main__':
    four()
