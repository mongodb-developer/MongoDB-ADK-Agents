# Workshop Instructions

Welcome to the **Google ADK and MongoDB Atlas** workshop! <span aria-hidden="true">🎉</span>
In this workshop, you’ll build a **Grocery Shopping AI agent** step by step. Each exercise combines theory with hands-on practice so you can learn concepts and immediately apply them.

## Exercise 0: Browse the Database

1. On the left-hand sidebar, click on the green leaf icon to open the MongoDB extension.
2. From the extension page, click on **Local MongoDB Atlas** to connect to the MongoDB database. 
3. Explore the **grocery_store** database and the **inventory** collection provided.
4. Open a few documents and notice their structure.

**<span aria-hidden="true">👉</span> Question to consider:**
1. What information about the products stands out to you?
2. How could this data be useful to a shopping agent?
3. Are there any unusual fields in the documents?

## Exercise 1: Initialize the Agent with Google ADK

In this step, you’ll create your first AI Agent with ADK. At this stage, the agent won’t have any tools — which means it won’t be able to do much yet. This will demonstrate why tools are essential.

1. Open the file `mongodb_groceries_agent/agent.py`.

1. You’ll see a few Python imports. You’ll use these later to implement the tools. You'll also see a placeholder for a passkey:

    ```
    PASSKEY = "<ASK YOUR INSTRUCTOR FOR THE PASSKEY>"
    ```

    Ask your instructor for the passkey and replace the placeholder with it. This passkey authenticates you to the Google API for this workshop, so you don’t need to provide your own API key—we’ve created one for you.

1. With the API key in place, you’re ready to create your first agent. Add the following code to the file:

    ```python
    root_agent = Agent(
        model="gemini-2.5-flash",     # The LLM your agent will use
        name="grocery_shopping_agent",# A name for your agent
        instruction="",               # You’ll define the agent’s instructions later
        tools=[                       # Empty for now; you’ll add tools later
            # e.g. product search or add-to-cart
        ]
    )
    ```

    Explanation of each field:

    * **model** — The LLM powering the agent (here, Gemini 2.5 Flash).
    * **name** — A unique identifier for your agent instance.
    * **instruction** — A system message that defines how the agent should behave (you’ll fill this in later).
    * **tools** — Python functions that the agent can call (currently empty).

1. Run the following command in the terminal to start the ADK development UI:

    ```
    adk web
    ```

    You should see:

    ```
    INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
    ```

1. Hold CMD (Mac) or CTRL (Windows/Linux) and click on the link: http://127.0.0.1:8000.

    This opens the development UI where you can chat with your agent.

1. Test your Agent

    Try asking your agent:

    ```
    Find me sourdough bread in the inventory.
    ```

    **What happens?**
    Since the agent doesn’t have any tools yet, it cannot actually access the database. Instead, it might:

    - Make up a product that doesn’t exist in the database.
    - Ask you follow up questions about which inventory you're referring to.
    - Attempt to search the web for an answer.

    Neither of these behaviors is desirable — you want the agent to only use the grocery store inventory.

    **<span aria-hidden="true">👉</span> Discussion point:**
    What risks do you see if an agent makes up products or fetches information from outside sources instead of the inventory?

## Exercise 2: Find Similar Products with MongoDB Atlas Vector Search  

In this exercise, you’ll add a tool that lets the agent find products relevant to a user’s question. To do this, you’ll use **vector search**, which compares product embeddings to a user query and returns semantically similar results.  

### Step 1: Generate Embeddings  

1. Open the MongoDB extension by clicking the green MongoDB leaf in the sidebar.  
2. Expand the **Local MongoDB Atlas** connection, then the **grocery_store** database and finally, the **inventory** collection.  
3. Open any MongoDB document from the **inventory** collection. Notice the **gemini_embedding** field: it already contains the product’s vector embedding. 

We pre-generated these embeddings to save time and resources. Otherwise, every workshop attendee would need to re-run the same embedding process—producing identical vectors at unnecessary cost. For this exercise, you can work directly with the stored vectors.  

***Hint***: Don't close the document—you'll need it for the next steps.

### Step 2: Create a Vector Search Index

A vector search index is a special data structure optimized for similarity searches. It allows MongoDB to efficiently compare vectors and return the closest matches.

