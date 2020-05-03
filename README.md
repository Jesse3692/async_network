# Python 异步网络并发编程

## 从线程到协程

### 相关知识

#### 多进程和多线程

我们常见的操作系统（Windows，Linux，MacOS），都是支持多进程的多核操作系统。**所谓多进程**，就是操作系统可以同时执行多个任务。在操作系统中，每个任务就是一个进程。在同一个进程中有多个线程运行就是多线程。

一个 CPU 在某一时刻只能做一项任务，即在一个进程（或线程）中工作，当它闲置时，会被系统派到其他进程中。单核计算机也可以实现多进程，原理是时间片轮转，也就是进程切换。但是什么时候进行进程、线程切换是由操作系统决定的，**无法人为干预**。

#### 线程安全

在 python 多线程中，变量是共享的，这也是相较多进程的一个优点，线程占用资源要少的多，但也导致多个 CPU 同时操作多个线程时会引起结果无法预测的问题，也就是说 Python 的线程是不安全的。

#### GIL 全局解释器锁

由于上面提到线程是不安全的，那么怎么解决呢？CPython 解释器使用了加锁的方式：每个进程有一把锁，启动线程先加锁，结束线程释放锁，也就是 GIL（Global Interperter Lock）全局解释器锁，在任意时刻解释器中只有一个线程，这样就保证了线程的安全性。当然 GIL 的存在有很多其他益处，包括简化 CPython 解释器和大量扩展的实现。

GIL 实现了线程操作的安全性，但多线程的效率被大打折扣。

注意，GIL 不是语言特性，而是解释器的设计特点，有些 Python 解释器就没有 GIL（JPython），其他语言比如 Ruby 也有 GIL 设计。

#### 多线程提高工作效率

Python 的多线程在某些情况下是可以成倍提高程序的运行速度的，像是爬虫等网络 I/O 比较多的工作。

在爬虫这个场景中，CPU 做的事就是发起页面请求和处理响应数据，这两步是极快的，中间网络传输数据的过程是耗时且不占用 CPU 的。像这种情况，CPU 再多也没用，一个 CPU 抽空就能完成整个任务了，毕竟程序中需要 CPU 完成的工作并不多。

这样就涉及到复杂程序的分类了：

- CPU 密集型
- I/O 密集型

爬虫程序就是 I/O 密集型程序，而 CPU 密集型的程序是需要 CPU 不停运转的。

**模拟爬虫的网络 I/O**
主要代码实现：

```python
import time
import threading


def crawl_url():  # 模拟爬虫操作
    time.sleep(0.2)  # 模拟网络的I/O


def main1():
    # 模拟单线程
    for i in range(100):
        crawl_url()


def main2():
    # 模拟多线程
    thread_list = []
    for _ in range(100):
        t = threading.Thread(target=crawl_url)
        t.start()
        thread_list.append(t)
    for t in thread_list:
        t.join()
```

[完整代码-模拟网络爬虫中的 I/O 操作以及单线程和多线程的简单应用](./s1/thread.py)

运行结果:

```python
单线程爬虫耗时：20.0000
多线程爬虫耗时：0.2490
```

从运行结果上看，单线程（main1）的运行时间是多线程（mian2）运行时间的 100 倍，考虑到多线程创建、切换的开销，这个结果也是相当可观的，I/O 操作耗时越长，多线程的威力越大。

#### 异步和同步、阻塞和非阻塞

上面的爬虫示例中，单线程中的 for 循环运行 100 次爬取网页的操作，只有前一个执行完后一个才能执行，这就是同步的概念，而在爬虫函数内部的 I/O 操作为阻塞操作，线程无法向下执行。

多线程中的第一个 for 循环是，是创建 100 个线程并启动，这个操作是非阻塞的，不会等一个线程执行完再创建下一个线程，它是一口气创建 100 个线程并启动；而第二个 for 循环是将主线程挂起，直到所有的子线程完成，测试的主线程就是阻塞的，这种的程序运行的方式就是异步，CPU 在遇到 I/O 阻塞的时候不会在那一直等待的，而是被操作系统派往其他线程看看有没有可做的。

所谓的异步，就是 CPU 在当前线程阻塞时可以去其他线程中工作，不管怎么设计，在一个线程内部的代码都是顺序执行的，遇到 I/O 都得阻塞，所谓的非阻塞就是当前线程遇到阻塞时，CPU 去其他线程工作。

