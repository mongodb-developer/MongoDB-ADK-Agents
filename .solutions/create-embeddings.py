import pymongo
import os
from dotenv import load_dotenv
import certifi
from google import genai

load_dotenv()

# Gemini connection
geni_client = genai.Client()

def generate_embeddings(queries):
    """Generate embeddings for a batch of queries."""
    result = geni_client.models.embed_content(
        model="gemini-embedding-001",
        contents=queries,  # list of strings
    )
    return [embedding.values for embedding in result.embeddings]


# MongoDB connection
connection_string = os.environ.get("CONNECTION_STRING")
mongodb_client = pymongo.MongoClient(connection_string, tlsCAFile=certifi.where())

# Get documents without embeddings
docs = list(mongodb_client["grocery_store"]["inventory"].find({"gemini_embedding": {"$exists": False}}))
print(f"Found {len(docs)} documents without embeddings")

BATCH_SIZE = 50  # adjust depending on API quota/limits

for i in range(0, len(docs), BATCH_SIZE):
    batch = docs[i:i + BATCH_SIZE]
    queries = [f"{doc.get('product', '')} {doc.get('description', '')}" for doc in batch]

    print(f"Generating embeddings for batch {i // BATCH_SIZE + 1} with {len(batch)} items")
    embeddings = generate_embeddings(queries)

    # Update each doc with its corresponding embedding
    print(f"Updating documents for batch {i // BATCH_SIZE + 1} with {len(batch)} items")
    for doc, embedding in zip(batch, embeddings):
        mongodb_client["grocery_store"]["inventory"].update_one(
            {"_id": doc["_id"]},
            {"$set": {"gemini_embedding": embedding}}
        )
