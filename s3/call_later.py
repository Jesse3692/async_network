import asyncio
import functools


def hello(name):
    print('[hello] Hello, {}'.format(name))


async def work(t, name):
    print('[work {}] start'.format(name))
    await asyncio.sleep(t)
    print('[work {}] stop'.format(name))


def main():
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(work(1, 'A'))
    loop.call_later(1.2, hello, 'Tom')
    loop.call_soon(hello, 'Kitty')
    task4 = loop.create_task(work(2, 'B'))
    loop.call_later(1, hello, 'Jerry')
    loop.run_until_complete(task4)


if __name__ == "__main__":
    main()
