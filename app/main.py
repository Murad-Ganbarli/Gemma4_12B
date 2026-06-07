import json
import time
from typing import Optional
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from app.config import logger, Console
from app.model import llm
from app.history import (
    chat_history, 
    get_or_create_session, 
    add_user_message, 
    create_empty_assistant_entry
)
from app.templates import HTML_TEMPLATE

app = FastAPI()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


@app.post("/chat")
def chat(req: ChatRequest):
    session_id = get_or_create_session(req.session_id)
    
    logger.info("=========================================")
    logger.info(f"Incoming Request | Session: {session_id}")
    logger.info(f"User Message: {req.message}")

    # 1. Clear state/KV cache to prevent sequence position mismatch crashes (IndexError / llama_decode returned -1)
    llm.reset()

    # 2. Append the user's input to the history
    add_user_message(session_id, req.message)

    logger.info(f"Context history turns: {len(chat_history[session_id])}")
    logger.info("Generating streaming response from M4 GPU...")

    def stream_generator():
        start_time = time.time()
        token_count = 0
        
        # Create a mutable reference in history list BEFORE generator loops
        assistant_entry = create_empty_assistant_entry(session_id)
        
        # Extract context excluding the empty assistant placeholder
        model_context = chat_history[session_id][:-1]

        response_stream = llm.create_chat_completion(
            messages=model_context,
            stream=True
        )

        for chunk in response_stream:
            delta = chunk["choices"][0]["delta"]
            if "content" in delta:
                token = delta["content"]
                
                # Update memory
                assistant_entry["content"] += token
                token_count += 1
                
                # Print real-time generation speed metrics in-place
                elapsed_so_far = time.time() - start_time
                speed_so_far = token_count / elapsed_so_far if elapsed_so_far > 0 else 0
                print(
                    f"\r\033[94m[METRICS] Active stream | Speed: {speed_so_far:.2f} tokens/sec | Tokens: {token_count}\033[0m", 
                    end="", 
                    flush=True
                )

                yield json.dumps({"session_id": session_id, "token": token}) + "\n"

        # Once generator completes
        elapsed_time = time.time() - start_time
        final_speed = token_count / elapsed_time if elapsed_time > 0 else 0
        
        # Clear the in-place metrics line and output clean final result
        print("\r" + " " * 95 + "\r", end="", flush=True)
        Console.success(f"Generation Complete! Time: {elapsed_time:.2f}s | Speed: {final_speed:.2f} tokens/sec | Tokens: {token_count}")
        
        logger.info(f"Stream completed in {elapsed_time:.2f}s | Tokens generated: {token_count}")
        logger.info("=========================================")

    return StreamingResponse(stream_generator(), media_type="application/x-ndjson")


@app.get("/", response_class=HTMLResponse)
def home():
    logger.info("Web interface accessed.")
    return HTML_TEMPLATE