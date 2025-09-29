import os
import pymongo
import certifi
from google.adk.agents import Agent
from google import genai
from google.genai import types
from utils import set_env

PASSKEY = "<ASK YOUR INSTRUCTOR FOR THE PASSKEY>"
set_env(PASSKEY)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
