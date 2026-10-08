import os

import pymongo
from google.adk.agents import Agent
from google import genai
from google.genai import types

from mongodb_groceries_agent.utils import set_env

# set_env puts GOOGLE_API_KEY and CONNECTION_STRING in the environment, so it
# has to run before anything that reads them.
PASSKEY = "<ASK YOUR INSTRUCTOR FOR THE PASSKEY>"
set_env(PASSKEY)

CONNECTION_STRING = os.environ.get("CONNECTION_STRING")

# An agent with no tools at all. It cannot reach the inventory, so watch what it
# does when you ask it for a product.
root_agent = Agent(
    model="gemini-3.8-flash",
    name="grocery_shopping_agent",
    description="Helps shoppers find groceries.",
    instruction="",
    tools=[
        # e.g. product search or add-to-cart
    ],
)