### 协程初步

在多线程程序中，线程切换是由操作系统决定的，无法人为干预。上文中的爬虫示例中各个线程间无关联，没有先后顺序，不涉及相互引用，耦合性为零，这种场景下是非常适合多线程的。

**协程**是在线程的基础上编写由程序员决定代码执行顺序、可以相互影响的高耦合度代码的一种高级程序设计模式。

上文说到`不论如何设计，在一个线程内部，代码都是顺序执行的，遇到I/O都会阻塞`，直到出现了协程，这句话就成了伪命题。一个线程中可以有多个协程，当一个协程遇到 I/O 阻塞时，就可以手动的控制 CPU 去另一个协程中工作，此外连创建线程和切换线程的开销都省了。

#### 生成器原理

```python
In [1]: def fibo(n):
   ...:     a, b = 0, 1
   ...:     while b < n:
   ...:         a, b = b, a + b
   ...:         yield a
   ...:

In [2]: f = fibo(100)


In [3]: print(f)

<generator object fibo at 0x7f1b35624ba0>

In [4]: f

Out[4]: <generator object fibo at 0x7f1b35624ba0>

In [5]: for i in f:
   ...:     print(i)
   ...:

1
1
2
3
5
8
13
21
34
55
89
```

函数体内部有 yield 关键字的都是生成器函数，所以这里 fibo 是生成器函数。yield 关键字只能出现在函数中，生成器函数的执行结果是生成器，注意这里所讲的“执行结果”不是函数的 return 值。生成器终止时必定抛出 StopIteration 异常，而 for 循环可以捕获，异常的 value 属性值为生成器函数的 return 值。

生成器还可以用 next 方法迭代。生成器会在 yield 语句处暂停，这是至关重要的，未来协程中的 I/O 阻塞就出现在这里。

#### 生成器进化成协程

生成器是由迭代器进化而来的，所以生成器对象有`__iter__`和`__next__`方法，可以使用 for 循环获得值，注意这里所说的“获得值”指的是下文代码块中 yield 语句中 yield 关键字后面的 i。

这是在 python2.5 时出现的特性，在 python3.3 中出现 yield from 语法之前，生成器没有太大用处。但此时 yield 关键字还是实现了一些特性，而且至关重要，就是生成器对象有 send、throw 和 close 方法。这三个方法的作用分别是发送数据给生成器并赋值给 yield 语句、向生成器抛入异常由生成器内部处理、终止生成器，有这三个方法后才能使得生成器进化为协程。

**生成器（或协程）有四种存在状态：**

- GEN_CREATED 创建完成，等待执行
- GEN_RUNNING 解释器正在执行（这个状态一般观察不到）
- GEN_SUSPENDED 在 yield 表达式处暂停
- GEN_CLOSE 执行结束，生成器停止

**生成器的生命周期：**

```python
In [1]: import inspect

In [2]: def generator():
   ...:     i = "激活生成器"
   ...:     while True:
   ...:         try:
   ...:             value = yield i
   ...:         except ValueError:
   ...:             print("Over")
   ...:         i = value
   ...:

In [3]: g = generator()

In [4]: inspect.getgeneratorstate(g)

Out[4]: 'GEN_CREATED'

In [5]: next(g)

Out[5]: '激活生成器'

In [6]: inspect.getgeneratorstate(g)

Out[6]: 'GEN_SUSPENDED'

In [7]: g.send("Hello Generator")

Out[7]: 'Hello Generator'

In [8]: g.throw(ValueError)

Over
Out[8]: 'Hello Generator'

In [9]: g.close()

In [10]: inspect.getgeneratorstate(g)

Out[11]: 'GEN_CLOSED'
```

**代码说明如下：**

1. `g = generator()` 创建生成器

2. `inspect.getgeneratorstate(g)` 查看生成器状态

3. `next(g)` 预激生成器（或协程），这是必须要做的。在生成器创建完成后，需要将其第一次运行到 yield 语句处暂停。

4. `g.send("Hello Generator")` 暂停状态的生成器可以使用 send 方法发送数据，此方法的参数就是 yield 表达式的值，也就是 yield 表达式等号前面的 value 变量的值直接变成了“HelloGenerator”，继续向下执行完一次 while 循环，变量 i 被赋值，继续运行下一次循环，yield 表达式弹出变量 i

5. `g.throw(ValueError)` 向生成器抛入异常，异常会被 try except 捕获，作进一步处理

