import os
import sys
from huggingface_hub import HfApi

REPO_ID = "masahiroid/DeepSeek-Coder-V2-Lite-Instruct-Pyrite-2bit-GGUF"
GGUF_DIR = "/Volumes/NVMe2TB/AI-LLM/LLMjp/Pyrite/gguf_repo"

def main():
    api = HfApi()
    print(f"Ensuring repository exists: {REPO_ID}")
    api.create_repo(repo_id=REPO_ID, repo_type="model", exist_ok=True)
    print("Repository ready. Starting upload of files in", GGUF_DIR)
    
    commit_info = api.upload_folder(
        folder_path=GGUF_DIR,
        repo_id=REPO_ID,
        repo_type="model",
        commit_message="Initial release: DeepSeek-Coder-V2-Lite-Instruct Pyrite 2-bit GGUF + Q2_K baseline",
    )
    print("Upload completed successfully!")
    print("Commit:", commit_info)

if __name__ == "__main__":
    main()

