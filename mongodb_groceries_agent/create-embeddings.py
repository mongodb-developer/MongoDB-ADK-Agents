"""Generate and store an embedding for every inventory document.

Run once, after loading the dataset and before creating the vector search index.
Documents that already have an embedding are skipped, so re-running after a
failure picks up where it left off.
"""

import os

import pymongo
from dotenv import load_dotenv

from mongodb_groceries_agent.embeddings import EMBEDDING_DIMENSIONS, embed_documents

load_dotenv()

DATABASE_NAME = "grocery_store"
COLLECTION_NAME = "inventory"
EMBEDDING_FIELD = "embedding"
BATCH_SIZE = 50

connection_string = os.environ.get("CONNECTION_STRING")
mongodb_client = pymongo.MongoClient(connection_string)
collection = mongodb_client[DATABASE_NAME][COLLECTION_NAME]

documents = list(collection.find({EMBEDDING_FIELD: {"$exists": False}}))
print(f"Found {len(documents)} documents without embeddings")

for start in range(0, len(documents), BATCH_SIZE):
    batch = documents[start : start + BATCH_SIZE]
    batch_number = start // BATCH_SIZE + 1

    print(f"Embedding batch {batch_number} ({len(batch)} documents)")
    embeddings = embed_documents(batch)

    # Getting back fewer vectors than documents is silent otherwise, and would
    # write one document's embedding onto another document. Cheap to assert.
    if len(embeddings) != len(batch):
        raise RuntimeError(
            f"Expected {len(batch)} embeddings, got {len(embeddings)}. "
            "Each input needs its own types.Content: several Parts in one "
            "Content are aggregated into a single vector."
        )

    collection.bulk_write(
        [
            pymongo.UpdateOne(
                {"_id": document["_id"]},
                {"$set": {EMBEDDING_FIELD: embedding}},
            )
            for document, embedding in zip(batch, embeddings)
        ]
    )

print(
    f"Done. Stored {EMBEDDING_DIMENSIONS}-dimensional embeddings "
    f"in '{EMBEDDING_FIELD}'."
)
