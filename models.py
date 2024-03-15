from pydantic import BaseModel

class NewChat(BaseModel):
    user_message: str

class UserChatRequest(BaseModel):
    request_id: int
    user_message: str

class UserChatResponse(BaseModel):
    request_id: int
    assistant_message: str
