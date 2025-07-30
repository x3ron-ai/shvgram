import os

def get_config():
    return {
        "API_HASH": os.getenv("API_HASH"),
        "API_ID": os.getenv("API_ID"),
    }
