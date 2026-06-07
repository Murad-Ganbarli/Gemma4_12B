HTML_TEMPLATE = """
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

    const botBubble = addMessage("bot", "");
    let hasTokens = false;

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                message: text,
                session_id: session_id
            })
        });

        if (!res.ok) {
            throw new Error("Network response was not ok");
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\\n");
            
            buffer = lines.pop();

            for (const line of lines) {
                if (line.trim() === "") continue;
                try {
                    const data = JSON.parse(line);
                    session_id = data.session_id;
                    
                    botBubble.textContent += data.token;
                    hasTokens = true;
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                } catch (e) {
                    console.error("Stream line parse error:", e);
                }
            }
        }
    } catch (err) {
        console.error("Stream interrupted:", err);
        if (hasTokens) {
            botBubble.textContent += "\\n\\n⚠️ [Connection interrupted / cut off]";
        } else {
            botBubble.textContent = "Error connecting to the model server.";
        }
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
}

function addMessage(role, text) {
    const div = document.createElement("div");
    div.className = "msg " + role;
    div.textContent = text;
    document.getElementById("messages").appendChild(div);
    return div;
}
</script>
</body>
</html>
"""