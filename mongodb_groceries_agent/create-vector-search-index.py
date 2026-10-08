"""Create the vector search index on the inventory collection.

You only do this once. MongoDB keeps the index up to date as documents change.
"""

import os
import pprint
import time

import pymongo

CONNECTION_STRING = os.environ.get("CONNECTION_STRING")
database_client = pymongo.MongoClient(CONNECTION_STRING)

DATABASE_NAME = "grocery_store"
COLLECTION_NAME = "inventory"

collection = database_client[DATABASE_NAME][COLLECTION_NAME]

index_definition = {
    "name": "vector_index",
    "type": "vectorSearch",
    "definition": {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": 1536,
                # One of euclidean, cosine or dotProduct. dotProduct here
                # because gemini-embedding-2 returns unit-length vectors, and it
                # is cheaper than cosine for those. For embeddings that are not
                # normalized, use cosine: it ignores magnitude, where dotProduct
                # does not.
                #
                # No quantization: it starts paying off above ~100k vectors and
                # this collection holds 5,000.
                "similarity": "dotProduct",
            },
            # Indexed separately so $vectorSearch can pre-filter on it.
            {"type": "filter", "path": "category"},
        ]
    },
}

# Check the declaration against the data before creating anything. A dimension
# mismatch is not an error: mongot silently skips every document whose vector is
# a different length, so the index reports READY and queryable over nothing, and
# searches come back empty with no clue why.
sample = collection.find_one({}, {index_definition["definition"]["fields"][0]["path"]: 1})
if not sample:
    raise SystemExit(f"{DATABASE_NAME}.{COLLECTION_NAME} is empty.")

field = index_definition["definition"]["fields"][0]["path"]
stored = sample.get(field)
if stored is None:
    raise SystemExit(
        f"No '{field}' field in {DATABASE_NAME}.{COLLECTION_NAME}. "
        f"Document has: {', '.join(k for k in sample if k != '_id')}"
    )

declared = index_definition["definition"]["fields"][0]["numDimensions"]
if len(stored) != declared:
    raise SystemExit(
        f"numDimensions is {declared} but '{field}' holds {len(stored)} numbers. "
        f"Set numDimensions to {len(stored)} and run this again."
    )

print("Creating the vector search index...")
collection.create_search_index(index_definition)

print("Waiting for the index to be queryable. This may take up to a minute...")
while True:
    indexes = list(collection.list_search_indexes("vector_index"))
    if indexes and indexes[0].get("queryable"):
        break
    time.sleep(5)

print("The index is ready to query:")
pprint.pp(indexes)