6. `g.close()` close 方法终止生成器，异常不会被抛出

   因为生成器的调用方也就是程序员自己可以控制生成器的启动、暂停、终止，而且可以向生成器内部传入数据，所以这种生成器又叫协程，generator 函数既可以叫做生成器函数，也可以叫做协程函数，这是生成器向协程的过渡阶段。

#### 预激协程

预先激活生成器（或协程）可以使用 next 方法，也可以使用生成器的 send 方法发送 None 值：g.send(None)。为简化协程的使用，我们可以尝试编写一个装饰器来预激协程，这样创建的协程会立即进入 GEN_SUSPENDED 状态，可以直接使用 send 方法。

```python
In [1]: from functools import wraps

In [2]: def coroutine(func):  # 预激协程装饰器
   ...:     @wraps(func)  # wraps装饰器保证func函数的签名不被修改
   ...:     def wrapper(*args, **kw):
   ...:         g = func(*args, **kw)
   ...:         next(g)  # 预激协程
   ...:         return g  # 返回激活后的协程
   ...:     return wrapper
   ...:


In [3]: @coroutine  # 使用装饰器重新创建协程函数
   ...: def generator():
   ...:     i = '激活生成器'
   ...:     while True:
   ...:         try:
   ...:             value = yield i
   ...:         except ValueError:
   ...:             print('Over')
   ...:         i = value
   ...:


In [4]: g = generator()


In [5]: import inspect

In [6]: inspect.getgeneratorstate(g)

Out[6]: 'GEN_SUSPENDED'
```

#### 协程的返回值

前文“生成器原理”这一小节中提到了`StopIteration`异常的 value 属性值为生成器（协程）函数的 return 值，我们可以在使用协程时捕获这个异常并得到这个值。

```python
In [8]: @coroutine
   ...: def generator():
   ...:     l = []
   ...:     while True:
   ...:         value = yield
   ...:         if value == 'CLOSE':
   ...:             break
   ...:         l.append(value)
   ...:     return l
   ...:

In [9]: g = generator()

In [10]: g.send('hello')

In [11]: g.send('coroutine')

In [12]: g.send('CLOSE')

---------------------------------------------------------------------------
StopIteration                             Traceback (most recent call last)
<ipython-input-12-863c90462435> in <module>
----> 1 g.send('CLOSE')

StopIteration: ['hello', 'coroutine']
```

**代码说明如下：**

1. `l = []`创建列表，保存协程 send 方法每次发送的参数
2. `value = yield` yield 表达式不弹出值，仅作暂停之用
3. `if value == 'CLOSE':` 如果 send 方法的参数为 CLOSE，break 终止 while 循环，停止生成器，抛出 StopIteration 异常
4. `l.append(value)` 将 value 添加到列表
5. `return l` 设置协程函数的返回值，该值在协程终止抛出 StopIteration 异常时赋值给 value 赋值

**可以这样捕获异常：**

```python
In [13]: g = generator()

In [14]: for i in('hello', 'coroutine', 'CLOSE'):
    ...:     try:
    ...:         g.send(i)
    ...:     except StopIteration as e:
    ...:         value = e.value
    ...:         print('END')
    ...:

END

In [15]: value

Out[15]: ['hello', 'coroutine']
```

### 使用 yield from

python3.3 中新增了 yield from 语法，这是全新的语言结构，是 yield 的升级版。相比 yield 该语法有两大优势：避免嵌套循环、转移控制权

#### 避免嵌套循环

python 内置模块`itertools`是十分强大的，里面有很多实用的方法，其中有一个是 chain 方法，它可以接收任意数量的可迭代对象作为参数，返回一个包含所有参数中的元素的迭代器。

```python
In [1]: from itertools import chain

In [2]: c = chain({'one', 'two'}, list('ace'))

In [3]: c
Out[3]: <itertools.chain at 0x7f151c5b2dd8>

In [4]: for i in c:
   ...:     print(i)
   ...:

one
two
a
c
e
```

接下来我们使用 yield 关键字来实现 chain 方法:

注意这里 chain_yield 函数的返回值是生成器

```python
In [5]: def chain_yield(*args):
   ...:     for iter_obj in args:
   ...:         for i in iter_obj:
   ...:             yield i
   ...:

In [6]: c = chain_yield({'one', 'two'}, list('ace'))

In [7]: c
Out[7]: <generator object chain_yield at 0x7f151c5b65c8>

In [8]: for i in c:
   ...:     print(i)
   ...:

one
two
a
c
e
```

