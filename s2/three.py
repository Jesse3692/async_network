import time
import asyncio
import functools


def three():
    start = time.time()
    # @asyncio.coroutine
    async def corowork():
        print('[corowork]Start coroutine')
        time.sleep(0.1)
        print('[corowork]This is a coroutine')

    def callback(name, task):
        print('[callback] Hello {}'.format(name))
        print('[callback] coroutine state: {}'.format(task._state))

    loop = asyncio.get_event_loop()
    coroutine = corowork()
    task = loop.create_task(coroutine)
    task.add_done_callback(functools.partial(callback, 'Jesse'))
    loop.run_until_complete(task)

    end = time.time()
    print('运行耗时：{:.4f}'.format(end - start))


if __name__ == '__main__':
    three()
