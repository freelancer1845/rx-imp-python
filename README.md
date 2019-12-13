# Python implementation of Rx-Imp

## Install latest version (needs python3 try pip3 install rximp)

```bash
pip install rximp
```

## Other implementations

* [Java](https://github.com/freelancer1845/rx-imp-java)
* [Javascript/Typescript](https://github.com/freelancer1845/rx-imp-js)

## Example using ZeroMQ (pyzmq)

```python

import zmq
from rximp import RxImp
from rx.subject import Subject
from queue import Queue
from rx import interval, of
from rx.operators import timeout
import time

context = zmq.Context()

socket = context.socket(zmq.PAIR)
port = "5555"
socket.bind("tcp://*:5555") # on other side do socket.connect("tcp://<ipaddress>:5555")

_in = Subject()
_out = Subject()

_outQueue = Queue()

_out.subscribe(on_next=lambda x: _outQueue.put(x))

_rxImp = RxImp(_in, _out)

_rxImp.registerCall("pingpong", lambda x: of(0))


def pingTimeCall():
    start = time.time()
    _rxImp.observableCall("pingpong", 0).pipe(timeout(1.0)).subscribe(on_next=lambda x: print(
        "Ping Time: {}s".format(time.time() - start)), on_error=lambda x: print("Ping Pong Timed out"))


interval(1.0).subscribe(lambda x: pingTimeCall())

while True:
    try:
        msg = socket.recv(flags=zmq.NOBLOCK)
        if msg is not None:
            _in.on_next(msg)
    except zmq.ZMQError:
        pass

    if not _outQueue.empty():
        socket.send(_outQueue.get())

    time.sleep(0.001)

```


## Example using websocket_client library


```python
import websocket
from threading import Thread
import time
from rximp import RxImp
from rx.subject import Subject
from rx import timer, of

_in = Subject()
_out = Subject()

_rxImp = None


def on_message(ws, message):
    _in.on_next(message)


def on_error(ws, error):
    print(error)


def on_close(ws: websocket.WebSocketApp):
    import traceback
    traceback.print_stack()
    traceback.print_exc()
    print("### closed ###")


def on_open(ws):
    global _rxImp
    print("Websocket Opened")
    print("Creating RXIMP Hanlder")
    _rxImp = RxImp(_in, _out)
    _out.subscribe(lambda x: ws.send(x, opcode=websocket.ABNF.OPCODE_BINARY))


if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://localhost:8080/rx",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open

    def doStupidThings(x):
        _rxImp.observableCall('stupidTarget',
                              None).subscribe(lambda x: print(x))

    def handleStupidThings(x):
        return of(x)

    _rxImp.registerCall('stupidTarget', handleStupidThings)

    timer(1.0).subscribe(lambda x: doStupidThings(x))

    ws.run_forever()

```