> **<span aria-hidden="true">📗</span> Extra credit:** If you’d like to dive deeper into how vector search indexes work in MongoDB, check out [this video](https://www.youtube.com/watch?v=AvCuiRs2cxw).

**<span aria-hidden="true">💡</span> Key things to know:**
- You only need to create the index once. As new documents with vectors are added, MongoDB keeps the index updated automatically.  
- You can create the index from any MongoDB driver, the MongoDB Shell, or directly in Atlas. For this workshop, you’ll define it programmatically using the Python driver, which makes the process reproducible.

#### Task: Update the Vector Creation Script  

Open **`mongodb_groceries_agent/create-vector-search-index.py`** and fill in the placeholders:  

1. `<DATABASE_NAME>`: the name of the database that you explored through the MongoDB extension
2. `<COLLECTION_NAME>`: the collection with grocery products  
3. `<VECTOR_FIELD_IN_THE_DOCUMENT>`: the name of the field storing the vector embedding
4. `<LENGTH_OF_THE_VECTOR>`: the size of the embedding array.
    - ***Hint***: The size is one of 128, 256, 512, 768, 1536, or 2048. Check the number of lines in the MongoDB document you opened earlier.
5. `<VECTOR_SEARCH_DEFINITION>`: use the predefined variable in the script and pass it into the method  

Stop the running process in the terminal by pressing CTRL+C. Then, execute the vector creation script:

```bash
python mongodb_groceries_agent/create-vector-search-index.py
```

After a 10-second timeout, the script will display the collection’s search indexes. Pay attention to the status of the index you just created—it may show as ***BUILDING*** or ***READY***. The collection has only 5000 documents, so by the time you start using the index, it will be fully built with status ***READY***.

### Step 3: Implement the Vector Search Tool

With the index in place, let’s implement the search tool that the agent will use to find similar products.

In this step, you’ll:  
- Define a helper function to generate embeddings with Gemini. The function will be used to transform the user questions into vector embeddings.
- Implement the `find_similar_products` tool that performs a vector search against the MongoDB `inventory` collection. 
- Register the tool with the agent so it becomes part of the shopping workflow. 

Open **`mongodb_groceries_agent/agent.py`** and replace the `root_agent` variable with the following code.

**<span aria-hidden="true">️⚠️</span> Important**: Don't delete the imports or the `GOOGLE_API_KEY` variable!

```python
# Initialize the GenAI client to vectorize the user queries
genai_client = genai.Client()
# Initialize the MongoDB client to communicate with the database
CONNECTION_STRING = os.environ.get("CONNECTION_STRING")
database_client = pymongo.MongoClient(CONNECTION_STRING)

DATABASE_NAME = "grocery_store"
INVENTORY_COLLECTION_NAME = "inventory"

# 3. Helper function: Generate embeddings for a user query
def generate_embeddings(query):
    """Generate embeddings for the user query using the Gemini embedding model."""
    result = genai_client.models.embed_content(
        model="gemini-embedding-001",
        contents=query,
        # 1. Replace with the desired size of the vector. This should match the vector size in the document.
        config=types.EmbedContentConfig(output_dimensionality=<OUTPUT_VECTOR_SIZE>) 
    )
    return result.embeddings[0].values

# 4. Tool: Perform a vector search against MongoDB Atlas
def find_similar_products(query: str) -> str:
    """Search for products with names semantically similar to the query.

    Args:
        query: The user’s request (e.g., product name or description).
    Returns:
        A list of product documents with details (excluding embeddings).
    """
    vector_embeddings = generate_embeddings(query)

    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",  # <-- Leave as it is. This is the name of the index you created in Step 2
                "path": "<VECTOR_FIELD_IN_THE_DOCUMENT>",  # <-- 2. Replace with the document field that holds the vector embedding
                "queryVector": vector_embeddings,
                "numCandidates": 100,
                "limit": 10
            },
        },
        {
            "$project": {
                "_id": 0,
                # 3. Replace with the document field the holds the embedding. This will reduce the network traffic and the tokens the agent needs to include in LLM prompt.
                "<VECTOR_FIELD_IN_THE_DOCUMENT>": 0  
            }
        }
    ]

    try:
        documents = database_client[DATABASE_NAME][INVENTORY_COLLECTION_NAME].aggregate(pipeline).to_list()
        return documents
    except pymongo.errors.OperationFailure:
        return "Failed to find similar products."

instruction = """
You are the **Online Groceries Agent**, a friendly and helpful virtual assistant for our e-commerce grocery store. 
Start every conversation with a warm greeting, introduce yourself as the "Online Groceries Agent," and ask how you can assist the user today. 
Your role is to guide customers through their shopping experience.

What you can do:
- Help users discover and explore products in the store.
- Suggest alternatives when the exact item is not available.

Available tools:
1. **find_similar_products**: Search for products with names semantically similar to the user’s request.  
Core guidelines:
- **Always search first**: If a user asks for a product, call `find_similar_products`.  
- **Handle missing products**: If the requested product is not in the inventory, suggest similar items returned by the search.  
- **Clarify only when necessary**: Ask for more details if the request is unclear and you cannot perform a search.  
- Keep your tone positive, approachable, and customer-focused throughout the interaction.  

Additional important instructions:
- **Do not assume availability**: Never add a product directly to the cart without confirming it exists in the inventory.  
- **Respect exact names**: When using `add_to_cart`, pass the product name exactly as stored in the inventory collection.  
- **Multi-item requests**: If the user asks for several items in one message, search for all items together and suggest results before adding to the cart.  
- **Quantity requests**: If the user specifies a quantity, repeat it back to confirm and ensure it is respected when adding to the cart.  
- **Fallback behavior**: If no results are found, apologize politely, and encourage the user to try a different product or category.  
- **Stay focused**: Only handle product discovery. Politely decline requests unrelated to groceries.  
- **Answering product questions**: If the question is about a product (e.g., "Is this organic?" or "How much does it cost?"), use the search results to answer. If the information is not available, respond transparently that you don’t have that detail.  

Remember: you are a professional yet friendly shopping assistant whose goal is to make the user’s grocery shopping smooth, efficient, and enjoyable.
"""

# 5. Define the agent and register the tools
root_agent = Agent(
    model="gemini-2.5-flash",
    name="grocery_shopping_agent",
    instruction=instruction,
    tools=[
        <TOOL_FUNCTION_NAME> # <-- 4. Replace with the product search function declared above.
    ]
)
```

Replace any of the placeholders with the correct values:
    1. `<OUTPUT_VECTOR_SIZE>` - Replace with the desired size of the vector. This should match the vector size in the document.
    2. `<VECTOR_FIELD_IN_THE_DOCUMENT` — Replace with the document field that holds the vector embedding
    3. `<VECTOR_FIELD_IN_THE_DOCUMENT>` (again) — Replace with the document field the holds the embedding. This will reduce the network traffic and the tokens the agent needs to include in LLM prompt.
    4.  `<TOOL_FUNCTION_NAME>` - Replace with the product search function declared above.

Finally, start the agent development server again with the following command:

```
adk web
```

Hold CMD (Mac) or CTRL (Windows/Linux) and click on the link: http://127.0.0.1:8000. Once again, this opens the development UI where you can chat with your agent.

Try asking your agent:

```
Find me sourdough bread in the inventory.
```

**<span aria-hidden="true">👉</span> Discussion point:**
Does the agent respond in a different way? Is it running any tools? What happens when you click on the tool execution boxes?

## Exercise 3: Add to Cart and Calculate Cart Total  

In this exercise, you’ll extend the agent with two new tools that make it possible to manage a shopping cart in MongoDB:  

1. **`add_to_cart`** – adds products to a user’s cart.  
2. **`calculate_cart_total`** – sums the total cost of products in the cart.  

The cart will be stored in a separate MongoDB collection called **carts**, identified by the username of the shopper. This will require the agent to ask for an username. In a real application, you'd need to implement authorization first.

### Step 1: Implement the Tools  

Open **`mongodb_groceries_agent/agent.py`** and add the following code after the definition of the `find_similar_products` function (around line 75).

The code below contains placeholders that you’ll need to replace with the correct variables or methods. Updating these ensures that the tools work correctly with your database and collections.

```python

def add_to_cart(product: str, username: str) -> str:
    """Add a product to the user's cart in MongoDB.
    This function retrieves the product from the inventory collection and adds it to the user's cart.
    Args:
      product: The name of the product to add. The product name should match the name in the inventory collection.
      username: The name of the user.
    
    Returns:
      Success or failure message.
    """
    products_collection = database_client[DATABASE_NAME][INVENTORY_COLLECTION_NAME]
    product_document = <COLLECTION_NAME>.find_one( # <--- 1. Replace with the collection name defined on the previous line
        {"product": <PRODUCT_NAME>}, # <--- 2. Replace with the product name passed as an argument to the function
        {
            # Return only these three fields
            "product": 1,
            "sale_price": 1,
            "category": 1
        }
    )

    if (not product_document):
        return f"Product {product} not found in the inventory."

    # Add the product to the user's cart
    # If the user does not have a cart, create one
    # If the user has a cart, add the product to the existing cart
    # The cart is stored in a separate collection "carts"
    # The cart is identified by the username of the user
    if not username:
        return "Username is required to add a product to the cart."

    cart_collection = database_client[DATABASE_NAME][CARTS_COLLECTION_NAME]
    cart_collection.update_one(
        {"username": username},
        {"$addToSet": {"products": <PRODUCT_DOCUMENT>}}, # <-- 3. Replace with the product document variable defined above
        upsert=True
    )

    return f"Product {product_document['product']} added to your cart."

def calculate_cart_total(username: str) -> str:
    """Calculates the total price of all products in the user cart.
    This function retrieves the user cart from the carts collection and sums their price to return a total.
    Args:
      username: The name of the user.
    
    Returns:
      Total price
    """
    cart_document = database_client[DATABASE_NAME][CARTS_COLLECTION_NAME].<FIND_METHOD>( # <-- 4. Replace with the correct collection method to find one document
        {"username": username},
        {
            "_id": 0,
            "products": 1
        }
    )

    total = 0
    for product in cart_document["products"]:
        total = total + product["sale_price"]

    return total
```

Replace the placeholders:
1. <COLLECTION_NAME> – Replace with the collection variable defined on the previous line.
2. <PRODUCT_NAME> – Replace with the product argument passed into the function.
3. <PRODUCT_DOCUMENT> – Replace with the product_document variable defined earlier in the function.
4. <FIND_METHOD> – Replace with the correct collection method to find a single document.

### Step 2: Update the Agent

Now, update the agent's instruction to explain its new capabilities and add the new tools to the list of tools.

```python
instruction="""
You are the **Online Groceries Agent**, a friendly and helpful virtual assistant for our e-commerce grocery store. 
Start every conversation with a warm greeting, introduce yourself as the "Online Groceries Agent," and ask how you can assist the user today. 
Your role is to guide customers through their shopping experience.

What you can do:
- Help users discover and explore products in the store.
- Suggest alternatives when the exact item is not available.
- Add products to the user’s shopping cart.
- Answer product-related questions in a clear and concise way.
- Return the total in the user’s shopping cart.

Available tools:
1. **find_similar_products**: Search for products with names semantically similar to the user’s request.  
2. **add_to_cart**: Add a product to the user’s cart in MongoDB. Pass only the product name (as it appears in the inventory collection) and the user’s username.  
3. **calculate_cart_total**: Sum the total of all products in a user's cart and return it. Pass the user’s username.

Core guidelines:
- **Always search first**: If a user asks for a product, call `find_similar_products` before attempting to add it to the cart.  
- **Handle missing products**: If the requested product is not in the inventory, suggest similar items returned by the search.  
- **Parallel tool use**: You may call multiple tools in parallel when appropriate (e.g., searching for several items at once).  
- **Clarify only when necessary**: Ask for more details if the request is unclear and you cannot perform a search.  
- Keep your tone positive, approachable, and customer-focused throughout the interaction.  

Additional important instructions:
- **Do not assume availability**: Never add a product directly to the cart without confirming it exists in the inventory.  
- **Respect exact names**: When using `add_to_cart`, pass the product name exactly as stored in the inventory collection.  
- **Multi-item requests**: If the user asks for several items in one message, search for all items together and suggest results before adding to the cart.  
- **Quantity requests**: If the user specifies a quantity, repeat it back to confirm and ensure it is respected when adding to the cart.  
- **Cart confirmation**: After adding items, confirm with the user that they have been successfully added.  
- **Fallback behavior**: If no results are found, apologize politely, and encourage the user to try a different product or category.  
- **Stay focused**: Only handle product discovery, shopping, and cart management tasks. Politely decline requests unrelated to groceries.  
- **Answering product questions**: If the question is about a product (e.g., "Is this organic?" or "How much does it cost?"), use the search results to answer. If the information is not available, respond transparently that you don’t have that detail.  

Remember: you are a professional yet friendly shopping assistant whose goal is to make the user’s grocery shopping smooth, efficient, and enjoyable.
"""

root_agent = Agent(
    model="gemini-2.5-flash",
    name="grocery_shopping_agent",
    instruction=instruction,
    tools=[
        find_similar_products,
        # 5. Add the two new tools to the list
        <ADD_TO_CART_TOOL>,
        <CALCULATE_TOTAL_TOOL>
    ]
)
```

Replace the two placeholders at the bottom:
- `<ADD_TO_CART_TOOL>`
- `<CALCULATE_TOTAL_TOOL>`


Stop the running process in the terminal by pressing `Ctrl+C`. Then, run the dev server command again:

```
adk web
```

Test the agent. Here are a few sample prompts:

```
- Add milk, flour, and chocolate to my cart.
- Show me the best-rated products.
- I want to bake a chocolate cake—find me the ingredients I’ll need.
- What’s the total cost of my cart?
```

## Final

🎉 Congratulations—you’ve completed the exercises!

Complete the short assessment to claim your **AI Agents with MongoDB Skill Badge** here: [mdb.link/adk-london-badge](https://mdb.link/adk-london-badge).
