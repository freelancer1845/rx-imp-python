from rx.subject import Subject
from rx import Observable, defer
from rx.disposable import Disposable
from typing import Callable, Dict
from rx.operators import map, publish, filter, take_while, replay, do
import json
from types import FunctionType

from .message import RxImpMessage


class RxImp(object):

    def __init__(self, inObs: Observable, outSubject: Subject):
        super().__init__()
        self._in: Observable = inObs.pipe(
            map(self._mapIncoming),
            publish())
        self._in.connect()
        self._out = Subject()
        self._out.pipe(map(self._mapOutgoing)).subscribe(outSubject)

    def observableCall(self, topic: str, payload) -> Observable:
        message = RxImpMessage(
            topic, 0, RxImpMessage.STATE_SUBSCRIBE, json.dumps(payload))

        def func():
            obs = self._in.pipe(
                filter(lambda x: x.id == message.id),
                map(lambda x: self._checkError(x)),
                take_while(lambda x: self._checkNotComplete(x)),
                map(lambda x: json.loads(x.payload)),
                replay()
            )
            obs.connect()
            self._out.on_next(message)
            return obs

        return defer(lambda x: func())

    def registerCall(self, topic: str, handler: Callable[[Dict, Subject], None]) -> Disposable:

        def handleSubscription(msg: RxImpMessage):
            subject: Subject = Subject()

            def on_next(next):
                nextMsg = RxImpMessage(
                    topic=msg.topic, count=0, rx_state=RxImpMessage.STATE_NEXT, payload=json.dumps(next), id=msg.id)
                self._out.on_next(nextMsg)

            def on_error(error):
                errorMsg = RxImpMessage(
                    topic=msg.topic, count=0, rx_state=RxImpMessage.STATE_ERROR, payload=json.dumps(error), id=msg.id)
                self._out.on_next(errorMsg)

            def on_complete():
                completeMsg = RxImpMessage(
                    topic=msg.topic, count=0, rx_state=RxImpMessage.STATE_COMPLETE, payload=None, id=msg.id)
                self._out.on_next(completeMsg)

            subject.subscribe(
                on_next=lambda x: on_next(x),
                on_error=lambda x: on_error(x),
                on_completed=lambda: on_complete()
            )
            handler(json.loads(msg.payload), subject)
        return self._in.pipe(
            filter(lambda x: x.rx_state == RxImpMessage.STATE_SUBSCRIBE),
            filter(lambda x: x.topic == topic)
        ).subscribe(on_next=lambda x: handleSubscription(x))

    def _mapIncoming(self, data):
        return RxImpMessage.fromBytes(data)

    def _mapOutgoing(self, msg: RxImpMessage):
        return msg.toBytes()

    def _checkError(self, msg: RxImpMessage) -> RxImpMessage:
        if msg.rx_state == RxImpMessage.STATE_ERROR:
            raise Exception(json.loads(msg.payload))
        else:
            return msg

    def _checkNotComplete(self, msg: RxImpMessage) -> bool:
        if msg.rx_state == RxImpMessage.STATE_COMPLETE:
            return False
        else:
            return True
