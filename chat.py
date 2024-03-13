import sys
from queue import Queue
from loguru import logger
from engine import Engine
import paho.mqtt.client as mqtt
from paho.mqtt import client as mqtt_client

logger.remove()
logger.add(sys.stdout, level='INFO')

conversation_counter = 0
bot = Engine()


class Subscriber:
    def __init__(self):
        self.client = mqtt.Client(
            mqtt_client.CallbackAPIVersion.VERSION1, 'python-mqtt-123'
        )
        self.topic = 'vLLM'
        self.completed_requests = Queue()

    def on_message(self, client, userdata, message):
        logger.info(f'Received message: {message}')
        self.completed_requests.put(message)

    def connect(self, broker="localhost", port=1883):
        self.client.connect(broker, port, 300)
        self.client.subscribe(self.topic)
        self.client.on_message = self.on_message
        self.client.loop_start()

class Chat:
    def __init__(self):
        global conversation_counter
        self.id = str(conversation_counter)
        self.messages = []
        self.history = ''
        self.prefix_pos = -1
        conversation_counter += 1

        self.subscriber = Subscriber()

    def chat(self, user_message: str) -> str:
        self.messages.append(user_message)
        self.history, self.prefix_pos = self._history()

        bot.send_message(
            request_id = self.id,
            messsage=self.history,
            prefix_pos=self.prefix_pos
        )

        bot()

        while self.subscriber.completed_requests:
            for m in self.subscriber.completed_requests:
                print(f'Queue message: {m}')
                assistant_message = m
                self.messages.append(assistant_message)

        return assistant_message

    def _history(self):
        user_fomrat = "User: {message}"
        assistant_format = "Assistant: {message}"

        complete_history = ''

        for idx, msg in enumerate(self.conversation.messages):
            if idx%2:
                complete_history += user_fomrat.format(message=msg)
                complete_history += '\n'
                continue

            complete_history += assistant_format.format(message=msg)
            complete_history += '\n'

        return complete_history, len(complete_history) - 1

    def end_chat(self):
        with open('history.txt', 'w') as fp:
            for ln in self.history.split('\n'):
                fp.write(ln)

if __name__ == '__main__':
    c1 = Chat()
    r1 = c1.chat('Hello, I want to know how to close the account!')

    print(r1)
