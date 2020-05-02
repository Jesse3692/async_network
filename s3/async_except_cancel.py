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
        loop.stop()
    finally:
        loop.close()


if __name__ == "__main__":
    main()
