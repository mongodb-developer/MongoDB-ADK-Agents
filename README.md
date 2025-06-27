# MongoDB VertexAI Groceries Agent

This project provides an AI-powered agent for grocery shopping, leveraging MongoDB for data storage and Google Vertex AI for semantic search and embeddings.

Check out the [Medium tutorial](https://medium.com/google-cloud/build-a-python-ai-agent-in-15-minutes-with-google-adk-and-mongodb-atlas-vector-search-groceries-b6c4af017629) for more information.

## Features
- Semantic product search using MongoDB Atlas Vector Search and Vertex AI embeddings
- Add products to user carts in MongoDB

## Prerequisites
- Python 3.10+
- Access to Google Cloud Vertex AI
- Access to a MongoDB Atlas cluster (instructions below)
- Required Python packages (instructions below)
- [Google ADK CLI](https://github.com/google/adk) installed (instructions below)

## Loading the Dataset and Generating Embeddings

1. **Create a free MongoDB Atlas cluster**

- Go to [MongoDB Atlas](https://mongodb.com/try?utm_campaign=devrel&utm_source=github&utm_medium=cta&utm_content=google-cloud-adk-grocery-agent&utm_term=stanimira.vlaeva) and sign up for a free account.
- Click "Build a Database" and choose the free tier (Shared, M0).
- Select your preferred cloud provider and region, then click "Create".
- Create a database user with a username and password.
- Add your IP address to the IP Access List (or allow access from anywhere for development).
- Once the cluster is created, click "Connect" and choose "Connect your application" to get your connection string. Use this string for the `CONNECTION_STRING` environment variable in the next steps.

2. **Load the Dataset into MongoDB**

Import the provided dataset into your MongoDB database using the following command (replace placeholders as needed):

```bash
mongoimport --uri "$CONNECTION_STRING" --db "$DATABASE_NAME" --collection "$COLLECTION_NAME" --type csv --headerline --file mongodb-groceries-agent/dataset.csv
```

3. **Generate Embeddings for the Inventory**

After loading the data, you need to generate vector embeddings for each product. Run the following script:

```bash
python mongodb-groceries-agent/create-embeddings.py
```

This will process all products in the collection and add/update the embedding field required for semantic search.


## Setup

1. **Clone the repository**

```bash
git clone <your-repo-url>
cd MongoDB-VertexAI-ADK
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Install the ADK CLI**

Follow the [official ADK installation instructions](https://github.com/google/adk#installation) or run:

```bash
pip install google-adk
```

4. **Set environment variables**

Set the following environment variables (e.g., in your shell or a `.env` file):

- `GOOGLE_CLOUD_PROJECT`: Your Google Cloud project ID
- `GOOGLE_CLOUD_LOCATION`: Your Google Cloud region (e.g., `us-central1`)
- `DATABASE_NAME`: The MongoDB database name (e.g., `grocery_store`)
- `COLLECTION_NAME`: The MongoDB collection name (e.g., `inventory`)
- `CONNECTION_STRING`: Your MongoDB Atlas connection string

Example (for bash/zsh):

```bash
export GOOGLE_CLOUD_PROJECT=your-gcp-project
export GOOGLE_CLOUD_LOCATION=us-central1
export DATABASE_NAME=grocery_store
export COLLECTION_NAME=inventory
export CONNECTION_STRING="mongodb+srv://<user>:<password>@<cluster-url>/"
```

5. **Run the agent using ADK**

Navigate to the `mongodb-groceries-agent` directory and run:

```bash
adk web
```

## Usage
- The agent will start and be ready to handle product search and cart operations.
- You can extend the agent with new tools or integrate it into a larger application.

## Project Structure
- `mongodb-groceries-agent/agent.py`: Main agent logic
- `mongodb-groceries-agent/create-embeddings.py`: Utility for creating embeddings
- `mongodb-groceries-agent/dataset.csv`: Example dataset

## Notes
- Ensure your Google Cloud and MongoDB credentials are valid and have the necessary permissions.
- For local development, you may want to use a virtual environment.
- The ADK CLI is required for running and managing agents.

## License
See [LICENSE](LICENSE) for details.
