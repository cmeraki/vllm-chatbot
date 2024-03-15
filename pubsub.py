import sys
from queue import Queue
import paho.mqtt.client as mqtt
from paho.mqtt import client as mqtt_client
from loguru import logger

logger.remove()
logger.add(sys.stdout, level='INFO')

class Publisher:
    def __init__(self, topic):
        self.client = mqtt.Client(
            mqtt_client.CallbackAPIVersion.VERSION1
        )
        self.topic = topic

    def connect(self, broker="localhost", port=1883):
        self.client.connect(broker, port, 60)

    def publish(self, message):
        self.client.publish(self.topic, message)


class Subscriber:
    def __init__(self, topic):
        self.client = mqtt.Client(
            mqtt_client.CallbackAPIVersion.VERSION1
        )
        self.topic = topic
        self.completed_requests = []

    def on_message(self, client, userdata, message):
        logger.info(f'Received message: {message}')
        self.completed_requests.append(message)

    def connect(self, broker="localhost", port=1883):
        self.client.connect(broker, port, 300)
        self.client.subscribe(self.topic)
        self.client.on_message = self.on_message
        self.client.loop_start()
