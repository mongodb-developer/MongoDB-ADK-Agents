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
CARTS_COLLECTION_NAME = "carts"

database_client = pymongo.MongoClient(CONNECTION_STRING)
inventory_collection = database_client[DATABASE_NAME][INVENTORY_COLLECTION_NAME]
carts_collection = database_client[DATABASE_NAME][CARTS_COLLECTION_NAME]


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

def find_similar_products(query: str, category: str = "") -> dict:
    """Search for products semantically similar to the query.

    Args:
        query: What the shopper is looking for, such as a product name or a
            description. For example "organic apples" or "something sweet".
        category: Optional. Restrict results to a single product category,
            spelled exactly as it appears in the inventory. Leave empty to
            search the whole store.

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

    # Pre-filtering runs before the vector comparison, so the candidates that
    # come back are already restricted to the category. It does not affect
    # vectorSearchScore, and filtered queries are typically slower than the
    # equivalent unfiltered one.
    if category:
        search_stage["filter"] = {"category": {"$eq": category}}

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


def add_to_cart(product: str, username: str, quantity: int = 1) -> dict:
    """Add a product to the user's cart.

    Args:
        product: The product name, exactly as stored in the inventory.
        username: The name of the user whose cart to add to.
        quantity: How many to add. Defaults to 1.

    Returns:
        A dict with a "status" key, and on success the updated cart line.
    """
    # `username` arrives from the model, which is fine for a workshop and wrong
    # for production: the model can get it wrong, and nothing stops one shopper
    # from naming another's cart. Real deployments read the identity from the
    # session (ToolContext.state), where the model cannot reach it.
    if not username:
        return {
            "status": "error",
            "error_message": "A username is required to add a product to the cart.",
        }

    if quantity < 1:
        return {
            "status": "error",
            "error_message": "Quantity must be at least 1.",
        }

    product_document = inventory_collection.find_one(
        {"product": product},
        {"_id": 0, "product": 1, "sale_price": 1, "category": 1},
    )

    if not product_document:
        return {
            "status": "error",
            "error_message": (
                f"'{product}' is not in the inventory. "
                "Search for it first and use the exact name from the results."
            ),
        }

    # Two writes rather than one: bump the quantity if the product is already in
    # the cart, otherwise append it. $addToSet cannot do this — a second add of
    # the same product is silently a no-op, so quantity could never go above 1.
    updated = carts_collection.update_one(
        {"username": username, "products.product": product},
        {"$inc": {"products.$.quantity": quantity}},
    )

    if updated.matched_count == 0:
        carts_collection.update_one(
            {"username": username},
            {"$push": {"products": {**product_document, "quantity": quantity}}},
            upsert=True,
        )

    return {
        "status": "success",
        "product": product_document["product"],
        "quantity_added": quantity,
    }


def calculate_cart_total(username: str) -> dict:
    """Calculate the total price of everything in the user's cart.

    Args:
        username: The name of the user whose cart to total.

    Returns:
        A dict with a "status" key, and on success the cart "total".
    """
    # Let the database do the arithmetic. Summing in Python means pulling every
    # line item back just to add up one field.
    pipeline = [
        {"$match": {"username": username}},
        {"$unwind": "$products"},
        {
            "$group": {
                "_id": None,
                "total": {
                    "$sum": {
                        "$multiply": ["$products.sale_price", "$products.quantity"]
                    }
                },
                "item_count": {"$sum": "$products.quantity"},
            }
        },
    ]

    results = list(carts_collection.aggregate(pipeline))

    # No cart yet, or a cart with nothing in it. Both are ordinary states, not
    # errors — the carts collection is emptied at the start of this challenge.
    if not results:
        return {"status": "success", "total": 0, "message": "Your cart is empty."}

    return {
        "status": "success",
        "total": results[0]["total"],
        "item_count": results[0]["item_count"],
    }


instruction = """
You are the **Online Groceries Agent**, a friendly and helpful virtual assistant for our e-commerce grocery store.
Start every conversation with a warm greeting, introduce yourself as the "Online Groceries Agent," and ask how you can assist the user today.
Your role is to guide customers through their shopping experience.

What you can do:
- Help users discover and explore products in the store.
- Suggest alternatives when the exact item is not available.
- Add products to the user's shopping cart.
- Answer product-related questions in a clear and concise way.
- Return the total in the user's shopping cart.

Available tools:
1. **find_similar_products**: Search for products with names semantically similar to the user's request. Pass a category to restrict the search to one section of the store.
2. **add_to_cart**: Add a product to the user's cart. Pass the product name, the user's username, and the quantity.
3. **calculate_cart_total**: Sum the total of all products in a user's cart. Pass the user's username.

Core guidelines:
- **Always search first**: If a user asks for a product, call `find_similar_products` before attempting to add it to the cart.
- **Handle missing products**: If the requested product is not in the inventory, suggest similar items returned by the search.
- **Parallel tool use**: You may call multiple tools in parallel when appropriate, such as searching for several items at once.
- **Clarify only when necessary**: Ask for more details if the request is unclear and you cannot perform a search.
- Keep your tone positive, approachable, and customer-focused throughout the interaction.

Additional important instructions:
- **Do not assume availability**: Never add a product to the cart without confirming it exists in the inventory.
- **Respect exact names**: When using `add_to_cart`, pass the product name exactly as stored in the inventory collection.
- **Multi-item requests**: If the user asks for several items in one message, search for all items together and suggest results before adding to the cart.
- **Quantity requests**: If the user specifies a quantity, repeat it back to confirm and pass it to `add_to_cart`.
- **Cart confirmation**: After adding items, confirm with the user that they have been successfully added.
- **Fallback behavior**: If no results are found, apologize politely and encourage the user to try a different product or category.
- **Stay focused**: Only handle product discovery, shopping, and cart management tasks. Politely decline requests unrelated to groceries.
- **Answering product questions**: If the question is about a product, such as "Is this organic?" or "How much does it cost?", use the search results to answer. If the information is not available, say so plainly.
- **Report tool errors**: If a tool returns a "status" of "error", tell the user what went wrong instead of guessing an answer.

Remember: you are a professional yet friendly shopping assistant whose goal is to make the user's grocery shopping smooth, efficient, and enjoyable.
"""


root_agent = Agent(
    model="gemini-3.8-flash",
    name="grocery_shopping_agent",
    description=(
        "Helps shoppers find groceries, answer questions about them, and manage "
        "their shopping cart."
    ),
    instruction=instruction,
    tools=[
        find_similar_products,
        add_to_cart,
        calculate_cart_total,
    ],
)
