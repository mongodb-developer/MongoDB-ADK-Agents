# MongoDB Groceries Agent

An AI grocery-shopping agent built with [Google ADK](https://adk.dev) and MongoDB
Vector Search. The agent finds products semantically, answers questions about
them, and manages a shopping cart.

Check out the [Medium tutorial](https://medium.com/google-cloud/build-a-python-ai-agent-in-15-minutes-with-google-adk-and-mongodb-atlas-vector-search-groceries-b6c4af017629) for a walkthrough.

## Features

- Semantic product search with MongoDB Vector Search and Gemini embeddings
- Category pre-filtering, so a search can be scoped to one section of the store
- Cart management, with quantities, backed by MongoDB

## Prerequisites

- Python 3.10+
- A Gemini API key ([AI Studio](https://aistudio.google.com/apikey))
- A MongoDB Atlas cluster (instructions below)

## Setup

### 1. Create a free MongoDB Atlas cluster

- Go to [MongoDB Atlas](https://mongodb.com/try?utm_campaign=devrel&utm_source=github&utm_medium=cta&utm_content=google-cloud-adk-grocery-agent&utm_term=stanimira.vlaeva) and sign up.
- Click "Build a Database" and choose the free tier (M0).
- Create a database user, and add your IP to the IP Access List.
- Click "Connect" > "Connect your application" to get your connection string.

### 2. Clone and install

```bash
git clone https://github.com/mongodb-developer/MongoDB-ADK-Agents.git
cd MongoDB-ADK-Agents
pip install -r requirements.txt
```

### 3. Set environment variables

Create a `.env` file in the repository root:

```bash
GOOGLE_GENAI_USE_VERTEXAI=FALSE
CONNECTION_STRING="your MongoDB connection string"
GOOGLE_API_KEY="your Gemini API key"
```

### 4. Load the dataset

`dataset.csv` holds 27,555 products. With a 1536-dimension vector on each one,
the embedded collection runs to roughly 550 MB, which does not fit the free
tier's 512 MB, and embedding all of them is 27,555 API calls.

For a free cluster, load a subset. 5,000 products is plenty to see semantic
search work. Product descriptions contain line breaks, so take the subset with
a CSV parser rather than `head`, which would cut a record in half:

```bash
python3 -c "
import csv, itertools
with open('mongodb_groceries_agent/dataset.csv', newline='') as src, \
     open('/tmp/subset.csv', 'w', newline='') as dst:
    reader, writer = csv.reader(src), csv.writer(dst)
    writer.writerows(itertools.islice(reader, 5001))
"

mongoimport --uri "$CONNECTION_STRING" --db grocery_store --collection inventory \
  --type csv --headerline --file /tmp/subset.csv
```

On a cluster with room for it, swap `/tmp/subset.csv` for the full
`mongodb_groceries_agent/dataset.csv`.

### 5. Generate embeddings

```bash
python mongodb_groceries_agent/create-embeddings.py
```

This embeds every product with `gemini-embedding-2` at 1536 dimensions and
stores the vector in an `embedding` field. Documents that already have one are
skipped, so it is safe to re-run after an interruption or after loading more
products.

### 6. Create the vector search index

```bash
python mongodb_groceries_agent/create-vector-search-index.py
```

The script waits until the index is queryable. It creates:

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 1536,
      "similarity": "dotProduct"
    },
    { "type": "filter", "path": "category" }
  ]
}
```

`dotProduct` works here because `gemini-embedding-2` returns unit-length vectors,
including at truncated dimensions. If you switch to a model that does not
normalize, such as `gemini-embedding-001` below its full 3072 dimensions, either
normalize the vectors yourself or use `cosine`, which ignores magnitude.
Using `dotProduct` on unnormalized vectors degrades results silently.

No quantization is configured: it starts paying off above roughly 100,000
vectors, and this dataset is smaller than that.

### 7. Run the agent

```bash
adk web
```

Run it from the repository root, not from inside `mongodb_groceries_agent/`.
ADK looks for agent packages in the directory you launch it from. Then open
http://127.0.0.1:8000 and pick `mongodb_groceries_agent`.

## Project structure

| Path | What it is |
|---|---|
| `mongodb_groceries_agent/agent.py` | The agent and its tools |
| `mongodb_groceries_agent/embeddings.py` | Embedding helpers shared by the agent and the indexer |
| `mongodb_groceries_agent/create-embeddings.py` | Embeds the inventory |
| `mongodb_groceries_agent/create-vector-search-index.py` | Creates the vector search index |
| `mongodb_groceries_agent/utils.py` | Workshop passkey helper |
| `mongodb_groceries_agent/dataset.csv` | The product dataset |
| `workshop/` | Starter and solution files for the instructor-led lab. See [workshop/README.md](workshop/README.md) |

## Notes

- `username` is passed to the cart tools as a regular argument, which keeps the
  workshop simple. In production, read the identity from the session
  (`ToolContext.state`) instead: anything the model supplies, the model can get
  wrong, and nothing stops one user from naming another's cart.
