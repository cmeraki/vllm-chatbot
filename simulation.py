import json
import time
import threading
import requests
import numpy as np
from loguru import logger
from functools import partial
from llm import LLM

sys_msg = 'You are a human user interacting with a conversational AI assistant or chatbot. You will engage in natural conversations, asking questions, making requests, and responding just as you would when talking to a real AI assistant. You can ask about any topics, request assistance with tasks, or just have an open-ended conversation. The key is to role-play as a typical user would when conversing with an AI chatbot, speaking in a casual, conversational manner and making your queries and responses sound like they would come from a human, not an AI itself. Do not break character or give any indication that you are an AI language model. Simply act as a realistic human user would when chatting with an AI assistant.'

sys_prompt = {
    'role': 'system',
    'content': sys_msg
}

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


def user_agent(llm, message):
    return llm(message)


def vllm_agent(llm, message):
    return llm(message)

def orchestrate_conversation(conversation_id: int):
    logger.info(f'Starting conversation with conversation id: {conversation_id}')

    user_llm = LLM(
        model_id='gpt-3.5-turbo-0125',
        messages=[sys_prompt],
    )

    user_msg = user_agent(llm=user_llm, message='START')
    chat_id, chatbot_msg = start_chatbot_agent(user_msg)

    logger.info(f'Request ID assigned for conversation id {conversation_id}\t{chat_id}')

    conversation_turn = 0
    num_total_turns = np.random.randint(5, 50)

    logger.info(f'Total number of turns for conversation id {conversation_id}\t{num_total_turns}')
    while conversation_turn < num_total_turns:
        try:
            logger.info(f'Conversation turn for conversation id {conversation_id}\t{conversation_turn}')
            user_msg = user_agent(llm=user_llm, message=chatbot_msg)
            chat_id, chatbot_msg = chatbot_agent(chat_id=chat_id, message=user_msg)

        except AssertionError as err:
            logger.error(f'{err}')
            continue

        except Exception as err:
            logger.error(f'Error: {err} in conversation id {conversation_id}')
            break

        finally:
            conversation_turn += 1


if __name__ == '__main__':

    num_convs = 1
    idx = 0
    threads = []

    while idx < num_convs:
        # wait_for_newchat = np.random.randint(2, 30)
        wait_for_newchat = 1
        logger.info(f'Waiting for a new conversation to start. Will sleep for {wait_for_newchat}s')
        time.sleep(wait_for_newchat)

        f = partial(orchestrate_conversation, conversation_id=idx)
        t = threading.Thread(target=f)
        t.start()

        threads.append(t)

        idx += 1


    for t in threads:
        t.join()