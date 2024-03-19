import sys
import json
from loguru import logger
from paho.mqtt.client import MQTTMessage
from pubsub import Publisher, Subscriber

logger.remove()
logger.add(sys.stdout, level='INFO')

class Chat:
    def __init__(self, id, publisher: Publisher,subscriber: Subscriber):
        self.id = id
        self.messages = []
        self.history = ''
        self.prefix_pos = -1

        self.publisher = publisher
        self.subscriber = subscriber

    def chat(self, user_message: str) -> str:
        logger.info(f'User message received: {user_message}')

        self.messages.append(user_message)
        self.history, self.prefix_pos = self._history()

        logger.info(f'User history: {self.history}')
        logger.info(f'Prefix pos: {self.prefix_pos}')

        self.publisher.connect()
        self.publisher.publish(json.dumps({
            'request_id': self.id,
            'message': self.history,
            'prefix_pos': self.prefix_pos
        }))

        while True:
            if self.subscriber.completed_requests:
                m: MQTTMessage = self.subscriber.completed_requests.pop()
                response = json.loads(m.payload.decode())
                assistant_message = response['message']
                logger.info(f'Assistant message: {assistant_message}. Queue message: {m.payload.decode()}')
                self.messages.append(assistant_message)

                return assistant_message

    def _history(self):
        user_fomrat = "User: {message}\n"
        assistant_format = "Assistant: {message}\n"
        prefix_pos = 1

        complete_history = ''

        for idx, msg in enumerate(self.messages):
            if not idx%2:
                complete_history += user_fomrat.format(message=msg)
                continue

            complete_history += assistant_format.format(message=msg)
            prefix_pos += len(assistant_format.format(message=msg))

        return complete_history, prefix_pos - 1

    def end_chat(self):
        with open(f'./tmp/history/history_{self.id}.txt', 'w') as fp:
            for ln in self.history.split('\n'):
                fp.write(ln)

if __name__ == '__main__':

    import numpy as np
    c = Chat()

    for i in range(0, 1):
        act_number = np.random.randint(1, 100)
        r = c.chat(f'Hello, I want to know how to close the account number {act_number}!')
        print(r)

    c.end_chat()
