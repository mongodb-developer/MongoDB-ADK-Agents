#!/bin/bash
#
# Load the product catalogue. Embeddings are NOT generated here: that needs a
# Gemini API key, which only you have. Run create-embeddings.py once the
# container is up, as the README describes.

set -euo pipefail

URI="mongodb://admin:mongodb@localhost:27017/?authSource=admin&directConnection=true"

echo "Waiting for MongoDB..."
for attempt in $(seq 60); do
    if mongosh --quiet "$URI" --eval 'db.adminCommand({ping: 1}).ok' >/dev/null 2>&1; then
        break
    fi
    if [ "$attempt" -eq 60 ]; then
        echo "MongoDB never accepted connections." >&2
        exit 1
    fi
    sleep 2
done

echo "Importing the product catalogue..."
mongoimport --uri "$URI" \
    --db grocery_store \
    --collection inventory \
    --drop \
    --type csv \
    --headerline \
    --file mongodb_groceries_agent/dataset.csv

cat <<'NEXT'

Catalogue loaded. Two steps left, both documented in the README:

  python3 mongodb_groceries_agent/create-embeddings.py
  python3 mongodb_groceries_agent/create-vector-search-index.py

Both need GOOGLE_API_KEY and CONNECTION_STRING in your .env.
NEXT
