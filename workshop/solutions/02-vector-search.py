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

# gemini-embedding-2 returns unit-length vectors, which is what lets the index
# use dotProduct. Both constants must match the ones used to embed the
# inventory, or queries and products land in different vector spaces.
EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSIONS = 1536

genai_client = genai.Client()


DATABASE_NAME = "grocery_store"
INVENTORY_COLLECTION_NAME = "inventory"

database_client = pymongo.MongoClient(CONNECTION_STRING)
inventory_collection = database_client[DATABASE_NAME][INVENTORY_COLLECTION_NAME]


def embed_query(query: str) -> list[float]:
    """Turn the shopper's words into a vector.

    Args:
        query: What the shopper asked for.

    Returns:
        A single embedding.
    """
    # This model has no task_type parameter: the task goes in the text. The
    # query prefix pairs with the "title: ... | text: ..." prefix used when the
    # products were embedded.
    result = genai_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=f"task: search result | query: {query}",
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS),
    )
    return result.embeddings[0].values

def find_similar_products(query: str) -> dict:
    """Search for products semantically similar to the query.

    Args:
        query: What the shopper is looking for, such as a product name or a
            description. For example "organic apples" or "something sweet".

    Returns:
        A dict with a "status" key, and on success a "products" list.
    """
    search_stage = {
        "index": "vector_index",
        "path": "embedding",
        "queryVector": embed_query(query),
        "numCandidates": 100,
        "limit": 10,
    }

    pipeline = [
        {"$vectorSearch": search_stage},
        # The embedding itself is large and of no use to the model. Everything
        # else, price included, is fair game for answering questions.
        {"$project": {"_id": 0, "embedding": 0}},
    ]

    try:
        products = list(inventory_collection.aggregate(pipeline))
    except pymongo.errors.OperationFailure as error:
        return {
            "status": "error",
            "error_message": f"The product search failed: {error}",
        }

    return {"status": "success", "products": products}


instruction = """
You are the **Online Groceries Agent**, a friendly and helpful virtual assistant for our e-commerce grocery store.
Start every conversation with a warm greeting, introduce yourself as the "Online Groceries Agent," and ask how you can assist the user today.
Your role is to guide customers through their shopping experience.

What you can do:
- Help users discover and explore products in the store.
- Suggest alternatives when the exact item is not available.

Available tools:
1. **find_similar_products**: Search for products with names semantically similar to the user's request.

Core guidelines:
- **Always search first**: If a user asks for a product, call `find_similar_products`.
- **Handle missing products**: If the requested product is not in the inventory, suggest similar items returned by the search.
- **Clarify only when necessary**: Ask for more details if the request is unclear and you cannot perform a search.
- Keep your tone positive, approachable, and customer-focused throughout the interaction.

Additional important instructions:
- **Fallback behavior**: If no results are found, apologize politely and encourage the user to try a different product or category.
- **Stay focused**: Only handle product discovery. Politely decline requests unrelated to groceries.
- **Answering product questions**: If the question is about a product, such as "Is this organic?" or "How much does it cost?", use the search results to answer. If the information is not available, say so plainly.
- **Report tool errors**: If a tool returns a "status" of "error", tell the user what went wrong instead of guessing an answer.

Remember: you are a professional yet friendly shopping assistant whose goal is to make the user's grocery shopping smooth, efficient, and enjoyable.
"""


root_agent = Agent(
    model="gemini-3.5-flash",
    name="grocery_shopping_agent",
    description="Helps shoppers find groceries.",
    instruction=instruction,
    tools=[
        find_similar_products,
    ],
)
