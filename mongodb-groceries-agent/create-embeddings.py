import vertexai
from vertexai.language_models import TextEmbeddingModel
import pymongo
import os
from dotenv import load_dotenv
import certifi

load_dotenv()

def generate_embeddings(query):
    vertexai.init(project="gcp-pov", location="us-central1")

    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    embeddings = model.get_embeddings([query])
    return embeddings[0].values

connection_string = os.environ.get("CONNECTION_STRING")
client = pymongo.MongoClient(os.environ.get("CONNECTION_STRING"), tlsCAFile=certifi.where())
docs = client["grocery_store"]["inventory"].find({"embedding": {"$exists": False}}).to_list()

print(len(docs))

for doc in docs:
    if "embedding" not in doc:
        print(f"Generating embeddings for {doc["product"]}")
        product = doc["product"]
        description = doc.get("description", "")
        embedding = generate_embeddings(product + " " + description)
        # Update the document with the new embedding
        client["grocery_store"]["inventory"].update_one(
            {"_id": doc["_id"]},
            {"$set": {"embedding": embedding}}
        )
    else:
        print(f"Embedding already exist for {doc["name"]}")

