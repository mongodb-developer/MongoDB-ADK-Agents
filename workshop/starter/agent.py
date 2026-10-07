import os

import pymongo
from google.adk.agents import Agent
from google import genai
from google.genai import types

from mongodb_groceries_agent.utils import set_env

PASSKEY = "<ASK YOUR INSTRUCTOR FOR THE PASSKEY>"
set_env(PASSKEY)

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
CONNECTION_STRING = os.environ.get("CONNECTION_STRING")

# You will build the agent here, one challenge at a time.