下面我们使用 python3.3 新增的 yield from 语法优化上下文的 chain 函数。

```python
In [9]: def chain_yield_from(*args):
   ...:     for iter_obj in args:
   ...:         yield from iter_obj
   ...:

In [10]: c = chain({'one', 'two'}, list('ace'))

In [11]: c

Out[11]: <itertools.chain at 0x7f151d28c8d0>

In [12]: c = chain_yield_from({'one', 'two'}, list('ace'))

In [13]: c

Out[13]: <generator object chain_yield_from at 0x7f151d2b7728>

In [14]: for i in c:
    ...:     print(i)
    ...:

one
two
a
c
e
```

可以看到 yield from 语句可以替代 for 循环，避免了嵌套循环。同 yield 一样，yield from 语句也只能出现在函数体内部，有 yield from 语句的函数叫做协程函数或生成器函数。

yield from 后面接收一个可迭代对象，例如上面代码中的`iter_obj`变量，在协程中，可迭代对象往往是协程对象，这样就形成了嵌套协程。

#### 转移控制权

转移控制权是 yield from 语法的核心功能，也是从生成器进化到协程的重要一步。

首先安装伪造数据的 faker 库，在终端执行`pip install faker`

下面举例说明转移控制权的功能，示例是一个将列表进行排序的程序。

```python
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

```

运行结果如下：

```python
国家代号列表 ['KP', 'NR', 'KN']
排序后的列表  ['KN', 'KP', 'NR']
--------------------------------
国家代号列表 ['GE', 'MT', 'GN']
排序后的列表  ['GE', 'GN', 'MT']
--------------------------------
国家代号列表 ['CY', 'CO', 'AE']
排序后的列表  ['AE', 'CO', 'CY']
--------------------------------
```

所谓的“转移控制权”就是 yield from 语法可以将子生成器的控制权交给调用方 main 函数，在 main 函数内部创建父生成器 c，控制 c.send 方法传值给子生成器。这是一个巨大的进步，在此基础上，python3.4 新增了创建协程的装饰器，这样非生成器函数的协程函数就正式出现了。

## asynciomo 模块

Python 之父龟叔在 Python 仓库之外开发了一个新项目，旨在解决 Python 异步编程的诸多问题，他把这个项目的代号命名为“Tulip”郁金香。Python3.4 把 Tulip 添加到标准库中时，将其命名为 asyncio。

### asyncio 模块简介

#### 协程装饰器

在 Python3.4 中，asyncio 模块出现，此时创建协程函数必须使用 asyncio.coroutine 装饰器标记。此前包含 yield from 语句的函数既可以称作生成器函数也可以称作协程函数，为了突出协程的重要性，现在使用 asyncio.coroutine 装饰器的函数就是真正的协程函数了。

#### 任务和事件循环

在 asyncio 模块中出现了一些新的概念，有 coroutine 协程、task 任务，event_loop 事件循环

**coroutine 协程**，协程对象，使用 asyncio.coroutine 装饰器装饰的函数被称作协程函数，它的调用不会立即执行函数而是返回一个协程对象，即协程函数的运行结果为协程对象，注意这里说的“运行结果”不是 return 值。协程对象需要包装成任务注入到事件循环，由事件循环调用。

**task 任务**将协程对象作为参数创建任务，任务是对协程对象的进一步封装，其中包含任务的各种状态。

**event_loop 事件循环**可以将多线程类比为工厂中的多个车间，而协程就是车间中的多台机器。在线程级程序中，一个车间只能有一台机器启动，要想提高工作效率，可以启动多个车间中的机器；而在协程程序中，一个车间中的不同机器可以同时运转，启动机器、暂停运转、延时启动、停止机器等操作都可以人为设置。

事件循环能够控制任务运行流程，也就是任务的调用方。

#### 一个简单的例子

下面这个例子中只是简单的写了一个协程的例子，使用`time.sleep(0.1)`模拟了`I/O`操作。

```python
In [1]: import time

In [2]: import asyncio

   ...:     start = time.time()
   ...:     @asyncio.coroutine
   ...:     def do_some_work():
   ...:         print('Start coroutine')
   ...:         time.sleep(0.1)
   ...:         print('This is a coroutine')
   ...:     loop = asyncio.get_event_loop()
   ...:     coroutine = do_some_work()
   ...:     loop.run_until_complete(coroutine)
   ...:     end = time.time()
   ...:     print('运行耗时：{:.4f}'.format(end - start))
   ...:

In [4]: one()
Start coroutine
This is a coroutine
运行耗时：0.1008
```

