import asyncio


async def work(loop, t):
    print('Start')
    await asyncio.sleep(t)
    print('after {}s stop'.format(t))
    loop.stop()  # 停止事件循环，stop后仍可以重新运行

loop = asyncio.get_event_loop()  # 创建事件循环
task = asyncio.ensure_future(work(loop, 1))  # 创建任务，该任务会自动加入事件循环
loop.run_forever()  # 无限运行事件循环，直至loop.stop停止
loop.close()  # 关闭事件循环，只有loop处于停止状态才会执行
