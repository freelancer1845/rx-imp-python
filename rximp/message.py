from uuid import uuid4
import json


class RxImpMessage(dict):

    STATE_NEXT = 0
    STATE_ERROR = 1
    STATE_COMPLETE = 2
    STATE_SUBSCRIBE = 3
    STATE_DISPOSE = 4

    def __init__(self, topic: str, count: int, rx_state: int, payload: bytes, id: str = None):

        self.topic = topic
        self.count = count
        self.rx_state = rx_state
        self.payload = payload
        if id is None:
            self.id = uuid4().hex
        else:
            self.id = id
        dict.__init__(self, topic=topic, count=count, rx_state=rx_state,payload=payload,id=self.id)

    @staticmethod
    def fromBytes(data):
        obj = json.loads(data.decode('UTF-16'))
        return RxImpMessage(topic=obj['topic'], count=obj['count'], rx_state=obj['rx_state'], payload=obj['payload'], id=obj['id'])

    def toBytes(self):
        return json.dumps(self).encode('UTF-16')
