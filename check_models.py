
import os
from google import genai

os.environ["GOOGLE_API_KEY"] = "AIzaSyAbvEK1y6UN-ZIu56R4b-ItOY1LVfrMGo0"

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
try:
    print("Listing models...")
    for model in client.models.list(config={"query_base": True}):
        print(model.name)
except Exception as e:
    print(f"Error: {e}")
