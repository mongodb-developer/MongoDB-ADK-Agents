"""Generate and store an embedding for every inventory document.

Run once, after loading the dataset and before creating the vector search index.
Documents that already have an embedding are skipped, so re-running after a
failure picks up where it left off.
"""

import os

import pymongo
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Must match EMBEDDING_MODEL and EMBEDDING_DIMENSIONS in agent.py. Changing
# either means re-embedding everything: the two models' vector spaces are not
# compatible, and the search index pins numDimensions.
EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSIONS = 1536

genai_client = genai.Client()


def embed_documents(documents: list[dict]) -> list[list[float]]:
    """Embed inventory documents for storage, one vector per document.

    Args:
        documents: Inventory documents, each with a `product` and `description`.

    Returns:
        One embedding per input document, in the same order.
    """
    texts = [
        f"title: {doc.get('product') or 'none'} | text: {doc.get('description', '')}"
        for doc in documents
    ]
    # One Content per input, each holding a single Part. Several Parts inside one
    # Content are aggregated into a single vector instead, with no error, so the
    # nesting here is load-bearing rather than ceremony.
    result = genai_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[
            types.Content(parts=[types.Part.from_text(text=text)]) for text in texts
        ],
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS),
    )
    return [embedding.values for embedding in result.embeddings]


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
