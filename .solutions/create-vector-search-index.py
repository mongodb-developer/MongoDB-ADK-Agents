import os
import pymongo
import time
import os
import pprint

CONNECTION_STRING = os.environ.get("CONNECTION_STRING")
database_client = pymongo.MongoClient(CONNECTION_STRING)
collection = database_client["grocery_store"]["inventory"]

index_definition = {
  "name": "vector_index",
  "type": "vectorSearch",
  "definition": {
    "fields": [
      {
        "numDimensions": 768,
        "path": "gemini_embedding",
        "similarity": "cosine",
        "type": "vector"
      }
    ]
  }
}

print("Creating the vector search index...")
collection.create_search_index(index_definition)

print("Waiting 10 seconds for the index to finish building...")
time.sleep(10)

indexes = list(collection.list_search_indexes())
print("Search indexes: ")
pprint.pp(indexes)
