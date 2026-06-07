
```markdown
# Local LLM Chat (Gemma-4-12B on Apple Silicon)

A modular, lightweight, high-performance local LLM chat server optimized for macOS and M-series (M1/M2/M3/M4) GPUs using Apple Metal.

This application runs the **Gemma-4-12B-it** model completely offline on your own hardware using a FastAPI backend and a responsive, streaming web interface.

## Features

- **Apple Silicon GPU Acceleration**: Offloads the entire model structure to your Mac's GPU cores via Metal.
- **Real-Time Streaming**: Tokens render incrementally in your browser as they are generated.
- **Context Preservation & Stream Recovery**: If you interrupt or stop the generator mid-sentence, your chat history retains the partially generated text for seamless multi-turn continuity.
- **Port Manager**: Automatically detects and prompts you to clear port `8000` if it is blocked by a ghost process before starting up.
- **Dual Clean-Logging**: Verbose framework outputs are directed quietly into `server.log`, while your terminal displays only hardware alerts and real-time generation metrics.

## Requirements

- **Operating System**: macOS (Ventura or newer recommended).
- **Processor**: Apple Silicon (M1, M2, M3, or M4 chip).
- **Memory**: 16 GB unified memory minimum (24 GB+ recommended for optimal overhead).
- **Disk Space**: At least 10 GB of free space.

## Directory Structure

```text
Gemma4_12B/
├── app/
│   ├── __init__.py
│   ├── config.py         # Dual logging configuration (Console + File)
│   ├── model.py          # Llama model initialization (Safe GPU offloading)
│   ├── history.py        # Active session state and history managers
│   ├── templates.py      # Frontend HTML template interface
│   └── main.py           # FastAPI initialization and routes
├── install.sh            # Automated compilation & environment setup script
├── run.py                # Programmatic server launcher
├── requirements.txt      # Dependency specification file
├── server.log            # Created automatically on startup (silenced outputs)
└── kill_server.sh        # Port-killer utility script
```

## Installation

1. Ensure you have a file named `requirements.txt` in your project folder with the following contents:

   ```text
   fastapi==0.110.0
   uvicorn==0.27.1
   pydantic==1.10.13
   llama-cpp-python[metal]==0.2.90
   huggingface-hub
   ```
2. Open your terminal in this directory and run the automatic installer:

   ```bash
   ./install.sh
   ```

   *Note: If Xcode Command Line Tools are missing, the script will trigger a pop-up dialog. Complete that installation, then run `./install.sh` again.*

## Running the Server

1. Activate your virtual environment:

   ```bash
   source .venv/bin/activate
   ```
2. Start the programmatic runner script:

   ```bash
   python run.py
   ```

   *On the first run, the script will automatically download the 7.38 GB Gemma-4 GGUF model directly from Hugging Face. Subsequent startups will load instantly from your local cache.*
3. Open your browser and navigate to:
   [**http://127.0.0.1:8000**](http://127.0.0.1:8000)

## System Management

### Viewing Detailed Logs

All server initialization logs, model metadata, and network request logs are written to `server.log`. You can monitor them in real-time in a separate terminal window:

```bash
tail -f server.log
```

### Clearing Ports Manually

If you ever need to manually force-close any processes left hanging on port `8000`, run your utility script:

```bash
./kill_server.sh
```

Or use the direct terminal command:

```bash
kill -9 $(lsof -t -i:8000) 2>/dev/null || echo "No process found on port 8000."
```

```

```
