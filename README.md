# MongoDB VertexAI Groceries Agent

This project provides an AI-powered agent for grocery shopping, leveraging MongoDB for data storage and Google Vertex AI for semantic search and embeddings.

Check out the [Medium tutorial](https://medium.com/google-cloud/build-a-python-ai-agent-in-15-minutes-with-google-adk-and-mongodb-atlas-vector-search-groceries-b6c4af017629) for more information.

## Features
- Semantic product search using MongoDB Atlas Vector Search and Vertex AI embeddings
- Add products to user carts in MongoDB

## Prerequisites
- Python 3.10+
- Access to Google Cloud Gemini API
- Access to a MongoDB Atlas cluster (instructions below)
- Required Python packages (instructions below)
- Google ADK Python installed (instructions below)

## Loading the Dataset and Generating Embeddings

1. **Create a free MongoDB Atlas cluster**

- Go to [MongoDB Atlas](https://mongodb.com/try?utm_campaign=devrel&utm_source=github&utm_medium=cta&utm_content=google-cloud-adk-grocery-agent&utm_term=stanimira.vlaeva) and sign up for a free account.
- Click "Build a Database" and choose the free tier (Shared, M0).
- Select your preferred cloud provider and region, then click "Create".
- Create a database user with a username and password.
- Add your IP address to the IP Access List (or allow access from anywhere for development).
- Once the cluster is created, click "Connect" and choose "Connect your application" to get your connection string. Use this string for the `CONNECTION_STRING` environment variable in the next steps.

2. **Clone the repository**

```bash
git clone https://github.com/mongodb-developer/MongoDB-ADK-Agents.git
cd MongoDB-VertexAI-ADK
```

3. **Load the Dataset into MongoDB Atlas**

Import the provided dataset into your MongoDB database using the following command (replace placeholders as needed):

```bash
mongoimport --uri "$CONNECTION_STRING" --db "$DATABASE_NAME" --collection "$COLLECTION_NAME" --type csv --headerline --file mongodb_groceries_agent/dataset.csv
```

4. **Generate Embeddings for the Inventory**

After loading the data, you need to generate vector embeddings for each product. Run the following script:

```bash
python mongodb_groceries_agent/create-embeddings.py
```

This will process all products in the collection and add/update the embedding field required for semantic search.

5. **Build a Vector Search Index for the Inventory**

Open the **Search and Vector Search** tab in the left sidebar in Atlas and create a vector search index on the inventory collection with the following definition:

```bash
{
  "fields": [
    {
      "numDimensions": 3072,
      "path": "gemini_embedding",
      "similarity": "cosine",
      "type": "vector"
    }
  ]
}
```

## Setup

1. **Install the Python dependencies**

```bash
pip install -r requirements.txt
```

2. **Install the ADK CLI**

Follow the [official ADK installation instructions](https://google.github.io/adk-docs/get-started/installation/) or run:

```bash
pip install google-adk
```

3. **Set environment variables**

Set the following environment variables in a `.env` file:

```bash
GOOGLE_GENAI_USE_VERTEXAI=FALSE

# Follow the guide: https://www.mongodb.com/docs/guides/atlas/connection-string/
CONNECTION_STRING="Your MongoDB connection string"
# Follow the guide: https://cloud.google.com/api-keys/docs/create-manage-api-keys
GOOGLE_API_KEY="Your Google Cloud API key"
```

5. **Run the agent using ADK**

Navigate to the `mongodb_groceries_agent` directory and run:

```bash
adk web
```

6. Open the web server running at `http://127.0.0.1:8000` and start using the application! 

## Usage
- The agent will start and be ready to handle product search and cart operations.
- You can extend the agent with new tools or integrate it into a larger application.

## Project Structure
- `mongodb_groceries_agent/agent.py`: Main agent logic
- `mongodb_groceries_agent/create-embeddings.py`: Utility for creating embeddings
- `mongodb_groceries_agent/dataset.csv`: Example dataset

## Notes
- Ensure your Google Cloud and MongoDB credentials are valid and have the necessary permissions.
- For local development, you may want to use a virtual environment.
- The ADK CLI is required for running and managing agents.

## License
See [LICENSE](LICENSE) for details.
