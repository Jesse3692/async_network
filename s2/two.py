import time
import asyncio

def two():
    start = time.time()
    @asyncio.coroutine
    def do_some_work():
        print('Start coroutine')
        time.sleep(0.1)
        print('This is a coroutine')
    
    loop = asyncio.get_event_loop()
    coroutine = do_some_work()
    task = loop.create_task(coroutine)
    print('task是不是asyncio.Task的实例？', isinstance(task, asyncio.Task))
    print('Task state:', task._state)
    loop.run_until_complete(task)
    print('Task state:', task._state)

    end = time.time()
    print('运行耗时：{:.4f}'.format(end - start))