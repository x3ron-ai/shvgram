from dotenv import load_dotenv
from shvclient.main import main
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)
if __name__ == "__main__":
    main()