from fastapi import FastAPI
from pydantic import BaseModel
import json
import random

app = FastAPI()

class Message(BaseModel):
    text: str

with open("intents.json", "r", encoding="utf-8") as f:
    intents = json.load(f)

@app.post("/chat")
def chat(msg: Message):
    user_text = msg.text.lower()

    for intent in intents["intents"]:
        for pattern in intent["patterns"]:
            if pattern in user_text:
                return {
                    "reply": random.choice(intent["responses"])
                }

    return {"reply": "Desculpa, não entendi 😅"}
