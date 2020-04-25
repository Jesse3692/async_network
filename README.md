# Python异步网络并发编程

## 从线程到协程

### 多进程和多线程

我们常见的操作系统（Windows，Linux，MacOS），都是支持多进程的多核操作系统。**所谓多进程**，就是操作系统可以同时执行多个任务。在操作系统中，每个任务就是一个进程。在同一个进程中有多个线程运行就是多线程。

一个CPU在某一时刻只能做一项任务，即在一个进程（或线程）中工作，当它闲置时，会被系统派到其他进程中。单核计算机也可以实现多进程，原理是时间片轮转，也就是进程切换。但是什么时候进行进程、线程切换是由操作系统决定的，**无法人为干预**。

### 线程安全

在python多线程中，变量是共享的，这也是相较多进程的一个优点，线程占用资源要少的多，但也导致多个CPU同时操作多个线程时会引起结果无法预测的问题，也就是说Python的线程是不安全的。

### GIL全局解释器锁

由于上面提到线程是不安全的，那么怎么解决呢？CPython解释器使用了加锁的方式：每个进程有一把锁，启动线程先加锁，结束线程释放锁，也就是GIL（Global Interperter Lock）全局解释器锁，在任意时刻解释器中只有一个线程，这样就保证了线程的安全性。当然GIL的存在有很多其他益处，包括简化CPython解释器和大量扩展的实现。

GIL实现了线程操作的安全性，但多线程的效率被大打折扣。

注意，GIL不是语言特性，而是解释器的设计特点，有些Python解释器就没有GIL（JPython），其他语言比如Ruby也有GIL设计。

### 多线程提高工作效率

Python的多线程在某些情况下是可以成倍提高程序的运行速度的，像是爬虫等网络I/O比较多的工作。

在爬虫这个场景中，CPU做的事就是发起页面请求和处理响应数据，这两步是极快的，中间网络传输数据的过程是耗时且不占用CPU的。像这种情况，CPU再多也没用，一个CPU抽空就能完成整个任务了，毕竟程序中需要CPU完成的工作并不多。

这样就涉及到复杂程序的分类了：

- CPU密集型
- I/O密集型

爬虫程序就是I/O密集型程序，而CPU密集型的程序是需要CPU不停运转的。

**模拟爬虫的网络I/O**

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

[完整代码-模拟网络爬虫中的I/O操作以及单线程和多线程的简单应用](./s1/thread.py)

运行结果:

```python
单线程爬虫耗时：20.0000
多线程爬虫耗时：0.2490
```

从运行结果上看，单线程（main1）的运行时间是多线程（mian2）运行时间的100倍，考虑到多线程创建、切换的开销，这个结果也是相当可观的，I/O操作耗时越长，多线程的威力越大。

### 异步和同步、阻塞和非阻塞

上面的爬虫示例中，单线程中的for循环运行100次爬取网页的操作，只有前一个执行完后一个才能执行，这就是同步的概念，而在爬虫函数内部的I/O操作为阻塞操作，线程无法向下执行。

多线程中的第一个for循环是，是创建100个线程并启动，这个操作是非阻塞的，不会等一个线程执行完再创建下一个线程，它是一口气创建100个线程并启动；而第二个for循环是将主线程挂起，直到所有的子线程完成，测试的主线程就是阻塞的，这种的程序运行的方式就是异步，CPU在遇到I/O阻塞的时候不会在那一直等待的，而是被操作系统派往其他线程看看有没有可做的。

所谓的异步，就是CPU在当前线程阻塞时可以去其他线程中工作，不管怎么设计，在一个线程内部的代码都是顺序执行的，遇到I/O都得阻塞，所谓的非阻塞就是当前线程遇到阻塞时，CPU去其他线程工作。

### 协程初步

在多线程程序中，线程切换是由操作系统决定的，无法人为干预。上文中的爬虫示例中各个线程间无关联，没有先后顺序，不涉及相互引用，耦合性为零，这种场景下是非常适合多线程的。

**协程**是在线程的基础上编写由程序员决定代码执行顺序、可以相互影响的高耦合度代码的一种高级程序设计模式。

上文说到`不论如何设计，在一个线程内部，代码都是顺序执行的，遇到I/O都会阻塞`，直到出现了协程，这句话就成了伪命题。一个线程中可以有多个协程，当一个协程遇到I/O阻塞时，就可以手动的控制CPU去另一个协程中工作，此外连创建线程和切换线程的开销都省了。