**代码说明：**

- `@asyncio.coroutine`是协程装饰器，被它装饰的是协程函数；
- `time.sleep(0.1)`是模拟的 I/O 操作；
- `loop = asyncio.get_event_loop()`是创建事件循环（每个线程中只能有一个事件循环，get_event_loop 方法会获取当前已经存在的事件循环，如果当前线程中没有，则新建一个）；
- `coroutine = do_some_work()`调用协程函数获取协程对象；
- `loop.run_until_complete(coroutine)`是将协程对象注入到事件循环，协程的运行由事件循环控制。事件的循环`run_until_complete`方法会阻塞运行，直到任务全部完成。协程对象作为`run_until_complete`方法的参数，loop 会自动将协程对象包装成任务来运行。

#### 协程的任务状态

协程对象不能直接运行，必须放入事件循环中或者由 yield from 进行调用。将协程对象注入事件循环的时候，其实是 run_until_complete 方法将协程对象包装成一个 task 任务对象，任务对象保存了协程运行后的状态用于未来获取协程的结果。

下面的示例中，主要是创建一个任务对象以及任务对象的状态查看

```python
In [1]: import time

In [2]: import asyncio

   ...:         time.sleep(0.1)
   ...:         print('This is a coroutine')
   ...:     loop = asyncio.get_event_loop()
   ...:     coroutine =do_some_work()
   ...:     task = loop.create_task(coroutine)
   ...:     print('task是不是asyncio.Task的实例？ ', isinstance(task, asyncio.Task))
   ...:     print('Task state:', task._state)
   ...:     loop.run_until_complete(task)
   ...:     print('Task state:', task._state)
   ...:     end = time.time()
   ...:     print('运行耗时：{:.4f}'.format(end - start))
   ...:

In [4]: two()
task是不是asyncio.Task的实例？  True
Task state: PENDING
Start coroutine
This is a coroutine
Task state: FINISHED
运行耗时：0.1006
```

**代码说明如下：**

- `task = loop.create_task(coroutine)`使用事件循环的 create_task 方法创建任务对象

- `print('task是不是asyncio.Task的实例？', isinstance(task, asyncio.Task))` task 是 asyncio.Task 类的实例，那么为什么使用协程对象创建任务？这是因为在这个过程中 asyncio.Task 做了一些工作，其中包括预激协程、协程运行中遇到异常时的处理

- `print('Task state:', task._state)` 查看任务对象的状态，task 对象的\_state 属性保存当前任务的运行状态，任务的运行状态有`PENDING`和`FINISHED`两种

- `loop.run_until_complete(task)` 将任务对象注入到事件循环中

### async 和 await 关键字

在 Python3.5 中新增了`async`和`await`关键字来定义协程函数。这两个关键字是一个组合，其作用等同于`@asyncio.coroutine`装饰器和 yield from 语句，此后协程与生成器就彻底泾渭分明了。

#### 绑定回调

为什么要进行回调的绑定？因为协程中肯定包含一个 IO 操作，等它处理完数据之后，我们希望得到通知，以便下一步数据处理，而这一需求可以通过向 future 对象中添加回调来实现。那什么是 future 对象？task 对象就是 future 对象，我们可以这样认为：因为 asyncio.Task 是 asyncio.Future 的子类，所以 task 对象可以添加回调函数。

回调函数的最后一个参数是 future 或 task 对象，通过该对象可以获取协程返回值。如果回调需要多个参数，可以通过偏函数导入。

简言之，一个任务完成后需要捎带运行的代码可以放到回调函数中：

```python
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

(async_network) [root@VM_0_16_centos async_network]# python -u "/home/jesse/async_network/s2/three.py"
[corowork]Start coroutine
[corowork]This is a coroutine
[callback] Hello Jesse
[callback] coroutine state: FINISHED
运行耗时：0.1008
```

**代码说明如下:**

- `async def corowork():`中使用 async 关键字替代`asyncio.coroutine`装饰器来创建协程函数。

- `def callback(name, task):`这是定义的回调函数，协程终止后需要顺便运行的代码，回调函数的参数有要求，最后一个位置参数必须为 task 对象。

