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
    """Search for products with name and description semantically similar to a given product.
    Returns a list of three similar products along with their project IDs.

    Args:
      user query about ecommerce products: str

    Returns:
      List of similar products with their IDs.
    """
    client = pymongo.MongoClient(CONNECTION_STRING, tlsCAFile=certifi.where())
    vector_embeddings = generate_embeddings(query)
    pipeline = [
        {
            "$vectorSearch": {
                "index": "inventory_vector_index",
                "path": "embedding",
                "queryVector": vector_embeddings,
                "numCandidates": 100,
                "limit": 10
            },
        },
        {
            "$project": {
                "_id": 0,
                "sale_price": 0,
                "market_price": 0,
                "embedding": 0,
            }
        }
    ]

    documents = client[DATABASE_NAME][COLLECTION_NAME].aggregate(pipeline).to_list()

    return documents

def add_to_cart(product: str, username: str) -> str:
    """Add a product to the user's cart in MongoDB.
    Args:
      product: The name of the product to add.
      username: The name of the user.
    
    Returns:
      Success or failure message.
    """
    client = pymongo.MongoClient(CONNECTION_STRING, tlsCAFile=certifi.where())
    products_collection = client[DATABASE_NAME][COLLECTION_NAME]
    product = products_collection.find_one({"product": product})

    cart_collection = client[DATABASE_NAME]["carts"]
    cart_collection.update_one({"username": username}, {"$addToSet": {"products": product}}, upsert=True)

    return f"Product {product} added to your cart."


root_agent = Agent(
    model="gemini-2.0-flash",
    name="grocery_shopping_agent",
    instruction=""" 
Start the Conversation with the user being a positive and friendly agent. Introduce yourself as the "Online Groceries Agent" and ask user how can you help them today. You are a customer agent for an ecommerce company and you are here to help the user with their shopping needs.

Additional instructions:
1. Ask for details only if you don't understand the query and are not able to search.
2. You can use multiple tools in parallel by calling functions in parallel.
    """ ,
    tools=[
        find_similar_products,
        add_to_cart
    ]
)
