import os
import pymongo
import time
import os
import pprint

CONNECTION_STRING = os.environ.get("CONNECTION_STRING")
database_client = pymongo.MongoClient(CONNECTION_STRING)

DATABASE_NAME = "<DATABASE_NAME>" # <-- 1. Insert the correct database name here
COLLECTION_NAME = "<COLLECTION_NAME>" # <-- 2. Insert the correct collection name here

collection = database_client[DATABASE_NAME][COLLECTION_NAME]

index_definition = {
  "name": "vector_index",
  "type": "vectorSearch",
  "definition": {
    "fields": [
      {
        "path": "<VECTOR_FIELD_IN_THE_DOCUMENT>", # <-- 3. Insert the correct field name here
        "numDimensions": <LENGTH_OF_THE_VECTOR>, # <-- 4. Insert the correct vector length here
        "similarity": "cosine",
        "type": "vector"
      }
    ]
  }
}

print("Creating the vector search index...")
collection.create_search_index(<VECTOR_SEARCH_DEFINITION>) # <-- 5. Use the variable defined above

print("Waiting 10 seconds for the index to finish building...")
time.sleep(10)

indexes = list(collection.list_search_indexes())
print("Search indexes: ")
pprint.pp(indexes)
