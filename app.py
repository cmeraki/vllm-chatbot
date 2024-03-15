import sys
from typing import Union
from loguru import logger
from fastapi import FastAPI
from collections import deque

from chat import Chat
from pubsub import Subscriber, Publisher
from models import UserChatRequest, UserChatResponse, NewChat

logger.remove()
logger.add(sys.stdout, level='INFO')

app = FastAPI()

publisher = Publisher('messages/user')
subscriber = Subscriber('messages/assistant')
subscriber.connect()

user_conversations = deque()

@app.post("/start_chat")
def start_chat(request: NewChat) -> UserChatResponse:
    global user_conversations
    request_id = len(user_conversations)
    conversation = Chat(
        id=str(request_id),
        publisher=publisher,
        subscriber=subscriber
    )
    user_conversations.append(conversation)

    assistant_message = conversation.chat(user_message=request.user_message)

    logger.info(f'Number of user conversations: {len(user_conversations)}')

    return {
        'request_id': request_id,
        'assistant_message': assistant_message
    }

@app.post("/chat")
def chat(request: UserChatRequest) -> Union[UserChatResponse, str]:
    global user_conversations
    try:
        logger.info(f'User conversations: {user_conversations}')
        conversation: Chat = user_conversations[request.request_id]
    except:
        return "User chat not found"

    assistant_message = conversation.chat(user_message=request.user_message)

    return {
        'request_id': request.request_id,
        'assistant_message': assistant_message
    }

@app.get("/end_chat")
def end_chat(request_id: int) -> str:
    try:
        conversation: Chat = user_conversations[request_id]
        conversation.end_chat()
        user_conversations.remove(request_id)
        {"status": True}

    except:
        return {"status": False}
