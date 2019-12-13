from rx.subject import Subject
from rx import Observable, defer, create
from rx.disposable import Disposable
from typing import Callable, Dict
from rx.operators import map, publish, filter, take_while, replay, do, share, take_until, take, do_action
import json
from types import FunctionType

from .message import RxImpMessage


class RxImp(object):

    def __init__(self, inObs: Observable, outSubject: Subject):
        """
        Parameters
        ---------
        inObs : Observable<bytes>
            Observable<bytes> that the instance subscribes to in order to receive data packets. The Observable should emit objects of type bytes
        outSubject : Subject<bytes>
            Subscribe to the outSubject to publish messages (i. e. send the to the receiver)
        """
        super().__init__()
        self._in: Observable = inObs.pipe(
            map(self._mapIncoming),
            publish())
        self._in.connect()
        self._out = Subject()
        self._out.pipe(map(self._mapOutgoing)).subscribe(outSubject)

    def observableCall(self, topic: str, payload) -> Observable:
        """
        Parameters
        ---------
        topic : str
            Topic mapped to this call. Other side must register a handler for this topic first using 'registerCall'
        payload : any
            Payload will be send to the other side in JSON format. May be None!
        
        Returns
        ---------
        Observable : dict
            Observable that will emit items received from the other side. Will also emit termination events

        """
        message = RxImpMessage(
            topic, 0, RxImpMessage.STATE_SUBSCRIBE, json.dumps(payload))

        def subscriptionFunction(observer, scheduler):
            def isRelevant(msg: RxImpMessage):
                return msg.rx_state == RxImpMessage.STATE_COMPLETE or msg.rx_state == RxImpMessage.STATE_ERROR or msg.rx_state == RxImpMessage.STATE_NEXT
            self._in.pipe(
                filter(lambda x: x.id == message.id),
                filter(lambda x: isRelevant(x)),
                map(lambda x: self._checkError(x)),
                take_while(lambda x: self._checkNotComplete(x)),
                map(lambda x: json.loads(x.payload)),
                share()
            ).subscribe(observer)
            self._out.on_next(message)

            def signalUnsubscribe():
                msg = RxImpMessage(
                    message.topic, 0, RxImpMessage.STATE_DISPOSE, None, id=message.id)
                self._out.on_next(msg)

            return lambda: signalUnsubscribe()

        return create(subscriptionFunction)

    def registerCall(self, topic: str, handler: Callable[[Dict], Observable]) -> Disposable:
        """
        Parameters
        ---------
        topic : str
            Topic this call will be registered on
        handler : Callable[[Dict], Observable]
            Handler for this topic. Is called with payload provided by caller (maybe empty). Return an Observable handling this call
        
        Returns
        ---------
        Disposable
            To remove registration
        """
        def handleSubscription(msg: RxImpMessage):

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

            handler(json.loads(msg.payload)).pipe(
                take_until(self._in.pipe(
                    filter(lambda x: x.rx_state == RxImpMessage.STATE_DISPOSE),
                    filter(lambda x: x.id == msg.id),
                    take(1)
                ))
            ).subscribe(on_next=lambda x: on_next(x),
                        on_error=lambda x: on_error(
                x),
                on_completed=lambda: on_complete())
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
