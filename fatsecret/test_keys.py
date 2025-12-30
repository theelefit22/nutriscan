import os
from fatsecret import Fatsecret
from dotenv import load_dotenv

load_dotenv()

def test_keys():
    key = os.environ.get("FATSECRET_CONSUMER_KEY")
    secret = os.environ.get("FATSECRET_CONSUMER_SECRET")
    
    if not key or not secret:
        print("Error: FATSECRET_CONSUMER_KEY or FATSECRET_CONSUMER_SECRET environment variables are not set.")
        return

    try:
        fs = Fatsecret(key, secret)
        print("Authenticating with FatSecret...")
        # A simple food search as a check
        results = fs.foods_search("apple")
        if results:
            print("Successfully connected! Found 'apple' results.")
        else:
            print("Connected, but no results found for 'apple'.")
    except Exception as e:
        print(f"Authentication Failed: {e}")

if __name__ == "__main__":
    test_keys()