- `task.add_done_callback(functools.partial(callback, 'Jesse'))`task 对象的 add_done_callback 方法可以添加回调函数，注意参数必须是回调函数，这个方法不能传入回调函数的参数，得通过 functools 模块的 partial 方法解决：将回调函数和其参数 name 作为 partial 方法的参数，而返回值就是偏函数，偏函数可作为 task.add_done_callback 方法的参数

#### 协程多任务

实际项目中，往往有多个协程创建多个任务对象，同时在一个 loop 里运行。为了把多个协程交给 loop，需要借助`asyncio.gather`方法。任务的 result 方法可以获得对应的协程函数的 return 值。

相应的代码如下：

```python
import time
import asyncio
import functools


def four():
    start = time.time()
    async def corowork(name, t):
        print('[corowork] Start coroutine', name)
        await asyncio.sleep(t)
        print('[corowork] Stop coroutine', name)
        return 'Coroutine {} OK'.format(name)

    loop = asyncio.get_event_loop()
    coroutine1 = corowork('ONE', 3)
    coroutine2 = corowork('TWO', 1)
    task1 = loop.create_task(coroutine1)
    task2 = loop.create_task(coroutine2)
    gather = asyncio.gather(task1, task2)
    loop.run_until_complete(gather)
    print('[task1]', task1.result())
    print('[task2]', task2.result())

    end = time.time()
    print('运行耗时：{:.4f}'.format(end - start))


if __name__ == '__main__':
    four()

(async_network) [root@VM_0_16_centos async_network]# python -u "/home/jesse/async_network/s2/four.py"
[corowork] Start coroutine ONE
[corowork] Start coroutine TWO
[corowork] Stop coroutine TWO
[corowork] Stop coroutine ONE
[task1] Coroutine ONE OK
[task2] Coroutine TWO OK
运行耗时：3.0032
```

**代码说明如下:**

- `await asyncio.sleep(t)`中`await`关键字等同于 Python3.4 中的 yield from 语句，后面接协程对象。`asyncio.sleep`方法的返回值为协程对象，这一步为阻塞运行。`asyncio.sleep`与`time.sleep()`是不同的，前者阻塞当前协程，即 corowork 函数的运行，而`time.sleep()`会阻塞整个线程，所以这里必须使用前者，阻塞当前协程，系统可以调度 CPU 可以在线程内的其它协程中运行。

将异步的时间休眠换成同步的后，协程代码将变成同步。

```Python
time.sleep(t)

(async_network) [root@VM_0_16_centos async_network]# python -u "/home/jesse/async_network/s2/four.py"
[corowork] Start coroutine ONE
[corowork] Stop coroutine ONE
[corowork] Start coroutine TWO
[corowork] Stop coroutine TWO
['Coroutine ONE OK', 'Coroutine TWO OK']
运行耗时：4.0050
```

- `return 'Coroutine {} OK'.format(name)`协程函数的 return 值可以在协程运行结束后保存到对应的 task 对象的 result 方法中。

- 创建两个协程对象，在协程内部分别阻塞 3 秒和 1 秒。

- 创建两个任务对象

- `gather = asyncio.gather(task1, task2)`中`asyncio.gather`方法将任务对象作为参数，创建任务收集器。注意，`asyncio.gather`方法中参数的顺序决定了协程的启动顺序。

- `loop.run_until_complete(gather)`，将任务收集器作为参数传入事件循环的`run_until_complete`方法，阻塞运行，直到全部任务完成。

- `print('[task1]', task1.result())` 任务结束后，事件循环停止，打印任务的 result 方法返回值，即协程函数的 return 值。

**额外说明的几点**:

- 多数情况下无需调用 task 的 add_done_callback 方法，可以直接把回调函数中的代码写入 await 语句的后面，协程是可以暂停和恢复的。

- 多数情况下同样无需调用 task 的 result 方法获取协程函数的 return 值，因为事件循环的 run_until_complete 方法的返回值就是协程函数的 return 值。修改上文的代码如下：

```python
result = loop.run_until_complete(gather)
print(result)

(async_network) [root@VM_0_16_centos async_network]# python -u "/home/jesse/async_network/s2/four.py"
[corowork] Start coroutine ONE
[corowork] Start coroutine TWO
[corowork] Stop coroutine TWO
[corowork] Stop coroutine ONE
['Coroutine ONE OK', 'Coroutine TWO OK']
运行耗时：3.0033
```

