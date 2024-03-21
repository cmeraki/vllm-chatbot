import sys
import json
import time
import concurrent.futures
import requests
import numpy as np
from loguru import logger
from functools import partial
from llm import LLM
from datasets import load_dataset

sys_msg = 'You are a human user interacting with a conversational AI assistant or chatbot. You will engage in natural conversations, asking questions, making requests, and responding just as you would when talking to a real AI assistant. You can ask about any topics, request assistance with tasks, or just have an open-ended conversation. The key is to role-play as a typical user would when conversing with an AI chatbot, speaking in a casual, conversational manner and making your queries and responses sound like they would come from a human, not an AI itself. Do not break character or give any indication that you are an AI language model. Simply act as a realistic human user would when chatting with an AI assistant.'

sys_prompt = {
    'role': 'system',
    'content': sys_msg
}
logger.remove()
logger.add('./simulation.log', format="{time} - {level} - {thread} - {process} - {message}", enqueue=True, level='INFO')
ds = load_dataset('HuggingFaceH4/ultrachat_200k')
ds = ds['train_gen']

def start_chatbot_agent(message):
    url = "http://127.0.0.1:8000/start_chat"

    payload = json.dumps({
        "user_message": message
    })

    headers = {
    'accept': 'application/json',
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    assert response.status_code == 200, 'Request not successful'

    data = response.json()

    return data['request_id'], data['assistant_message']


def chatbot_agent(chat_id, message):
    url = "http://127.0.0.1:8000/chat"

    payload = json.dumps({
        "request_id": str(chat_id),
        "user_message": message
    })

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    assert response.status_code == 200, 'Request not successful'

    data = response.json()

    return data['request_id'], data['assistant_message']


def user_llm(message, max_tokens):
    idx = np.random.randint(0, len(ds))
    return ds[idx]['prompt']


def orchestrate_conversation(conversation_id: int):
    logger.info(f'Starting conversation with conversation id: {conversation_id}')

    # user_llm = LLM(
    #     model_id='gpt-3.5-turbo-0125',
    #     messages=[sys_prompt],
    # )
    chatbot_llm = LLM(
        model_id='mistralai/Mistral-7B-Instruct-v0.2',
        uri='http://0.0.0.0:8000/v1/',
        # messages=[sys_prompt]
    )

    user_msg = user_llm(message='START', max_tokens=1204)
    # chat_id, chatbot_msg = start_chatbot_agent(user_msg)
    chat_id=1

    logger.info(f'Request ID assigned for conversation id {conversation_id}\t{chat_id}')

    conversation_turn = 0
    num_total_turns = np.random.randint(5, 15)

    logger.info(f'Total number of turns for conversation id {conversation_id}\t{num_total_turns}')
    while conversation_turn < num_total_turns:
        try:
            logger.info(f'Conversation turn for conversation id {conversation_id}\t{conversation_turn}')
            chatbot_msg = chatbot_llm(message=user_msg, max_tokens=256)
            user_msg = user_llm(message=chatbot_msg, max_tokens=1204)
            # chat_id, chatbot_msg = chatbot_agent(chat_id=chat_id, message=user_msg)

        except AssertionError as err:
            logger.error(f'{err}')
            break

        except Exception as err:
            logger.error(f'Error: {err} in conversation id {conversation_id}')
            break

        finally:
            conversation_turn += 1

    logger.info(f'Ending conversation {conversation_id} after {conversation_turn} turns')
    logger.info(f'Tokens: {chatbot_llm.total_tokens, chatbot_llm.input_tokens, chatbot_llm.output_tokens}')


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('-n', type=int, required=False, default=20, help='Number of conversations to start')
    parser.add_argument('-w', type=int, required=False, default=4, help='Upper limit of wait period between starting conversations (in s). Should be greater than 2')

    args = parser.parse_args()
    w = args.w

    num_convs = args.n
    idx = 0

    with concurrent.futures.ProcessPoolExecutor() as executor:
        while idx < num_convs:
            # wait_for_newchat = np.random.randint(2, w)
            # logger.info(f'Waiting for a new conversation to start. Will sleep for {wait_for_newchat}s')
            # time.sleep(wait_for_newchat)

            f = partial(orchestrate_conversation, conversation_id=idx)
            executor.submit
            executor.submit(f)
            idx += 1


"""
We can serve a single 7B model (fp16) on 4090
- X number of requests concurrently
- With throughput Y tokens/s
- With Zs latency
"""