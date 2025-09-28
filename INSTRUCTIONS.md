# Workshop Instructions

Welcome to the **Google ADK and MongoDB Atlas** workshop! <span aria-hidden="true">🎉</span>
In this workshop, you’ll build a **Grocery Shopping AI agent** step by step. Each exercise combines theory with hands-on practice so you can learn concepts and immediately apply them.

## Exercise 0: Browse the Database

1. On the left-hand sidebar, click on the green leaf icon to open the MongoDB extension.
2. From the extension page, click on **Groceries Database** to connect to the MongoDB database. 
3. Explore the database and collections provided.
4. Open a few documents and notice their structure.

**<span aria-hidden="true">👉</span> Question to consider:**
1. What information about the products stands out to you?
2. How could this data be useful to a shopping agent?
3. Are there any unusual fields in the documents?

## Exercise 1: Initialize the Agent

In this step, you’ll create your first AI Agent with ADK. At this stage, the agent won’t have any tools — which means it won’t be able to do much yet. This will demonstrate why tools are essential.

1. Open the file `mongodb-groceries-agent/agent.py`.

2. You’ll see a few Python imports. You’ll use these later to implement the tools. Add the following code after the imports:

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
    * **name** → A unique identifier for your agent instance.
    * **instruction** → A system message that defines how the agent should behave (you’ll fill this in later).
    * **tools** → Python functions that the agent can call (currently empty).

3. Run the following command in the terminal to start the ADK development UI:

    ```
    adk web
    ```

    You should see:

    ```
    INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
    ```

4. Hold CMD (Mac) or CTRL (Windows/Linux) and click on the link: http://127.0.0.1:8000.

    This opens the development UI where you can chat with your agent.

5. Test your Agent

    Try asking your agent:

    ```
    Find me sourdough bread in the inventory.
    ```

    **What happens?**
    Since the agent doesn’t have any tools yet, it cannot actually access the database. Instead, it might:
        - Make up a product that doesn’t exist in the database.
        - Ask you follow up questions about which inventory you're referring to.
        - Attempt to search the web for an answer.

    Neither of these behaviors is desirable — we want the agent to only use our inventory.

    **<span aria-hidden="true">👉</span> Discussion point:**
    What risks do you see if an agent makes up products or fetches information from outside sources instead of the inventory?

