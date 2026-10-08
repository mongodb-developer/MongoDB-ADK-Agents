"""Embedding helpers shared by the indexing script and the agent.

Query and document vectors have to come from the same model, at the same
dimensionality, with the same task prefix. Keeping both callers on these two
functions is what guarantees that.
"""

from google import genai
from google.genai import types

# gemini-embedding-2 auto-normalizes truncated dimensions, so the vectors it
# returns are unit length and the index can use the cheaper dotProduct
# similarity. gemini-embedding-001 only did that at its full 3072 dimensions —
# below that you had to divide by the L2 norm yourself, and skipping it quietly
# degraded results under dotProduct. Changing either of these constants means
# re-embedding the whole collection: the two models' vector spaces are not
# compatible, and the index pins numDimensions.
EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSIONS = 1536

_genai_client = None


def _client() -> genai.Client:
    """The GenAI client, built on first use.

    Not built at import time on purpose. The workshop agent calls
    set_env(PASSKEY) to put GOOGLE_API_KEY in the environment, and that runs
    after this module is imported. genai.Client() raises if no key is set yet,
    so constructing one here would break the import that sets the key.
    """
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client()
    return _genai_client


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
    result = _client().models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[
            types.Content(parts=[types.Part.from_text(text=text)]) for text in texts
        ],
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS),
    )
    return [embedding.values for embedding in result.embeddings]


def embed_query(query: str) -> list[float]:
    """Embed a user query for retrieval against the stored document vectors.

    Args:
        query: What the shopper asked for.

    Returns:
        A single embedding.
    """
    # gemini-embedding-2 has no task_type parameter. The task goes in the text,
    # and the query prefix has to pair with the document prefix used above —
    # otherwise queries and documents land in different regions of the space.
    result = _client().models.embed_content(
        model=EMBEDDING_MODEL,
        contents=f"task: search result | query: {query}",
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS),
    )
    return result.embeddings[0].values
