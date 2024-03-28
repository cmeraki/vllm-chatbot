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
from datetime import datetime

sys_msg = 'You are a human user interacting with a conversational AI assistant or chatbot. You will engage in natural conversations, asking questions, making requests, and responding just as you would when talking to a real AI assistant. You can ask about any topics, request assistance with tasks, or just have an open-ended conversation. The key is to role-play as a typical user would when conversing with an AI chatbot, speaking in a casual, conversational manner and making your queries and responses sound like they would come from a human, not an AI itself. Do not break character or give any indication that you are an AI language model. Simply act as a realistic human user would when chatting with an AI assistant.'

sys_prompt = {
    'role': 'system',
    'content': sys_msg
}
ds = load_dataset('HuggingFaceH4/ultrachat_200k')
ds = ds['train_gen']
dt = datetime.now()

logger.remove()
logger.add(f"./logs/{dt.strftime('%Y%m%d_%H%M')}.log", format="{message}", enqueue=True, level='INFO', serialize=True)

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


def orchestrate_conversation(conversation_id: int, num_total_turns: int):
    logger.bind(conversation_id=conversation_id).info(f'Starting conversation with conversation id: {conversation_id}')

    # user_llm = LLM(
    #     model_id='gpt-3.5-turbo-0125',
    #     messages=[sys_prompt],
    # )
    chatbot_llm = LLM(
        model_id='mistralai/Mistral-7B-Instruct-v0.2',
        uri='http://0.0.0.0:8000/v1/',
        messages=[]
    )

    user_msg = user_llm(message='START', max_tokens=1024)
    # chat_id, chatbot_msg = start_chatbot_agent(user_msg)
    chat_id=1

    logger.bind(conversation_id=conversation_id).info(f'Request ID assigned for conversation id {conversation_id}\t{chat_id}')

    conversation_turn = 0

    logger.bind(
        conversation_id=conversation_id
    ).info(f'Total number of turns for conversation id {conversation_id}\t{num_total_turns}')
    while conversation_turn < num_total_turns:
        try:
            logger.bind(
                conversation_id=conversation_id, turn=conversation_turn
            ).info(f'Conversation turn for conversation id {conversation_id}\t{conversation_turn}')
            chatbot_msg = chatbot_llm(message=user_msg, max_tokens=512)
            logger.bind(
                conversation_id=conversation_id, turn=conversation_turn
            ).info(f'Tokens: {chatbot_llm.total_tokens, chatbot_llm.input_tokens, chatbot_llm.output_tokens}')
            logger.bind(
                conversation_id=conversation_id, turn=conversation_turn
            ).debug(f'Messages: {chatbot_llm.messages}')
            user_msg = user_llm(message=chatbot_msg, max_tokens=1024)
            # chat_id, chatbot_msg = chatbot_agent(chat_id=chat_id, message=user_msg)

        except Exception as err:
            logger.bind(
                conversation_id=conversation_id, turn=conversation_turn
            ).error(f'Error: {err} in conversation id {conversation_id}')
            logger.bind(
                conversation_id=conversation_id, turn=conversation_turn
            ).error(f'{chatbot_llm.messages}')
            break

        finally:
            conversation_turn += 1

    logger.bind(
        conversation_id=conversation_id
    ).info(f'Ending conversation {conversation_id} after {conversation_turn} turns')
    
    logger.bind(
        conversation_id=conversation_id
    ).info(f'Tokens: {chatbot_llm.total_tokens, chatbot_llm.input_tokens, chatbot_llm.output_tokens}')

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('-r', type=float, required=False, default=4, help='Timely rate')
    parser.add_argument('-n', type=int, required=False, default=20, help='Time unit to run the test for')
    parser.add_argument('-l', type=int, required=False, default=15, help='Lower bound of conversations')
    parser.add_argument('-u', type=int, required=False, default=25, help='Upper bound of conversations')

    args = parser.parse_args()
    rate = args.r
    time_unit = args.n
    l, u = args.l, args.u

    logger.info(f'Rate: {rate}, time units: {time_unit}')
    logger.info(f'Lower bound of total turns: {l}, higher bound of total turns: {u}')

    arrival_rates = np.random.exponential(1/rate, time_unit)
    num_turns = np.random.randint(l, u, time_unit)

    idx = 0

    with concurrent.futures.ProcessPoolExecutor() as executor:
        for arrival, num_total_turns in zip(arrival_rates, num_turns):
            logger.info(f'Sleeping for {arrival}s')
            time.sleep(arrival)

            f = partial(orchestrate_conversation, conversation_id=idx, num_total_turns=num_total_turns)
            executor.submit(f)
            idx += 1

"""
We can serve a single 7B model (fp16) on 4090
- X number of requests concurrently
- With throughput Y tokens/s
- With Zs latency
"""