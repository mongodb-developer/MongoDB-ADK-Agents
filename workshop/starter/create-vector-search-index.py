"""Create the vector search index on the inventory collection.

You only do this once. MongoDB keeps the index up to date as documents change.

Fill in the placeholders marked below, then run:

    python3 mongodb_groceries_agent/create-vector-search-index.py
"""

import os
import pprint
import time

import pymongo

CONNECTION_STRING = os.environ.get("CONNECTION_STRING")
database_client = pymongo.MongoClient(CONNECTION_STRING)

DATABASE_NAME = "<DATABASE_NAME>"      # <-- 1. The database you explored
COLLECTION_NAME = "<COLLECTION_NAME>"  # <-- 2. The collection holding the products

collection = database_client[DATABASE_NAME][COLLECTION_NAME]

index_definition = {
    "name": "vector_index",
    "type": "vectorSearch",
    "definition": {
        "fields": [
            {
                "type": "vector",
                # 3. The field holding the embedding array
                "path": "<VECTOR_FIELD_IN_THE_DOCUMENT>",
                # 4. How many numbers are in that array?
                "numDimensions": <LENGTH_OF_THE_VECTOR>,
                # 5. "euclidean", "cosine" or "dotProduct"? euclidean measures
                #    distance between the vectors' endpoints; cosine measures the
                #    angle and ignores length; dotProduct measures both, which is
                #    cheaper than cosine but only correct when every vector has a
                #    length of exactly 1. Check the embedding model's docs before
                #    you choose.
                "similarity": "<SIMILARITY_FUNCTION>",
            },
            # Indexed separately so $vectorSearch can pre-filter on it. You will
            # use this in the next challenge.
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
# 6. Pass the variable defined above
collection.create_search_index(<VECTOR_SEARCH_DEFINITION>)

print("Waiting for the index to be queryable. This may take up to a minute...")
while True:
    indexes = list(collection.list_search_indexes("vector_index"))
    if indexes and indexes[0].get("queryable"):
        break
    time.sleep(5)

print("The index is ready to query:")
pprint.pp(indexes)
