import time
import asyncio

def one():
    start = time.time()
    @asyncio.coroutine
    def do_some_work():
        print('Start coroutine')
        time.sleep(0.1)
        print('This is a coroutine')
    loop = asyncio.get_event_loop()
    coroutine = do_some_work()
    loop.run_until_complete(coroutine)
    end = time.time()
    print('运行耗时：{:.4f}'.format(end - start))

if __name__ == "__main__":
    one()