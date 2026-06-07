import os
import uuid
import time
import json
import logging
from typing import Dict, List, Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from llama_cpp import Llama

# 1. Setup Dual Logging (Terminal + File)
logger = logging.getLogger("LocalServer")
logger.setLevel(logging.INFO)

# Clear default handlers to avoid duplicate prints
logger.handlers = []

log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

# Console handler (for terminal output)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# File handler (writes to server.log in the project folder)
file_handler = logging.FileHandler("server.log", mode="a", encoding="utf-8")
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

app = FastAPI()

logger.info("Initializing model loading process...")

# Automatically downloads, caches, and loads the model from Hugging Face
llm = Llama.from_pretrained(
    repo_id="ggml-org/gemma-4-12B-it-GGUF",
    filename="gemma-4-12B-it-Q4_K_M.gguf",
    n_gpu_layers=-1,                        # Offload to your M4 GPU
    n_ctx=4096,                             # Standard context window
    n_threads=8,                            # Match physical cores
    flash_attn=True,                        # Enable Flash Attention
    f16_kv=True,                            # Optimized KV cache
    verbose=True                            # Enable internal llama.cpp logging
)

logger.info("Model loaded successfully. Server is ready.")

chat_history: Dict[str, List[dict]] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


@app.post("/chat")
def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    
    logger.info("=========================================")
    logger.info(f"Incoming Request | Session: {session_id}")
    logger.info(f"User Message: {req.message}")

    if session_id not in chat_history:
        chat_history[session_id] = [
            {"role": "system", "content": "You are a helpful assistant"}
        ]
        logger.info(f"Created new chat session for ID: {session_id}")

    chat_history[session_id].append(
        {"role": "user", "content": req.message}
    )

    logger.info(f"Context history turns: {len(chat_history[session_id])}")
    logger.info("Generating streaming response from M4 GPU...")

    # Streaming Generator
    def stream_generator():
        start_time = time.time()
        full_assistant_response = []
        
        # Call llama-cpp-python with stream=True
        response_stream = llm.create_chat_completion(
            messages=chat_history[session_id],
            stream=True
        )

        for chunk in response_stream:
            delta = chunk["choices"][0]["delta"]
            if "content" in delta:
                token = delta["content"]
                full_assistant_response.append(token)
                # Yield JSON line-by-line (NDJSON format)
                yield json.dumps({"session_id": session_id, "token": token}) + "\n"

        elapsed_time = time.time() - start_time
        assistant_answer = "".join(full_assistant_response)
        
        # Save the finalized answer to the context history list
        chat_history[session_id].append(
            {"role": "assistant", "content": assistant_answer}
        )
        
        logger.info(f"Stream completed in {elapsed_time:.2f}s | Response length: {len(assistant_answer)} chars")
        logger.info("=========================================")

    return StreamingResponse(stream_generator(), media_type="application/x-ndjson")


@app.get("/", response_class=HTMLResponse)
def home():
    logger.info("Web interface accessed.")
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Local LLM Chat</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: white;
            display: flex;
            justify-content: center;
            padding-top: 40px;
            margin: 0;
        }
        #chat {
            width: 600px;
            height: 85vh;
            display: flex;
            flex-direction: column;
            border: 1px solid #334155;
            border-radius: 10px;
            overflow: hidden;
            background: #1e293b;
        }
        #messages {
            flex: 1;
            padding: 15px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .msg {
            max-width: 80%;
            padding: 10px 14px;
            border-radius: 8px;
            line-height: 1.4;
            word-wrap: break-word;
            white-space: pre-wrap;
        }
        .user {
            background: #2563eb;
            align-self: flex-end;
            color: white;
        }
        .bot {
            background: #334155;
            align-self: flex-start;
            color: #f1f5f9;
        }
        #inputBox {
            display: flex;
            border-top: 1px solid #334155;
            background: #0f172a;
        }
        input {
            flex: 1;
            padding: 15px;
            border: none;
            outline: none;
            background: transparent;
            color: white;
            font-size: 16px;
        }
        button {
            padding: 0 25px;
            border: none;
            background: #22c55e;
            color: black;
            font-weight: bold;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #16a34a;
        }
    </style>
</head>
<body>
    <div id="chat">
        <div id="messages"></div>
        <div id="inputBox">
            <input id="input" placeholder="Type a message..." onkeydown="if(event.key === 'Enter') send()" />
            <button onclick="send()">Send</button>
        </div>
    </div>

<script>
let session_id = null;

async function send() {
    const input = document.getElementById("input");
    const text = input.value.trim();
    if (!text) return;
    input.value = "";

    addMessage("user", text);

    const messagesDiv = document.getElementById("messages");
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    // Create the assistant response bubble ahead of receiving the stream
    const botBubble = addMessage("bot", "");

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                message: text,
                session_id: session_id
            })
        });

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\\n");
            
            // Retain any incomplete last line
            buffer = lines.pop();

            for (const line of lines) {
                if (line.trim() === "") continue;
                try {
                    const data = JSON.parse(line);
                    session_id = data.session_id;
                    
                    // Stream tokens directly into the bubble text content
                    botBubble.textContent += data.token;
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                } catch (e) {
                    console.error("Stream line parse error:", e);
                }
            }
        }
    } catch (err) {
        botBubble.textContent = "Error connecting to the model server.";
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
}

function addMessage(role, text) {
    const div = document.createElement("div");
    div.className = "msg " + role;
    div.textContent = text;
    document.getElementById("messages").appendChild(div);
    return div; // Return element pointer so we can modify text on the fly
}
</script>
</body>
</html>
"""