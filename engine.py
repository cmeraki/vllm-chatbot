import sys
import vllm
from vllm import LLM, SamplingParams
import paho.mqtt.client as mqtt
from paho.mqtt import client as mqtt_client
from typing import List
from loguru import logger

logger.remove()
logger.add(sys.stdout, level='DEBUG')

requests_q = {}
total_requests = 0

class Engine:
    def __init__(
            self,
            model_id: str = 'TheBloke/Llama-2-7b-Chat-AWQ'
        ) -> None:
        self.sampling_params = SamplingParams(
            temperature=0.7,
            top_p=0.9,
            max_tokens=1024,
            top_k=20,
            repetition_penalty=1.15
        )

        self.prefix = (
            "You are a helpful customer care chatbot for a financial company called as Mars."
            "For a user query, please respond appropriately by asking questions "
            "and gathering more information before responding.\n"
        )

        self.llm = LLM(model=model_id, gpu_memory_utilization=0.7)
        initial_output = self.llm.generate(
            self.prefix, self.sampling_params
        )

        logger.info(f'Prefix cached: {initial_output}')

        self.engine = self.llm.llm_engine
        self.global_prefix_pos = len(self.prefix)

        self.client = mqtt.Client(
            mqtt_client.CallbackAPIVersion.VERSION1, 'python-mqtt-123'
        )
        self.topic = 'vLLM'

        self.client.connect('localhost', 1883, 300)

    def send_message(self, request_id: str, message: str, prefix_pos: int) -> None:
        logger.info(f'Request ID {request_id} received')

        self.engine.add_request(
            request_id=request_id,
            prompt=self.prefix + message,
            sampling_params=self.sampling_params,
            prefix_pos=self.global_prefix_pos + prefix_pos
        )

        logger.info(f'Prefix pos used: {self.global_prefix_pos + prefix_pos}')

    def __call__(self) -> None:
        while self.engine.has_unfinished_requests():
                logger.info(f'Unfinished requests {self.engine.get_num_unfinished_requests()}')

                request_outputs: List[vllm.RequestOutput] = self.llm.step()
                for request_output in request_outputs:
                    if request_output.finished:
                        msg_to_publish = {
                            'request_id': request_output.request_id,
                            'message': request_output.outputs[0].text
                        }
                        logger.info(f'Publishing {request_output.request_id}')
                        self.client.publish(self.topic, msg_to_publish)