### 生成器原理

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

函数体内部有yield关键字的都是生成器函数，所以这里fibo是生成器函数。yield关键字只能出现在函数中，生成器函数的执行结果是生成器，注意这里所讲的“执行结果”不是函数的return值。生成器终止时必定抛出StopIteration异常，而for循环可以捕获，异常的value属性值为生成器函数的return值。

生成器还可以用next方法迭代。生成器会在yield语句处暂停，这是至关重要的，未来协程中的I/O阻塞就出现在这里。

### 生成器进化成协程

生成器是由迭代器进化而来的，所以生成器对象有`__iter__`和`__next__`方法，可以使用for循环获得值，注意这里所说的“获得值”指的是下文代码块中yield语句中yield关键字后面的i。

这是在python2.5时出现的特性，在python3.3中出现yield from语法之前，生成器没有太大用处。但此时yield关键字还是实现了一些特性，而且至关重要，就是生成器对象有send、throw和close方法。这三个方法的作用分别是发送数据给生成器并赋值给yield语句、向生成器抛入异常由生成器内部处理、终止生成器，有这三个方法后才能使得生成器进化为协程。

**生成器（或协程）有四种存在状态：**

- GEN_CREATED 创建完成，等待执行
- GEN_RUNNING 解释器正在执行（这个状态一般观察不到）
- GEN_SUSPENDED 在yield表达式处暂停
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

3. `next(g)` 预激生成器（或协程），这是必须要做的。在生成器创建完成后，需要将其第一次运行到yield语句处暂停。

4. `g.send("Hello Generator")` 暂停状态的生成器可以使用send方法发送数据，此方法的参数就是yield表达式的值，也就是yield表达式等号前面的value变量的值直接变成了“HelloGenerator”，继续向下执行完一次while循环，变量i被赋值，继续运行下一次循环，yield表达式弹出变量i

5. `g.throw(ValueError)` 向生成器抛入异常，异常会被try except捕获，作进一步处理

6. `g.close()` close方法终止生成器，异常不会被抛出

   因为生成器的调用方也就是程序员自己可以控制生成器的启动、暂停、终止，而且可以向生成器内部传入数据，所以这种生成器又叫协程，generator函数既可以叫做生成器函数，也可以叫做协程函数，这是生成器向协程的过渡阶段。

### 预激协程

预先激活生成器（或协程）可以使用next方法，也可以使用生成器的send方法发送None值：g.send(None)。为简化协程的使用，我们可以尝试编写一个装饰器来预激协程，这样创建的协程会立即进入GEN_SUSPENDED状态，可以直接使用send方法。

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



### 协程的返回值

前文“生成器原理”这一小节中提到了`StopIteration`异常的value属性值为生成器（协程）函数的return值，我们可以在使用协程时捕获这个异常并得到这个值。

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

1. `l = [] `创建列表，保存协程send方法每次发送的参数
2. `value = yield ` yield表达式不弹出值，仅作暂停之用
3. `if value == 'CLOSE': ` 如果send方法的参数为CLOSE，break终止while循环，停止生成器，抛出StopIteration异常
4. `l.append(value) ` 将value添加到列表
5. `return l ` 设置协程函数的返回值，该值在协程终止抛出StopIteration异常时赋值给value赋值

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

### 使用yield from

python3.3中新增了yield from语法，这是全新的语言结构，是yield的升级版。相比yield该语法有两大优势：避免嵌套循环、转移控制权

#### 避免嵌套循环

python内置模块`itertools`是十分强大的，里面有很多实用的方法，其中有一个是chain方法，它可以接收任意数量的可迭代对象作为参数，返回一个包含所有参数中的元素的迭代器。

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

接下来我们使用yield关键字来实现chain方法:

注意这里chain_yield函数的返回值是生成器

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

下面我们使用python3.3新增的yield from 语法优化上下文的chain函数。

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

可以看到yield from语句可以替代for循环，避免了嵌套循环。同yield一样，yield from语句也只能出现在函数体内部，有yield from语句的函数叫做协程函数或生成器函数。

yield from 后面接收一个可迭代对象，例如上面代码中的`iter_obj`变量，在协程中，可迭代对象往往是协程对象，这样就形成了嵌套协程。

#### 转移控制权