- 事件循环有一个 stop 方法用来停止循环和一个 close 方法用来关闭循环。以上示例中都没有调用 loop.close 方法，似乎并没有什么问题。所以到底要不要调用 loop.close 呢？简单来说，loop 只要不关闭，就还可以再次运行 run_until_complete 方法，关闭后则不可以运行。有人会建议调用 loop.close，彻底清理 loop 对象防止误用，其实多数情况下根本没有这个必要。

- asyncio 模块提供了 asyncio.gather 和 asyncio.wait 两个任务收集方法，它们的作用相同，都是将协程任务按顺序排定，再将返回值作为参数加入到事件循环中。前者在上文已经用到，后者与前者的区别是它可以获取任务的执行状态（PENDING & FINISHED），当有一些特别的需求例如在某些情况下取消任务，可以使用 asyncio.wait 方法。

## asyncio 异步编程

基于 Python 生成器实现异步的模块不止 asyncio，还有 gevent、greenlet 等模块。

### 取消任务

在事件循环启动之后停止之前，我们可以手动取消任务的执行，注意只有 PENDING 状态的任务才能被取消，FINISHED 状态的任务已经完成，不能取消。

#### 事件循环的 cancel 方法

```python
import asyncio
import time


async def work(id, t):
    print('Working...')
    await asyncio.sleep(t)
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


(async_network) [root@VM_0_16_centos async_network]# python -u "/home/jesse/async_network/s3/async_cancel.py"
Working...
Working...  # 遇到IO阻塞，释放CPU，CPU到下一个协程中运行
Working...  # 以上步骤瞬间完成，这时候的loop中全部协程处于阻塞状态
Work 1 done
Work 2 done
Work 3 done  #
```

**代码说明**:

- 创建一个列表，列表中有三个协程对象那个，协程内部分别阻塞 1-3 秒

- 程序运行过程中，快捷键`Ctrl + C`会触发`KeyboardInterrupt`异常。代码捕获异常，在程序终止前完成异常抛出和异常结束中的代码。

- 事件循环的 stop 方法取消所有未完成的任务，停止事件循环。

- 关闭事件循环

#### task 的 cancel 方法

任务的 cancel 方法也可以取消任务，而 asyncio.Task.all_tasks 方法可以获得事件循环中的全部任务。修改上文代码中的 main 函数如下：

```python
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

(async_network) [root@VM_0_16_centos async_network]# python -u "/home/jesse/async_network/s3/async_cancel.py"
Working...
Working...
Working...
Work 1 done
^C
取消任务： <Task pending coro=<work() running at /home/jesse/async_network/s3/async_cancel.py:7> wait_for=<Future pending cb=[<TaskWakeupMethWrapper object at 0x7f802f4eca08>()]> cb=[gather.<locals>._done_callback(2)() at /usr/lib64/python3.6/asyncio/tasks.py:622]> PENDING
取消状态: True PENDING
取消任务： <Task pending coro=<work() running at /home/jesse/async_network/s3/async_cancel.py:7> wait_for=<Future pending cb=[<TaskWakeupMethWrapper object at 0x7f802f4eca38>()]> cb=[gather.<locals>._done_callback(1)() at /usr/lib64/python3.6/asyncio/tasks.py:622]> PENDING
取消状态: True PENDING
取消任务： <Task finished coro=<work() done, defined at /home/jesse/async_network/s3/async_cancel.py:5> result=None> FINISHED
取消状态: False FINISHED
```

**代码说明**:

- 每个线程里只能有一个事件循环，此方法可以获得事件循环中的所有任务的集合，任务的状态有 PENDING 和 FINISHED 两种

- 任务的 cancel 方法可以取消未完成的任务，取消成功返回 True，已完成的任务取消失败返回

### 排定任务

排定 task/future 在事件循环中的执行顺序，也就是对应的协程先执行哪个，遇到 IO 阻塞时，CPU 转而运行哪个任务，这是我们在运行异步编程时一个需求。前文所示的多任务程序中，事件循环里的任务的执行顺序由`asyncio.ensure_future`、`loop.create_task`和`asyncio.gather`排定，这一节介绍 loop 的其他方法。

#### loop.run_forever 无限运行事件循环

事件循环的 run_until_complete 方法运行事件循环，当其中的全部任务完成后，自动停止事件循环；run_forever 方法为无限运行事件循环，需要自定义 loop.stop 方法并执行之后才会停止。

