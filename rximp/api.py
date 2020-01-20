from rx.subject import Subject
from rx import Observable, defer, create
from rx.disposable import Disposable
from typing import Callable, Dict
from rx.operators import map, publish, filter, take_while, replay, do, share, take_until, take, do_action
import json
from types import FunctionType
from threading import Lock

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

        def subscriptionFunction(observer, scheduler):
            message = RxImpMessage(
                topic, 0, RxImpMessage.STATE_SUBSCRIBE, json.dumps(payload))

            publisher: Subject = Subject()
            lock = Lock()
            currentCount = 0
            queue = []

            def orderingSubscriber(msg: RxImpMessage):
                nonlocal currentCount
                nonlocal queue
                with lock:
                    currentCount += 1
                    queue.append(msg)
                    queue.sort(key=lambda x: x.count)
                    toNext = [msg for msg in queue if msg.count < currentCount]
                    queue = [msg for msg in queue if msg.count >= currentCount]
                    for msg in toNext:
                        publisher.on_next(msg)

            def isRelevant(msg: RxImpMessage):
                return msg.rx_state == RxImpMessage.STATE_COMPLETE or msg.rx_state == RxImpMessage.STATE_ERROR or msg.rx_state == RxImpMessage.STATE_NEXT

            secondSubscription: Disposable = self._in.pipe(
                filter(lambda x: x.id == message.id),
                filter(lambda x: isRelevant(x)),
                map(lambda x: self._checkError(x)),
            ).subscribe(on_next=lambda x: orderingSubscriber(x), on_error=lambda err: publisher.on_error(err))

            subscription: Disposable = publisher.pipe(
                take_while(lambda x: self._checkNotComplete(x)),
                map(lambda x: json.loads(x.payload)),
            ).subscribe(observer)
            self._out.on_next(message)

            def signalUnsubscribe():
                msg = RxImpMessage(
                    message.topic, 0, RxImpMessage.STATE_DISPOSE, None, id=message.id)
                secondSubscription.dispose()
                subscription.dispose()
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
            currentCount = 0

            def on_next(next):
                nonlocal currentCount
                nextMsg = RxImpMessage(
                    topic=msg.topic, count=currentCount, rx_state=RxImpMessage.STATE_NEXT, payload=json.dumps(next), id=msg.id)
                currentCount += 1
                self._out.on_next(nextMsg)

            def on_error(error):
                nonlocal currentCount
                errorMsg = RxImpMessage(
                    topic=msg.topic, count=currentCount, rx_state=RxImpMessage.STATE_ERROR, payload=json.dumps(error), id=msg.id)
                currentCount += 1
                self._out.on_next(errorMsg)

            def on_complete():
                nonlocal currentCount
                completeMsg = RxImpMessage(
                    topic=msg.topic, count=currentCount, rx_state=RxImpMessage.STATE_COMPLETE, payload=None, id=msg.id)
                currentCount += 1
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
