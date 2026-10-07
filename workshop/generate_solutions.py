#!/usr/bin/env python3
"""Regenerate workshop/solutions/ from mongodb_groceries_agent/agent.py.

The solutions are the cumulative states of the same file, so writing them by
hand means four copies of every fix. They are derived from the finished agent
instead, and CI re-runs this with --check to catch anyone editing a solution
directly.

    python3 workshop/generate_solutions.py            # write
    python3 workshop/generate_solutions.py --check    # fail if stale
"""

import argparse
import ast
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
AGENT = REPO / "mongodb_groceries_agent" / "agent.py"
SOLUTIONS = REPO / "workshop" / "solutions"

PREAMBLE = '''import os

import pymongo
from google.adk.agents import Agent

from mongodb_groceries_agent.embeddings import embed_query
from mongodb_groceries_agent.utils import set_env

PASSKEY = "<ASK YOUR INSTRUCTOR FOR THE PASSKEY>"
set_env(PASSKEY)

CONNECTION_STRING = os.environ.get("CONNECTION_STRING")

'''

# Collection handles, in the order the finished agent declares them. The
# search-only solutions never touch carts, so that pair is dropped for them.
CONSTANTS = '''DATABASE_NAME = "grocery_store"
INVENTORY_COLLECTION_NAME = "inventory"
CARTS_COLLECTION_NAME = "carts"

database_client = pymongo.MongoClient(CONNECTION_STRING)
inventory_collection = database_client[DATABASE_NAME][INVENTORY_COLLECTION_NAME]
carts_collection = database_client[DATABASE_NAME][CARTS_COLLECTION_NAME]
'''

CONSTANTS_SEARCH_ONLY = (
    CONSTANTS.replace('CARTS_COLLECTION_NAME = "carts"\n', "").replace(
        "carts_collection = database_client[DATABASE_NAME][CARTS_COLLECTION_NAME]\n", ""
    )
)

BARE_AGENT = '''# An agent with no tools at all. It cannot reach the inventory, so watch what it
# does when you ask it for a product.
root_agent = Agent(
    model="gemini-3.8-flash",
    name="grocery_shopping_agent",
    description="Helps shoppers find groceries.",
    instruction="",
    tools=[
        # e.g. product search or add-to-cart
    ],
)
'''

SEARCH_ONLY_INSTRUCTION = '''instruction = """
You are the **Online Groceries Agent**, a friendly and helpful virtual assistant for our e-commerce grocery store.
Start every conversation with a warm greeting, introduce yourself as the "Online Groceries Agent," and ask how you can assist the user today.
Your role is to guide customers through their shopping experience.

What you can do:
- Help users discover and explore products in the store.
- Suggest alternatives when the exact item is not available.

Available tools:
1. **find_similar_products**: Search for products with names semantically similar to the user's request.{category_note}

Core guidelines:
- **Always search first**: If a user asks for a product, call `find_similar_products`.
- **Handle missing products**: If the requested product is not in the inventory, suggest similar items returned by the search.
- **Clarify only when necessary**: Ask for more details if the request is unclear and you cannot perform a search.
- Keep your tone positive, approachable, and customer-focused throughout the interaction.

Additional important instructions:
- **Fallback behavior**: If no results are found, apologize politely and encourage the user to try a different product or category.
- **Stay focused**: Only handle product discovery. Politely decline requests unrelated to groceries.
- **Answering product questions**: If the question is about a product, such as "Is this organic?" or "How much does it cost?", use the search results to answer. If the information is not available, say so plainly.
- **Report tool errors**: If a tool returns a "status" of "error", tell the user what went wrong instead of guessing an answer.

Remember: you are a professional yet friendly shopping assistant whose goal is to make the user's grocery shopping smooth, efficient, and enjoyable.
"""
'''

SEARCH_ONLY_AGENT = '''root_agent = Agent(
    model="gemini-3.8-flash",
    name="grocery_shopping_agent",
    description="Helps shoppers find groceries.",
    instruction=instruction,
    tools=[
        find_similar_products,
    ],
)
'''


def top_level(source: str, tree: ast.Module, name: str) -> str:
    """Return the source of the top-level function or assignment called `name`."""
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) + "\n"
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return ast.get_source_segment(source, node) + "\n"
    raise KeyError(f"{name} is not defined at the top level of {AGENT.name}")


def without_category(find_similar_products: str) -> str:
    """Strip the category pre-filter, for the solution that predates it."""
    stripped = find_similar_products.replace(
        'def find_similar_products(query: str, category: str = "") -> dict:',
        "def find_similar_products(query: str) -> dict:",
    )
    stripped = re.sub(
        r"\n        category: Optional\..*?search the whole store\.\n",
        "\n",
        stripped,
        flags=re.S,
    )
    stripped = re.sub(
        r"\n    # Pre-filtering runs.*?\n\n",
        "\n",
        stripped,
        flags=re.S,
    )
    if "category" in stripped:
        raise SystemExit(
            "Could not strip the category pre-filter. The markers this script "
            "keys on in find_similar_products have changed."
        )
    return stripped


def build() -> dict[str, str]:
    source = AGENT.read_text()
    tree = ast.parse(source)

    find = top_level(source, tree, "find_similar_products")
    add = top_level(source, tree, "add_to_cart")
    total = top_level(source, tree, "calculate_cart_total")
    instruction = top_level(source, tree, "instruction")
    root = top_level(source, tree, "root_agent")

    search_only = SEARCH_ONLY_INSTRUCTION + "\n\n" + SEARCH_ONLY_AGENT

    return {
        "01-bare-agent.py": PREAMBLE + BARE_AGENT,
        "02-vector-search.py": (
            PREAMBLE
            + CONSTANTS_SEARCH_ONLY
            + "\n\n"
            + without_category(find)
            + "\n\n"
            + search_only.format(category_note="")
        ),
        "03-filtered-search.py": (
            PREAMBLE
            + CONSTANTS_SEARCH_ONLY
            + "\n\n"
            + find
            + "\n\n"
            + search_only.format(
                category_note=(
                    " Pass a category to restrict the search to one section "
                    "of the store."
                )
            )
        ),
        "04-cart-tools.py": (
            PREAMBLE
            + CONSTANTS
            + "\n\n"
            + find
            + "\n\n"
            + add
            + "\n\n"
            + total
            + "\n\n"
            + instruction
            + "\n\n"
            + root
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if any solution is out of date instead of writing",
    )
    args = parser.parse_args()

    stale = []
    for name, content in build().items():
        ast.parse(content)  # never ship a solution that does not parse
        path = SOLUTIONS / name
        if args.check:
            if not path.exists() or path.read_text() != content:
                stale.append(name)
        else:
            path.write_text(content)
            print(f"wrote {path.relative_to(REPO)}")

    if stale:
        print(
            "These solutions are out of date: "
            + ", ".join(stale)
            + "\nRun: python3 workshop/generate_solutions.py",
            file=sys.stderr,
        )
        return 1

    if args.check:
        print("All solutions are up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
