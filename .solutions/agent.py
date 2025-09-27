import os
import pymongo
import certifi
from google.adk.agents import Agent
from google import genai
from google.genai import types

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
CONNECTION_STRING = os.environ.get("CONNECTION_STRING")
DATABASE_NAME = "grocery_store"
INVENTORY_COLLECTION_NAME = "inventory"
CARTS_COLLECTION_NAME = "carts"

genai_client = genai.Client()
database_client = pymongo.MongoClient(CONNECTION_STRING, tlsCAFile=certifi.where())

def generate_embeddings(query):
    result = genai_client.models.embed_content(
        model="gemini-embedding-001",
        contents=query
    )

    return result.embeddings[0].values

def find_similar_products(query: str) -> str:
    """Searches for products with a product name semantically similar to a given product.
    Returns a list of three similar products along with their project IDs.

    Args:
        query: A string containing the user's query about ecommerce products.
            This can be a product name, description, or any other relevant information related to the
            products in the ecommerce database.
    Example:
        query = "organic apples"
    Example:
        query = "sweet treats"
    Returns:
        A list of dictionaries, each containing the product name and other relevant details.
    """

    vector_embeddings = generate_embeddings(query)

    pipeline = [
        {
            # Perform a vector search to find similar products
            # using the vector search index "inventory_vector_index"
            # and the embedding field "embedding"
            # The query vector is generated from the user's query
            # and we limit the results to 10 candidates
            "$vectorSearch": {
                "index": "vector_index",
                "path": "gemini_embedding",
                "queryVector": vector_embeddings,
                "numCandidates": 100,
                "limit": 10
            },
        },
        {
            # Exclude the embedding and price fields from the results
            "$project": {
                "_id": 0,
                "sale_price": 0,
                "gemini_embedding": 0
            }
        }
    ]

    try :
        # Execute the aggregation pipeline to find similar products
        # The result will be a list of products with their details
        documents = database_client[DATABASE_NAME][INVENTORY_COLLECTION_NAME].aggregate(pipeline).to_list()
        return documents
    except pymongo.errors.OperationFailure as e:
        return "Failed to find similar products."

def add_to_cart(product: str, username: str) -> str:
    """Add a product to the user's cart in MongoDB.
    This function retrieves the product from the inventory collection and adds it to the user's cart.
    Args:
      product: The name of the product to add. The product name should match the name in the inventory collection.
      username: The name of the user.
    
    Returns:
      Success or failure message.
    """
    products_collection = database_client[DATABASE_NAME][INVENTORY_COLLECTION_NAME]
    product_document = products_collection.find_one(
        {"product": product},
        {
            "product": 1,
            "sale_price": 1,
            "category": 1
        }
    )

    if (not product_document):
        return f"Product {product} not found in the inventory."

    # Add the product to the user's cart
    # If the user does not have a cart, create one
    # If the user has a cart, add the product to the existing cart
    # The cart is stored in a separate collection "carts"
    # The cart is identified by the username of the user
    if not username:
        return "Username is required to add a product to the cart."

    cart_collection = database_client[DATABASE_NAME][CARTS_COLLECTION_NAME]
    cart_collection.update_one(
        {"username": username},
        {"$addToSet": {"products": product_document}},
        upsert=True
    )

    return f"Product {product_document['product']} added to your cart."

def calculate_cart_total(username: str) -> str:
    """Calculates the total price of all products in the user cart.
    This function retrieves the user cart from the carts collection and sums their price to return a total.
    Args:
      username: The name of the user.
    
    Returns:
      Total price
    """
    cart_document = database_client[DATABASE_NAME][CARTS_COLLECTION_NAME].find_one(
        {"username": username},
        {
            "_id": 0,
            "products": 1
        }
    )

    total = 0
    for product in cart_document["products"]:
        total = total + product["sale_price"]

    return total


root_agent = Agent(
    model="gemini-2.5-flash",
    name="grocery_shopping_agent",
    instruction=""" 
You are the **Online Groceries Agent**, a friendly and helpful virtual assistant for our e-commerce grocery store. 
Start every conversation with a warm greeting, introduce yourself as the "Online Groceries Agent," and ask how you can assist the user today. 
Your role is to guide customers through their shopping experience.

What you can do:
- Help users discover and explore products in the store.
- Suggest alternatives when the exact item is not available.
- Add products to the user’s shopping cart.
- Answer product-related questions in a clear and concise way.
- Return the total in the user’s shopping cart.

Available tools:
1. **find_similar_products**: Search for products with names semantically similar to the user’s request.  
2. **add_to_cart**: Add a product to the user’s cart in MongoDB. Pass only the product name (as it appears in the inventory collection) and the user’s username.  
3. **calculate_cart_total**: Sum the total of all products in a user's cart and return it. Pass the user’s username.

Core guidelines:
- **Always search first**: If a user asks for a product, call `find_similar_products` before attempting to add it to the cart.  
- **Handle missing products**: If the requested product is not in the inventory, suggest similar items returned by the search.  
- **Parallel tool use**: You may call multiple tools in parallel when appropriate (e.g., searching for several items at once).  
- **Clarify only when necessary**: Ask for more details if the request is unclear and you cannot perform a search.  
- Keep your tone positive, approachable, and customer-focused throughout the interaction.  

Additional important instructions:
- **Do not assume availability**: Never add a product directly to the cart without confirming it exists in the inventory.  
- **Respect exact names**: When using `add_to_cart`, pass the product name exactly as stored in the inventory collection.  
- **Multi-item requests**: If the user asks for several items in one message, search for all items together and suggest results before adding to the cart.  
- **Quantity requests**: If the user specifies a quantity, repeat it back to confirm and ensure it is respected when adding to the cart.  
- **Cart confirmation**: After adding items, confirm with the user that they have been successfully added.  
- **Fallback behavior**: If no results are found, apologize politely, and encourage the user to try a different product or category.  
- **Stay focused**: Only handle product discovery, shopping, and cart management tasks. Politely decline requests unrelated to groceries.  
- **Answering product questions**: If the question is about a product (e.g., "Is this organic?" or "How much does it cost?"), use the search results to answer. If the information is not available, respond transparently that you don’t have that detail.  

Remember: you are a professional yet friendly shopping assistant whose goal is to make the user’s grocery shopping smooth, efficient, and enjoyable.
    """ ,
    tools=[
        find_similar_products,
        add_to_cart,
        calculate_cart_total
    ]
)
