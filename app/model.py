import contextlib
from llama_cpp import Llama
from app.config import logger, Console

logger.info("Initializing model loading process...")
Console.info("Loading Gemma-4-12B model onto Apple M4 GPU...")

try:
    # Temporarily redirect all stdout and stderr (including python prints) to server.log
    with open("server.log", "a", encoding="utf-8") as f:
        with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
            llm = Llama.from_pretrained(
                repo_id="ggml-org/gemma-4-12B-it-GGUF",
                filename="gemma-4-12B-it-Q4_K_M.gguf",
                n_gpu_layers=-1,         # Offload all layers to your M4 GPU
                n_ctx=4096,              # Standard optimized context window
                n_threads=8,             # Match physical cores
                flash_attn=False,        # Stable attention for Gemma 2/4
                f16_kv=True,             # Optimized KV cache
                verbose=False            # Silence C++ level output
            )
    
    logger.info("Model loaded successfully.")
    Console.success("Hardware Offload: Active (Apple M4 GPU via Metal)")
    Console.success("Model loaded successfully. Server is ready.")
    
except Exception as e:
    logger.error(f"Error during model initialization: {str(e)}")
    Console.warn("GPU initialization failed. Falling back to CPU instead.")
    
    # Fallback to CPU-only load if GPU fails, also redirected silently to server.log
    with open("server.log", "a", encoding="utf-8") as f:
        with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
            llm = Llama.from_pretrained(
                repo_id="ggml-org/gemma-4-12B-it-GGUF",
                filename="gemma-4-12B-it-Q4_K_M.gguf",
                n_gpu_layers=0,          # Force CPU execution
                n_ctx=4096,
                n_threads=8,
                flash_attn=False,
                f16_kv=True,
                verbose=False
            )
    Console.success("Model loaded successfully using CPU fallback.")