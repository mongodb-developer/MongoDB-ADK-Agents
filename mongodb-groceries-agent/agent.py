import os
import pymongo
import certifi
import vertexai
from google.adk.agents import Agent
from vertexai.language_models import TextEmbeddingModel

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
PROJECT_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION")
DATABASE_NAME = os.environ.get("DATABASE_NAME")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME")
CONNECTION_STRING = os.environ.get("CONNECTION_STRING")

def generate_embeddings(query):
    vertexai.init(project=PROJECT_ID, location=PROJECT_LOCATION)

    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    embeddings = model.get_embeddings([query])
    return embeddings[0].values

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
    client = pymongo.MongoClient(CONNECTION_STRING, tlsCAFile=certifi.where())
    vector_embeddings = generate_embeddings(query)
    pipeline = [
        {
            # Perform a vector search to find similar products
            # using the vector search index "inventory_vector_index"
            # and the embedding field "embedding"
            # The query vector is generated from the user's query
            # and we limit the results to 10 candidates
            "$vectorSearch": {
                "index": "inventory_vector_index",
                "path": "embedding",
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
                "market_price": 0,
                "embedding": 0,
            }
        }
    ]

    try :
        # Execute the aggregation pipeline to find similar products
        # The result will be a list of products with their details
        documents = client[DATABASE_NAME][COLLECTION_NAME].aggregate(pipeline).to_list()
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
    client = pymongo.MongoClient(CONNECTION_STRING, tlsCAFile=certifi.where())
    products_collection = client[DATABASE_NAME][COLLECTION_NAME]
    product_document = products_collection.find_one(
        {"product": product},
        {
            "_id": 0,
            "product": 1,
            "sale_price": 1,
            "market_price": 1,
            "description": 1
        }
    )

    if (not product):
        return f"Product {product} not found in the inventory."

    # Add the product to the user's cart
    # If the user does not have a cart, create one
    # If the user has a cart, add the product to the existing cart
    # The cart is stored in a separate collection "carts"
    # The cart is identified by the username of the user
    if not username:
        return "Username is required to add a product to the cart."

    cart_collection = client[DATABASE_NAME]["carts"]
    cart_collection.update_one(
        {"username": username},
        {"$addToSet": {"products": product_document}},
        upsert=True
    )

    return f"Product {product_document['product']} added to your cart."


root_agent = Agent(
    model="gemini-2.0-flash",
    name="grocery_shopping_agent",
    instruction=""" 
Start the Conversation with the user being a positive and friendly agent. Introduce yourself as the "Online Groceries Agent" and ask user how can you help them today. You are a customer agent for an ecommerce company and you are here to help the user with their shopping needs.

You can help the user find products, add products to their cart, and answer any questions they may have about the products.
You can use the following tools to help the user:
1. find_similar_products: Search for products with a product name semantically similar to a given product.
2. add_to_cart: Add a product to the user's cart in MongoDB. Only pass the product name, matching the name in the inventory collection, and the username of the user.

Always search for products first before adding them to the cart. If the user asks for a product that is not in the inventory, you can suggest similar products based on their query.
You can use the tools in parallel to help the user find products and add them to their cart.

Additional instructions:
1. Ask for details only if you don't understand the query and are not able to search.
2. You can use multiple tools in parallel by calling functions in parallel.
    """ ,
    tools=[
        find_similar_products,
        add_to_cart
    ]
)
