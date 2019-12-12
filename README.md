# Python implementation of Rx-Imp

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