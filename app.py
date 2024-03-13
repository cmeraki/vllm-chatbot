from typing import List
from fastapi import FastAPI, Query

app = FastAPI()

# List to store incoming requests
requests = []

@app.get("/start_chat")
def start_chat(
    message: str = Query(description="The starting message of the chat")
):
    return {"message": f"Message '{message}' received with ID {id}"}

def continue_chat():

# Endpoint to retrieve the list of requests
@app.get("/requests")
def get_requests():
    return requests