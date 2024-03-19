import sys
import json
import vllm
from typing import List
from loguru import logger
from vllm import LLM, SamplingParams
from paho.mqtt.client import MQTTMessage
from pubsub import Publisher, Subscriber

logger.remove()
logger.add(sys.stdout, level='INFO')

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

        self.prefix = 'You are a virtual customer service agent for an e-commerce company. Greet customers warmly and converse naturally to understand their needs. Use polite, professional yet approachable language. Ask clarifying questions as needed. Provide clear explanations, troubleshooting steps, and accurate information based on company policies. Offer alternatives if requests cannot be fulfilled. Maintain a positive, patient, and empathetic attitude. Handle inquiries about orders, shipping, returns, products, account issues, etc. with the goal of an excellent customer experience.'

        self.llm = LLM(model=model_id, gpu_memory_utilization=0.7, max_model_len=1024)
        initial_output = self.llm.generate(
            self.prefix, self.sampling_params
        )

        logger.info(f'Prefix cached: {initial_output}')

        self.llm_engine = self.llm.llm_engine
        self.global_prefix_pos = len(self.prefix)

        self.publisher = Publisher('messages/assistant')
        self.subscriber = Subscriber('messages/user')

        self.subscriber.connect()

    def add_message(self, request_id: str, message: str, prefix_pos: int) -> None:
        logger.info(f'Request ID {request_id} received')
        logger.info(f'Prefix pos used: {self.global_prefix_pos + prefix_pos}')

        self.llm_engine.add_request(
            request_id=request_id,
            prompt=self.prefix + message,
            sampling_params=self.sampling_params,
            prefix_pos=self.global_prefix_pos + prefix_pos
        )

    def listen_for_message(self) -> None:
        if self.subscriber.completed_requests:
            m: MQTTMessage = self.subscriber.completed_requests.pop()
            logger.info(f'Queue message: {m.payload.decode()}')
            user_message = json.loads(m.payload.decode())
            self.add_message(
                user_message['request_id'], user_message['message'], user_message['prefix_pos']
            )

    def __call__(self) -> None:
        logger.info('Running step function')

        while True:
            self.listen_for_message()

            if not self.llm_engine.has_unfinished_requests():
                continue

            request_outputs: List[vllm.RequestOutput] = self.llm_engine.step()
            logger.debug(f'Requests processed in this step: {[r.request_id for r in request_outputs]}')
            logger.debug(f'Number of unfinished requests: {self.llm_engine.get_num_unfinished_requests()}')

            for request_output in request_outputs:
                if request_output.finished:
                    msg_to_publish = json.dumps({
                        'request_id': request_output.request_id,
                        'prompt': request_output.prompt,
                        'message': request_output.outputs[0].text
                    })
                    logger.info(f'Publishing {request_output.request_id}')
                    logger.info(
                        f'Tokens for the prompt: {len(request_output.prompt_token_ids)} Tokens for the request: {len(request_output.outputs[0].token_ids)}'
                    )
                    self.publisher.connect()
                    self.publisher.publish(msg_to_publish)


if __name__ == '__main__':
    bot = Engine()
    bot()