```Python
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

(async_network) [root@VM_0_16_centos async_network]# python -u "/home/jesse/async_network/s3/run_forever.py"
Start
after 1s stop
```

以上是单任务事件循环，将 loop 作为参数传入协程函数创建协程，在协程内部执行 loop.stop 方法停止事件循环。

下面是多任务事件循环，使用回调函数执行 loop.stop 停止事件循环，修改代码如下：

```Python
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


(async_network) [root@VM_0_16_centos async_network]# python -u "/home/jesse/async_network/s3/run_forever_callback.py"
Start
Start
after 1s stop
after 2s stop
运行耗时：2.0022
```

loop.run_until_complete 方法本身也是调用 loop.run_forever 方法，然后通过回调函数调用 loop.stop 方法实现的。

#### loop.call_soon 排定普通函数到事件循环

事件循环的 call_soon 方法可以将普通函数作为任务加入到事件循环并立即排定任务的执行顺序。

```python
import asyncio
import time


def hello(name):
    """普通函数"""
    print('[hello] Hello, {}'.format(name))


async def work(t, name):
    """协程函数"""
    print('[work] start', name)
    await asyncio.sleep(t)
    print('[work] {} after {}s stop'.format(name, t))


def main():
    loop = asyncio.get_event_loop()
    # 向事件循环中添加任务
    asyncio.ensure_future(work(1, 'A'))  # 第一个执行
    # call_soon将普通函数作为task加入到事件循环并排定执行顺序
    # 该方法的第一个参数为普通函数名字，普通函数的参数写在后面
    loop.call_soon(hello, 'Tom')         # 第二个执行
    # 向事件循环中添加任务
    loop.create_task(work(2, 'B'))       # 第三个执行
    # 阻塞启动事件循环，顺便再添加一个任务
    loop.run_until_complete(work(3, 'C'))  # 第四个执行


if __name__ == "__main__":
    main()

(async_network) [root@VM_0_16_centos async_network]# python -u "/home/jesse/async_network/s3/call_soon.py"
[work] start A
[hello] Hello, Tom
[work] start B
[work] start C
[work] A after 1s stop
[work] B after 2s stop
[work] C after 3s stop
```

#### asyncio.call_later 排定普通函数并异步延时调用

此方法同 loop.call_soon 一样，可将普通函数作为任务放到事件循环里，不同之处在于此方法可延时执行，第一个参数作为延时时间。

```python
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


(async_network) [root@VM_0_16_centos async_network]# python -u "/home/jesse/async_network/s3/call_later.py"
[work A] start  # 执行任务①，打印以上内容，阻塞一秒；然后执行任务②，阻塞一点二秒
[hello] Hello, Kitty  # 执行任务③，打印以上内容
[work B] start  # 执行任务④，打印以上内容，阻塞两秒；然后执行任务⑤，阻塞一秒
[hello] Hello, Jerry  # 阻塞结束 call_later这个延时一秒是事件循环启动时就开始计时的，所以比任务①先执行
[work A] stop  # 阻塞结束 接着执行任务①
[hello] Hello, Tom  # 阻塞结束 接着执行任务②
[work B] stop  # 阻塞结束 接着执行任务④
```

**call_later 的阻塞计时是从事件循环启动时开始计算的**。

#### loop.call_at & loop.time 排定普通任务并异步指定时刻调用

- call_soon 立刻执行，call_later 延时执行，call_at 在某时刻执行

- loop.time 就是事件循环内部的一个计时方法，返回值是时刻，数据类型是 float

修改以上`call_later.py`代码如下：

```python
def main():
    loop = asyncio.get_event_loop()
    start = loop.time()
    asyncio.ensure_future(work(1, 'A'))
    # loop.call_later(1.2, hello, 'Tom')
    loop.call_at(start+1.2, hello, 'Tom')
    loop.call_soon(hello, 'Kitty')
    task4 = loop.create_task(work(2, 'B'))
    # loop.call_later(1, hello, 'Jerry')
    loop.call_at(start+1, hello, 'Jerry')
    loop.run_until_complete(task4)
```

此代码的运行结果与`call_later.py`代码一致。

这三个 call_xxx 方法的作用都是将普通函数作为任务排定到事件循环中，返回值都是 asyncio.events.TimerHandle 实例，注意它们不是协程任务，不能作为 loop.run_until_complete 的参数。
