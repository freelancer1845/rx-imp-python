import unittest
from rximp import RxImp
from rx import Observable, of, interval
from rx.operators import map, do, take, finally_action
from rx.subject import Subject
from rx.testing.mockobserver import MockObserver
import json
import time
from rx.testing import TestScheduler, Recorded
from rx.testing.reactivetest import OnCompleted

scheduler = TestScheduler()


class RxImpTest(unittest.TestCase):

    TEST_TOPIC = '/topic/test'

    def setUp(self):
        self.inSubject = Subject()
        self.outSubject = Subject()
        self.rxImp = RxImp(self.inSubject, self.outSubject)

    def test_messagesSubscribeOnCall(self):
        mockObs = MockObserver(scheduler=scheduler)
        self.outSubject.pipe(
            map(lambda x: self.rxImp._mapIncoming(x)),
            map(lambda x: json.loads(x.payload))
        ).subscribe(mockObs)
        self.outSubject.subscribe(self.inSubject)
        self.rxImp.observableCall(
            RxImpTest.TEST_TOPIC, 253).subscribe()

        time.sleep(0.5)
        self.assertTrue(len(mockObs.messages) == 1)
        self.assertTrue(mockObs.messages[0].value.value is 253)

    def test_simpleConnect(self):
        mockObs = MockObserver(scheduler=scheduler)

        def handler(args):
            return of(args)

        self.rxImp.registerCall(RxImpTest.TEST_TOPIC, lambda x: handler(x))

        self.outSubject.subscribe(self.inSubject)

        self.rxImp.observableCall(RxImpTest.TEST_TOPIC, 1).subscribe(mockObs)
        time.sleep(0.5)
        self.assertTrue(len(mockObs.messages) == 2)
        self.assertTrue(mockObs.messages[0].value.value is 1)

    def test_signalsComplete(self):
        mockObs = MockObserver(scheduler=scheduler)
        mockObs2 = MockObserver(scheduler=scheduler)
        subject = Subject()
        subject.subscribe(mockObs2)

        def handler(args):
            return interval(0.01).pipe(take(10), finally_action(lambda: subject.on_completed()))

        self.rxImp.registerCall(RxImpTest.TEST_TOPIC, lambda x: handler(x))

        self.outSubject.subscribe(self.inSubject)

        self.rxImp.observableCall(RxImpTest.TEST_TOPIC, 1).pipe(
            take(5)).subscribe(mockObs)
        time.sleep(0.1)
        print(mockObs.messages)
        self.assertTrue(len(mockObs.messages) == 6)
        print(mockObs2.messages)
        self.assertTrue(len(mockObs2.messages) == 1)


if __name__ == "__main__":
    unittest.main()
