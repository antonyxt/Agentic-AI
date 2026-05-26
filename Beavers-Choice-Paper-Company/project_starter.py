import pandas as pd
import numpy as np
import os
import time
import dotenv
import ast
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union
from sqlalchemy import create_engine, Engine

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.tools import Tool
from pydantic_ai.settings import ModelSettings
from pydantic import BaseModel
from typing import Dict, Literal
import json

# Create an SQLite database
db_engine = create_engine("sqlite:///munder_difflin.db")

# List containing the different kinds of papers 
paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",              "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},  # per plate
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},  # per cup
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},  # per napkin
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},  # per cup
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},  # per cover
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},  # per envelope
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},  # per sheet
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},  # per pad
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},  # per card
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},  # per flyer
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},  # per roll
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},  # per roll
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},  # per bag
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},  # per tag
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},  # per folder

    # Large-format items (priced per unit)
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]


# Given below are some utility functions you can use to implement your multi-agent system

def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """
    Generate inventory for exactly a specified percentage of items from the full paper supply list.

    This function randomly selects exactly `coverage` × N items from the `paper_supplies` list,
    and assigns each selected item:
    - a random stock quantity between 200 and 800,
    - a minimum stock level between 50 and 150.

    The random seed ensures reproducibility of selection and stock levels.

    Args:
        paper_supplies (list): A list of dictionaries, each representing a paper item with
                               keys 'item_name', 'category', and 'unit_price'.
        coverage (float, optional): Fraction of items to include in the inventory (default is 0.4, or 40%).
        seed (int, optional): Random seed for reproducibility (default is 137).

    Returns:
        pd.DataFrame: A DataFrame with the selected items and assigned inventory values, including:
                      - item_name
                      - category
                      - unit_price
                      - current_stock
                      - min_stock_level
    """
    # Ensure reproducible random output
    np.random.seed(seed)

    # Calculate number of items to include based on coverage
    num_items = int(len(paper_supplies) * coverage)

    # Randomly select item indices without replacement
    selected_indices = np.random.choice(
        range(len(paper_supplies)),
        size=num_items,
        replace=False
    )

    # Extract selected items from paper_supplies list
    selected_items = [paper_supplies[i] for i in selected_indices]

    # Construct inventory records
    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),  # Realistic stock range
            "min_stock_level": np.random.randint(50, 150)  # Reasonable threshold for reordering
        })

    # Return inventory as a pandas DataFrame
    return pd.DataFrame(inventory)

def init_database(db_engine: Engine, seed: int = 137) -> Engine:    
    """
    Set up the Munder Difflin database with all required tables and initial records.

    This function performs the following tasks:
    - Creates the 'transactions' table for logging stock orders and sales
    - Loads customer inquiries from 'quote_requests.csv' into a 'quote_requests' table
    - Loads previous quotes from 'quotes.csv' into a 'quotes' table, extracting useful metadata
    - Generates a random subset of paper inventory using `generate_sample_inventory`
    - Inserts initial financial records including available cash and starting stock levels

    Args:
        db_engine (Engine): A SQLAlchemy engine connected to the SQLite database.
        seed (int, optional): A random seed used to control reproducibility of inventory stock levels.
                              Default is 137.

    Returns:
        Engine: The same SQLAlchemy engine, after initializing all necessary tables and records.

    Raises:
        Exception: If an error occurs during setup, the exception is printed and raised.
    """
    try:
        # ----------------------------
        # 1. Create an empty 'transactions' table schema
        # ----------------------------
        transactions_schema = pd.DataFrame({
            "id": [],
            "item_name": [],
            "transaction_type": [],  # 'stock_orders' or 'sales'
            "units": [],             # Quantity involved
            "price": [],             # Total price for the transaction
            "transaction_date": [],  # ISO-formatted date
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)

        # Set a consistent starting date
        initial_date = datetime(2025, 1, 1).isoformat()

        # ----------------------------
        # 2. Load and initialize 'quote_requests' table
        # ----------------------------
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 3. Load and transform 'quotes' table
        # ----------------------------
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        # Unpack metadata fields (job_type, order_size, event_type) if present
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))

        # Retain only relevant columns
        quotes_df = quotes_df[[
            "request_id",
            "total_amount",
            "quote_explanation",
            "order_date",
            "job_type",
            "order_size",
            "event_type"
        ]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 4. Generate inventory and seed stock
        # ----------------------------
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        # Seed initial transactions
        initial_transactions = []

        # Add a starting cash balance via a dummy sales transaction
        initial_transactions.append({
            "item_name": None,
            "transaction_type": "sales",
            "units": None,
            "price": 50000.0,
            "transaction_date": initial_date,
        })

        # Add one stock order transaction per inventory item
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"],
                "transaction_type": "stock_orders",
                "units": item["current_stock"],
                "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date,
            })

        # Commit transactions to database
        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)

        # Save the inventory reference table
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)

        return db_engine

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

paper_supplies_dict = {
    item["item_name"]: item
    for item in paper_supplies
}

def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: Union[str, datetime],
) -> int:
    """
    This function records a transaction of type 'stock_orders' or 'sales' with a specified
    item name, quantity, total price, and transaction date into the 'transactions' table of the database.

    Args:
        item_name (str): The name of the item involved in the transaction.
        transaction_type (str): Either 'stock_orders' or 'sales'.
        quantity (int): Number of units involved in the transaction.
        price (float): Total price of the transaction.
        date (str or datetime): Date of the transaction in ISO 8601 format.

    Returns:
        int: The ID of the newly inserted transaction.

    Raises:
        ValueError: If `transaction_type` is not 'stock_orders' or 'sales'.
        Exception: For other database or execution errors.
    """
    try:
        # Convert datetime to ISO string if necessary
        if quantity == 0:
            return
        date_str = date.isoformat() if isinstance(date, datetime) else date
        item = paper_supplies_dict.get(item_name)
        if item and transaction_type == "stock_orders":
            price = item["unit_price"] * quantity
        # Validate transaction type
        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")
        print(f"FUNC (create_transaction):item_name: {item_name}, transaction_type: {transaction_type},units: {quantity},price: {price}, transaction_date:'{date_str}'")
        # Prepare transaction record as a single-row DataFrame
        transaction = pd.DataFrame([{
            "item_name": item_name,
            "transaction_type": transaction_type,
            "units": quantity,
            "price": price,
            "transaction_date": date_str,
        }])

        # Insert the record into the database
        transaction.to_sql("transactions", db_engine, if_exists="append", index=False)

        # Fetch and return the ID of the inserted row
        result = pd.read_sql("SELECT last_insert_rowid() as id", db_engine)
        return int(result.iloc[0]["id"])

    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise

def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """
    Retrieve a snapshot of available inventory as of a specific date.

    This function calculates the net quantity of each item by summing 
    all stock orders and subtracting all sales up to and including the given date.

    Only items with positive stock are included in the result.

    Args:
        as_of_date (str): ISO-formatted date string (YYYY-MM-DD) representing the inventory cutoff.

    Returns:
        Dict[str, int]: A dictionary mapping item names to their current stock levels.
    """
    # SQL query to compute stock levels per item as of the given date
    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """

    # Execute the query with the date parameter
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})

    # Convert the result into a dictionary {item_name: stock}
    return dict(zip(result["item_name"], result["stock"]))

def get_stock_level_df(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Retrieve the stock level of a specific item as of a given date.

    This function calculates the net stock by summing all 'stock_orders' and 
    subtracting all 'sales' transactions for the specified item up to the given date.

    Args:
        item_name (str): The name of the item to look up.
        as_of_date (str or datetime): The cutoff date (inclusive) for calculating stock.

    Returns:
        pd.DataFrame: A single-row DataFrame with columns 'item_name' and 'current_stock'.
    """
    # Convert date to ISO string format if it's a datetime object
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # SQL query to compute net stock level for the item
    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name
        AND transaction_date <= :as_of_date
    """

    # Execute query and return result as a DataFrame
    return pd.read_sql(
            stock_query,
            db_engine,
            params={
                "item_name": item_name,
                "as_of_date": as_of_date
            },
        )
def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> Dict:
    """
    Retrieve the stock level of a specific item as of a given date.

    This function calculates the net stock by summing all 'stock_orders' and 
    subtracting all 'sales' transactions for the specified item up to the given date.

    Args:
        item_name (str): The name of the item to look up.
        as_of_date (str or datetime): The cutoff date (inclusive) for calculating stock.

    Returns:
        pd.DataFrame: A single-row DataFrame with columns 'item_name' and 'current_stock'.
    """
   
    df = get_stock_level_df(item_name, as_of_date)
    print(f"FUNC (get_stock_level): stock level details. Name: {df.item_name[0]}, current_stock: {df.current_stock[0]}")
    return df.to_dict(orient="records")

def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estimate the supplier delivery date based on the requested order quantity and a starting date.

    Delivery lead time increases with order size:
        - ≤10 units: same day
        - 11–100 units: 1 day
        - 101–1000 units: 4 days
        - >1000 units: 7 days

    Args:
        input_date_str (str): The starting date in ISO format (YYYY-MM-DD).
        quantity (int): The number of units in the order.

    Returns:
        str: Estimated delivery date in ISO format (YYYY-MM-DD).
    """
    # Debug log (comment out in production if needed)
    print(f"FUNC (get_supplier_delivery_date): Calculating for qty {quantity} from date string '{input_date_str}'")

    # Attempt to parse the input date
    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        # Fallback to current date on format error
        print(f"WARN (get_supplier_delivery_date): Invalid date format '{input_date_str}', using today as base.")
        input_date_dt = datetime.now()

    # Determine delivery delay based on quantity
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    # Add delivery days to the starting date
    delivery_date_dt = input_date_dt + timedelta(days=days)

    # Return formatted delivery date
    return delivery_date_dt.strftime("%Y-%m-%d")

def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """
    Calculate the current cash balance as of a specified date.

    The balance is computed by subtracting total stock purchase costs ('stock_orders')
    from total revenue ('sales') recorded in the transactions table up to the given date.

    Args:
        as_of_date (str or datetime): The cutoff date (inclusive) in ISO format or as a datetime object.

    Returns:
        float: Net cash balance as of the given date. Returns 0.0 if no transactions exist or an error occurs.
    """
    try:
        # Convert date to ISO format if it's a datetime object
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()

        # Query all transactions on or before the specified date
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine,
            params={"as_of_date": as_of_date},
        )

        # Compute the difference between sales and stock purchases
        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)

        return 0.0

    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0


def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """
    Generate a complete financial report for the company as of a specific date.

    This includes:
    - Cash balance
    - Inventory valuation
    - Combined asset total
    - Itemized inventory breakdown
    - Top 5 best-selling products

    Args:
        as_of_date (str or datetime): The date (inclusive) for which to generate the report.

    Returns:
        Dict: A dictionary containing the financial report fields:
            - 'as_of_date': The date of the report
            - 'cash_balance': Total cash available
            - 'inventory_value': Total value of inventory
            - 'total_assets': Combined cash and inventory value
            - 'inventory_summary': List of items with stock and valuation details
            - 'top_selling_products': List of top 5 products by revenue
    """
    # Normalize date input
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # Get current cash balance
    cash = get_cash_balance(as_of_date)

    # Get current inventory snapshot
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []

    # Compute total inventory value and summary by item
    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level_df(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append({
            "item_name": item["item_name"],
            "stock": stock,
            "unit_price": item["unit_price"],
            "value": item_value,
        })

    # Identify top-selling products by revenue
    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }


def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """
    Retrieve a list of historical quotes that match any of the provided search terms.

    The function searches both the original customer request (from `quote_requests`) and
    the explanation for the quote (from `quotes`) for each keyword. Results are sorted by
    most recent order date and limited by the `limit` parameter.

    Args:
        search_terms (List[str]): List of terms to match against customer requests and explanations.
        limit (int, optional): Maximum number of quote records to return. Default is 5.

    Returns:
        List[Dict]: A list of matching quotes, each represented as a dictionary with fields:
            - original_request
            - total_amount
            - quote_explanation
            - job_type
            - order_size
            - event_type
            - order_date
    """
    conditions = []
    params = {}

    # Build SQL WHERE clause using LIKE filters for each search term
    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    # Combine conditions; fallback to always-true if no terms provided
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Final SQL query to join quotes with quote_requests
    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    # Execute parameterized query
    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row._mapping) for row in result]

########################
########################
########################
# YOUR MULTI AGENT STARTS HERE
########################
########################
########################


# Set up and load your env parameters and instantiate your model.
load_dotenv()


"""Set up tools for your agents to use, these should be methods that combine the database functions above
 and apply criteria to them to ensure that the flow of the system is correct."""

tool_create_transaction = Tool(
    name="create_transaction",
    description="""
        This function records a transaction of type 'stock_orders' or 'sales' with a specified
        item name, quantity, total price, and transaction date into the 'transactions' table of the database.
    """,
    function=create_transaction,
    require_parameter_descriptions=True
)

tool_get_all_inventory = Tool(
    name="get_all_inventory",
    description="""
        Retrieve a snapshot of available inventory as of a specific date.
        This function calculates the net quantity of each item by summing
        all stock orders and subtracting all sales up to and including the given date.            
        Only items with positive stock are included in the result.
    """,
    function=get_all_inventory,
    require_parameter_descriptions=True

)

tool_get_stock_level = Tool(
    name="get_stock_level",
    description="""
        This function records a transaction of type 'stock_orders' or 'sales' with a specified
        item name, quantity, total price, and transaction date into the 'transactions' table of the database.
    """,
    function=get_stock_level,
    require_parameter_descriptions=True
)

tool_get_supplier_delivery_date = Tool(
    name="get_supplier_delivery_date",
    description="""
        Estimate the supplier delivery date based on the requested order quantity and a starting date.
    
        Delivery lead time increases with order size:
            - ≤10 units: same day
            - 11–100 units: 1 day
            - 101–1000 units: 4 days
            - >1000 units: 7 days    
    """,
    function=get_supplier_delivery_date,
    require_parameter_descriptions=True
)

tool_get_cash_balance = Tool(
    name="get_cash_balance",
    description="""
        Calculate the current cash balance as of a specified date.
        The balance is computed by subtracting total stock purchase costs ('stock_orders')
        from total revenue ('sales') recorded in the transactions table up to the given date.
    """,
    function=get_cash_balance,
    require_parameter_descriptions=True
)

tool_generate_financial_report = Tool(
    name="generate_financial_report",
    description="""
        Generate a complete financial report for the company as of a specific date.
        This includes:
        - Cash balance
        - Inventory valuation
        - Combined asset total
        - Itemized inventory breakdown
        - Top 5 best-selling products
    """,
    function=generate_financial_report,
    require_parameter_descriptions=True
)

tool_search_quote_history = Tool(
    name="search_quote_history",
    description="""
        Retrieve a list of historical quotes that match any of the provided search terms.
        The function searches both the original customer request (from `quote_requests`) and
        the explanation for the quote (from `quotes`) for each keyword. Results are sorted by
        most recent order date and limited by the `limit` parameter.
    """,
    function=search_quote_history,
    require_parameter_descriptions=True
)

# Tools for inventory agent
toolset_inventory_agent = [tool_get_all_inventory, tool_get_stock_level, tool_get_supplier_delivery_date,
                          tool_create_transaction]

# Tools for quoting agent
toolset_quoting_agent = [tool_search_quote_history, tool_generate_financial_report]

# Tools for ordering agent
toolset_sales_finalization_agent = [tool_create_transaction, tool_get_supplier_delivery_date]


# =========================================================
# PYDANTIC RESPONSE MODELS
# =========================================================

# Set up your agents and create an orchestration agent that will manage them.
# Define output message from orchestration agent
class OrchestrationClassification(BaseModel):
    classification: Literal["INQUIRY", "ORDER"]

class InvoiceResponse(BaseModel):
    customer_message: str
    invoice_text: str

# define orchestration agent
orchestration_agent = Agent(
    model="openai-chat:gpt-4o",
    name="Orchestration Agent",
    model_settings=ModelSettings(temperature=0.0),
    system_prompt="""
    You are the Orchestration Agent for the Munder Difflin paper supply company.

    Your responsibility is to analyze incoming customer requests and classify them into one of the following categories:

    - INQUIRY: The customer is requesting information only.
    - ORDER: The customer intends to purchase or place an order.

    ---

    ## Classification Guidelines

    Classify the request as INQUIRY when the customer:

    - Asks about inventory availability or stock levels
    - Requests delivery timelines or estimated delivery dates
    - Seeks pricing information, quotations, or comparisons
    - Requests general product, supplier, or financial information
    - Does not clearly express intent to purchase

    Classify the request as ORDER when the customer:

    - Explicitly states they want to buy, purchase, or order a product
    - Confirms or finalizes a purchase
    - Requests order placement, even if quantities are not specified
    - Indicates intent to proceed with procurement

    ---

    ## Additional Rules

    1. Questions about availability or delivery dates are always INQUIRY unless the customer explicitly asks to place the order.
    2. Price-related questions are INQUIRY unless purchase intent is clearly stated.
    3. If the request contains both informational and purchasing intent, classify it as ORDER.
    4. If the intent is ambiguous, default to INQUIRY.

    ---

    ## Output Format

    Return a JSON object that follows this schema:

    ```python
    class OrchestrationClassification(BaseModel):
        classification: Literal["INQUIRY", "ORDER"]
    ```
    """,
    output_type=OrchestrationClassification
    )

# Define inventory agent
## Manages the current stock level. Retrieves stock data, checks stock limits and triggers automatic reorders if required (e.g. via create_transaction for reorders).
class InventoryItemStatus(BaseModel):
    item_name: str
    requested_quantity: int
    available_quantity: int
    shortage_quantity: int
    fulfillable: bool
   
class InventoryResponse(BaseModel):
    answer: str
    proceed_with_order: bool
    inventory_status: list[InventoryItemStatus]
    supplier_delivery_date: str | None = None
    
inventory_agent = Agent(
    model="openai-chat:gpt-3.5-turbo",
    name="Inventory Agent",
    model_settings=ModelSettings(temperature=0.1),
    system_prompt="""
You are the Inventory Agent for the Munder Difflin paper supply company.

---
CORE MISSION
---
You manage inventory validation and restocking decisions for incoming requests.

You ONLY:
- check inventory
- validate fulfillment
- trigger restocking when required

You NEVER:
- generate quotes
- create invoices
- finalize pricing
- create sales transactions (except stock_orders via create_transaction tool)

STRICT INVENTORY NAME MATCHING RULE (HARD CONSTRAINT)

- Item names MUST match inventory exactly as returned by get_all_inventory or get_stock_level
- DO NOT perform fuzzy matching, partial matching, or semantic matching
- DO NOT assume product variants (e.g., A4, A3, premium, glossy, etc.)
- DO NOT map user-provided names to inventory items

MATCHING RULE:
IF user_item_name != exact_inventory_item_name:
    → item DOES NOT EXIST in inventory

In this case:
- set fulfillable = false
- available_quantity = 0
- shortage_quantity = requested_quantity
- DO NOT call create_transaction
- DO NOT attempt restocking

---
HARD EXECUTION PROTOCOL (MANDATORY)
---

Every ORDER request MUST follow this exact sequence:

PHASE 1 — DATA COLLECTION
- Call `get_all_inventory`

PHASE 2 — ITEM VALIDATION
For each requested item:
- Verify if item exists

If item does NOT exist:
    - set fulfillable = false
    - available_quantity = 0
    - shortage_quantity = requested_quantity
    - DO NOT call any transaction tool

If item EXISTS:
    - call `get_stock_level`
    - available_quantity = current_stock

PHASE 3 — FULFILLMENT DECISION

If available_quantity >= requested_quantity:
    - fulfillable = true
    - shortage_quantity = 0
    - NO transaction required

If available_quantity < requested_quantity:
    - calculate shortage_quantity
       available_quantity = requested_quantity - available_quantity
    - fulfillable = false

    MANDATORY ACTION:
    IF shortage_quantity > 0:
        - YOU MUST call `create_transaction`
        - transaction_type MUST be "stock_orders"
        - quantity MUST equal shortage_quantity
        - THEN call `get_supplier_delivery_date`

---
ABSOLUTE RULES (NON-NEGOTIABLE)
---

1. If shortage_quantity > 0 AND item exists:
   → create_transaction MUST be called
   → failure to call tool = invalid response

2. Never describe restocking without executing it

3. Never skip tool calls for ORDER requests

4. Never hallucinate inventory, pricing, or supplier info

---
INQUIRY REQUESTS
---

- Only read inventory
- MAY call `get_supplier_delivery_date` if asked about timing
- NEVER create transactions

---
TOOL USAGE RULES
---

Available tools:
- get_all_inventory
- get_stock_level
- get_supplier_delivery_date
- create_transaction

Tool usage rules:
- Tools must be executed immediately when required
- Do NOT explain before calling tools
- Do NOT summarize before tool execution

---
CUSTOMER-FACING RESPONSE STYLE (MANDATORY)
---

The `answer` field MUST:
- sound like a short operational fulfillment update
- summarize ONLY fulfillable items and backordered items
- avoid narrating internal system actions
- avoid phrases like:
  - "The order can be fulfilled"
  - "An order has been placed"
  - "Inventory validation completed"
  - "The following items are available"

Preferred style:
- "We can ship [available items]; [shortage items] is on backorder until [date]."

Examples:

GOOD:
- "We can ship colorful poster paper and streamers; balloons are on backorder until April 7, 2025."
- "Printer paper is available for immediate shipment."
- "Markers are partially available; remaining stock arrives on May 2, 2025."

BAD:
- "The order for X and Y can be fulfilled."
- "A stock order has been created."
- "Inventory validation succeeded."
- "There are no balloons in stock."

---
RESPONSE FORMAT RULES
---

Return ONLY valid JSON:

- answer: concise explanation of decision
- inventory_status: list of item statuses
- proceed_with_order: true only if fully fulfillable
- supplier_delivery_date: earliest relevant date if restocking occurs else null

---
BEHAVIOR CONSTRAINT
---

If restocking is required:
→ tool call is mandatory before final response
→ no exceptions
    """,
    tools=toolset_inventory_agent,
    output_type=InventoryResponse
    )

# Define quoting agent
## Analyzes past offers and prices in order to create a suitable offer for a customer request based on strategic specifications.
## Takes into account, for example, volume discounts or key financial figures.
class QuoteLineItem(BaseModel):
    item_name: str
    quantity: int
    unit_price: float
    discount_label: str | None = None
    discount_amount: float = 0.0
    original_price: float = 0.0
    final_unit_price: float
    line_total: float


class QuoteResponse(BaseModel):
    answer: str
    items: list[QuoteLineItem]
    subtotal: float
    total_discount: float
    grand_total: float
    remarks: str


quoting_agent = Agent(
    model="openai-chat:gpt-4o",
    name="Quoting Agent",
    model_settings=ModelSettings(temperature=0.2),
    system_prompt="""
    You are the Quoting Agent for the Munder Difflin paper supply company.

    Your role is to generate accurate, profitable, and customer-friendly quotes.

    You receive structured context containing:
    - customer orders
    - inventory feasibility
    - supplier timing
    - historical pricing

    You do NOT:
    - check inventory directly
    - create transactions
    - finalize orders
    - generate invoices

    Available tools:
    - `search_quote_history`
    - `generate_financial_report`

    Use tools only when necessary.

    Pricing & Discount Rules (mapped to QuoteLineItem fields):

    Each QuoteLineItem MUST contain:

    - item_name: product name
    - quantity: ordered quantity
    - unit_price: base price per unit before discount
    - discount_amount: per-unit discount applied (0 if none)
    - discount_label: reason for discount (nullable)
    - original_price = quantity × unit_price
    - final_unit_price = unit_price - discount_amount
    - line_total = quantity × final_unit_price

    Aggregation rules for QuoteResponse:

    - items: list of QuoteLineItem
    - subtotal = sum(original_price of all items)
    - total_discount = sum(quantity × discount_amount)
    - grand_total = subtotal - total_discount

    Discount Strategy:
    1. Apply bulk discounts strategically to encourage larger purchases (above 50 qty for an item).
    2. Use historical pricing and profitability considerations when determining discounts.
    3. Prefer modest, commercially realistic discounts.
    4. Never apply excessive or unprofitable discounts unless explicitly instructed.
    5. Every discounted item must include a valid discount label or reason.

    Operational Rules:
    1. Never alter inventory assumptions or supplier timelines.
    2. Base pricing only on provided context or tool results.
    3. Never leave monetary fields null or undefined.
    4. Generate concise professional customer remarks.
    5. Include customer-facing notes summarizing:
       - total discount received
       - savings achieved
       - bulk purchase benefits when applicable

    The generated pricing becomes the authoritative downstream pricing source.

    Return ONLY valid JSON matching the `QuoteResponse` schema.

    Do NOT return markdown.
    Do NOT include explanations outside JSON.
    """,
    tools=toolset_quoting_agent,
    output_type=QuoteResponse
)

# Define ordering agent
## Takes over the last step: checks whether the ordered items are available and whether the delivery times are suitable,
## and then creates a sales transaction. This completes the order with binding effect.
class FinalizedSaleItem(BaseModel):
    item_name: str
    quantity: int
    unit_price: float
    line_total: float


class SalesFinalizationResponse(BaseModel):
    order_confirmed: bool
    estimated_delivery_date: str
    transaction_ids: list[str]
    finalized_items: list[FinalizedSaleItem]
    subtotal: float
    discount_amount: float
    grand_total: float
    answer: str


sales_finalization_agent = Agent(
    model="openai-chat:gpt-3.5-turbo",
    name="Sales Finalization Agent",
    model_settings=ModelSettings(temperature=0.1),
    system_prompt="""
    You are the Sales Finalization Agent for Munder Difflin paper supply company.

	--------------------------------------------------
	CRITICAL PRINCIPLE
	--------------------------------------------------
	You are NOT allowed to skip any step involving transactions.

	If a transaction is required, it MUST be executed before final response.
    --------------------------------------------------
    INPUT
    --------------------------------------------------
    You receive QuoteResponse:

    - items: QuoteLineItem[]
    - subtotal (original)
    - total_discount (invoice-level only)
    - grand_total (final invoice total)

    --------------------------------------------------
    PRICING RULE (IMPORTANT)
    --------------------------------------------------

    You MUST use ORIGINAL pricing only:

    For each item:
    - unit_price = quote.unit_price  (DO NOT use final_unit_price)
    - line_total = quote.original_price ( DO NOT use quote.line_total)

    DO NOT apply or infer discounts at item level.

    --------------------------------------------------
    INVOICE DISCOUNT MODEL
    --------------------------------------------------

    - discount_amount = quote.total_discount
    - discount applies ONLY at invoice level
    - NEVER distribute discount across items

    --------------------------------------------------
    TRANSACTIONS
    --------------------------------------------------
    MANDATORY ACTION 
    For each item in QuoteLineItem:
    - you must create_transaction with
      - transaction_type = "sales"
      - item_name = item.item_name
      - quantity = item.quantity
      - price = item.line_total(NOT item.original_price)

    --------------------------------------------------
    OUTPUT RULES
    --------------------------------------------------

    Return ONLY JSON:

    - order_confirmed
    - estimated_delivery_date
    - transaction_ids
    - finalized_items:
        - item_name
        - quantity
        - unit_price (original)
        - line_total (original)
    - subtotal (original sum)
    - discount_amount (invoice level only)
    - grand_total(subtotal - discount_amount)
    - answer

    --------------------------------------------------
    CONSTRAINTS
    --------------------------------------------------

    - NEVER use final_unit_price
    - NEVER split discount into items
    - NEVER recompute pricing differently from quote
    - Quote data is authoritative
    """,
        tools=toolset_sales_finalization_agent,
        output_type=SalesFinalizationResponse
    )

# Define invoice agent
## This agent generate a complete and professional **customer invoice** based on the finalized order
invoice_agent = Agent(
    model="openai-chat:gpt-4o",
    name="Invoice Agent",
    model_settings=ModelSettings(temperature=0.1),
    system_prompt="""
    You are the Invoice Agent for the Munder Difflin paper supply company.

    Your responsibility is to generate a professional customer invoice based on finalized order information.
    
    You receive finalized structured JSON data containing:
    - customer information
    - finalized line items
    - finalized quantities
    - finalized unit prices
    - finalized line totals
    - finalized subtotal
    - finalized discounts (if applicable)
    - finalized grand total
    - delivery information

    All financial values are authoritative and were finalized upstream.
    You are a presentation and formatting layer only.

    You do NOT:
    - calculate pricing
    - modify totals
    - recompute discounts
    - infer quantities
    - reinterpret quote data
    - create transactions
    - validate inventory
    - finalize sales
    ---

    ## Responsibilities

    Your response must contain TWO sections:

    ### 1. Customer-Friendly Summary

    Provide a short and professional message that:
    - Thanks the customer for the order
    - Confirms the purchased item(s)
    - Mentions the expected delivery date
    - Informs the customer that the invoice is included below

    Keep this section concise and customer-friendly.

    ---

    ### 2. Formatted Invoice (Plain Text)

    Generate a clean ASCII-formatted invoice using a monospaced text layout.

    The invoice must always include:

    - Invoice number
    - Generate a realistic placeholder format:
        `INV-2026-XXX`

    - Invoice issue date
    - Use the current date

    - Billing information
    - Customer name
    - Customer address
    - Customer email
    - Use `<placeholder>` if any information is missing

    - Itemized order details
    - Item description
    - Quantity
    - Unit price
    - Line total

    - Pricing summary
    - Subtotal
    - Discount amount (if applicable)
    - Grand total

    - Delivery information
    - Expected delivery date

    - Closing thank-you note

    ---
    
    ## Financial Consistency Rules

    - Never recalculate subtotal, discount, or grand total
    - Never derive totals from displayed line items
    - Render all provided numeric values exactly as received
    - Never adjust quantities or unit prices
    - Never modify line totals
    - Preserve financial consistency from upstream systems
    - Never reconcile or validate arithmetic consistency

    
    ---
    
    ## Invoice Formatting Rules

    - Use plain-text ASCII formatting only
    - Use spaces for alignment (never tabs)
    - Keep the invoice width readable (~80 characters maximum)
    - Separate sections using dashed lines
    - Align numeric values consistently
    - Ensure totals are easy to read

    ---

    ## Discount Handling

    If discounts are provided:
    - Explicitly show:
    - Discount percentage or label
    - Discount amount deducted
    - Display the final grand total after discount

    If no discount exists:
    - Omit the discount section cleanly

    ---

    ## Example Structure

    Invoice No: INV-2026-034
    Date: 2026-05-24

    Bill To:
    Name: John Doe
    Address: <placeholder>
    Email: john@example.com

    ----------------------------------------------------------------

    Qty   Description                Unit Price      Line Total

    500   A4 Paper (80g/m²)          €0.10           €50.00

    ----------------------------------------------------------------

    Subtotal:                                        €50.00
    Discount (10%):                                  -€5.00
    Grand Total:                                     €45.00

    Expected Delivery Date: 2026-05-28

    Thank you for your business!

    ---

    ## Constraints

    - Always generate a complete invoice
    - Never omit pricing details
    - Always use placeholders for missing customer information
    - Maintain a professional and business-friendly tone
    - Do not invent unavailable customer data beyond placeholders

    ---

    ## Output Format

    Return a JSON object using the following Pydantic schema:

    ```python
    class InvoiceResponse(BaseModel):
        customer_message: str
        invoice_text: str
    ```
    Return ONLY valid JSON matching the schema.
    Do not wrap the response in markdown code fences.
    Do not include explanations outside the JSON response.
    """,
    output_type=InvoiceResponse
    )

class WorkflowContext(BaseModel):
    """Shared context passed between workflow agents."""
    request_id: str
    original_request: str

class WorkflowResponse(BaseModel):
    status: Literal[
        "INQUIRY",
        "ORDER_COMPLETED",
        "ORDER_FAILED",
        "INVALID_CLASSIFICATION"
    ]
    message: str
    invoice_text: str | None = None

class MultiAgentWorkflow:
    """
    End-to-end multi-agent workflow for handling customer inquiries
    and order processing for the Munder Difflin paper supply company.
    """

    def __init__(self):
        self.agents = {
            "orchestration": orchestration_agent,
            "inventory": inventory_agent,
            "quoting": quoting_agent,
            "sales": sales_finalization_agent,
            "invoice": invoice_agent
        }

        self.agent_usage_count = {
            "inventory": 0,
            "quoting": 0,
            "sales": 0,
            "invoice": 0,
        }

    def handle_inquiry(self, context: WorkflowContext):
        """
        Handle informational customer requests.

        Workflow:
        1. Inventory Agent validates stock and delivery feasibility.
        2. Return the informational response directly to the customer.
        """

        inventory_input = {
            "classification": "INQUIRY",
            "user_request": context.original_request
        }

        inventory_response = self.agents["inventory"].run_sync(
            json.dumps(inventory_input, indent=2),
            deps=context
        )
        
        self.agent_usage_count["inventory"] += 1
        print(
            f"--- Inventory Agent INQUIRY Answer: "
            f"{inventory_response.output.answer}"
        )
        #return inventory_response.output
        return WorkflowResponse(
            status="INQUIRY",
            message=inventory_response.output.answer
        )

    def handle_order(self, context: WorkflowContext) -> WorkflowResponse:
        """
        Handle customer purchase orders.

        Workflow:
        1. Inventory Agent validates stock and fulfillment feasibility.
        2. Quote Agent generates pricing.
        3. Sales Agent finalizes the transaction.
        4. Invoice Agent generates the customer invoice.
        """

        # ---------------------------------------------------------
        # Step 1: Inventory Validation
        # ---------------------------------------------------------

        inventory_input = {
            "classification": "ORDER",
            "user_request": context.original_request
        }

        inventory_response = self.agents["inventory"].run_sync(
            json.dumps(inventory_input, indent=2),
            deps=context
        )

        self.agent_usage_count["inventory"] += 1
        
        # Stop workflow if fulfillment is not possible
        if not inventory_response.output.proceed_with_order:
            print(
                f"Order cannot be processed: "
                f"{inventory_response.output.answer}"
            )
            #return inventory_response.output.answer
            return WorkflowResponse(
                status="ORDER_FAILED",
                message=inventory_response.output.answer
            )
        print(
            f"--- Inventory Agent ORDER Answer: "
            f"{inventory_response.output.answer}"
        )
        # ---------------------------------------------------------
        # Step 2: Quote Generation
        # ---------------------------------------------------------       
        quote_input = {
            "user_request": context.original_request,
            "inventory_context": inventory_response.output.model_dump()
        }

        quoting_response = self.agents["quoting"].run_sync(
            json.dumps(quote_input, indent=2),
            deps=context
        )

        self.agent_usage_count["quoting"] += 1

        # ---------------------------------------------------------
        # Step 3: Sales Finalization
        # ---------------------------------------------------------

        sales_input = {
            "user_request": context.original_request,
            "inventory_context": inventory_response.output.model_dump(),
            "quote_context": quoting_response.output.model_dump()
        }

        sales_response = self.agents["sales"].run_sync(
            json.dumps(sales_input, indent=2),
            deps=context
        )
        self.agent_usage_count["sales"] += 1
        
        if not sales_response.output.order_confirmed:
            return WorkflowResponse(
                status="ORDER_FAILED",
                message=sales_response.output.answer
            )
        # ---------------------------------------------------------
        # Step 4: Invoice Generation
        # ---------------------------------------------------------

        invoice_input = {
            "user_request": context.original_request,
            "inventory_context": inventory_response.output.model_dump(),
            "quote_context": quoting_response.output.model_dump(),
            "sales_context": sales_response.output.model_dump()
        }

        invoice_response = self.agents["invoice"].run_sync(
            json.dumps(invoice_input, indent=2),
            deps=context
        )
        self.agent_usage_count["invoice"] += 1

        #return invoice_response.output
        return WorkflowResponse(
            status="ORDER_COMPLETED",
            message=invoice_response.output.customer_message,
            invoice_text=invoice_response.output.invoice_text
        )

    def run(self, customer_request: str) -> WorkflowResponse:
        """
        Execute the multi-agent workflow for a customer request.

        Steps:
        1. Orchestration Agent classifies the request.
        2. Route request to inquiry or order workflow.
        3. Return the final response.
        """

        # Create shared workflow context
        context = WorkflowContext(
            request_id=f"REQ_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            original_request=customer_request
        )

        # ---------------------------------------------------------
        # Step 1: Request Classification
        # ---------------------------------------------------------

        orchestration_response = self.agents["orchestration"].run_sync(
            customer_request,
            deps=context
        )

        classification = orchestration_response.output.classification

        print(
            f"--- Orchestration Agent classified request as: "
            f"{classification}"
        )

        # ---------------------------------------------------------
        # Step 2: Workflow Routing
        # ---------------------------------------------------------

        if classification == "INQUIRY":
            response = self.handle_inquiry(context)

        elif classification == "ORDER":
            response = self.handle_order(context)

        else:
            response = WorkflowResponse(
                status="INVALID_CLASSIFICATION",
                message=(
                    "Invalid classification received from "
                    "the orchestration agent."
                )
            )

        return response
# Run your test scenarios by writing them here. Make sure to keep track of them.

def run_test_scenarios():
    
    print("Initializing Database...")
    init_database(db_engine)
    try:
        quote_requests_sample = pd.read_csv("quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return

    # Get initial state
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = report["cash_balance"]
    current_inventory = report["inventory_value"]

    ############
    ############
    ############
    # INITIALIZE YOUR MULTI AGENT SYSTEM HERE
    ############
    ############
    ############
    multi_agent_workflow = MultiAgentWorkflow()

    results = []
    for idx, row in quote_requests_sample.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")

        print(f"\n=== Request {idx+1} ===")
        print(f"Context: {row['job']} organizing {row['event']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")

        # Process request
        request_with_date = f"{row['request']} (Date of request: {request_date})"

        ############
        ############
        ############
        # USE YOUR MULTI AGENT SYSTEM TO HANDLE THE REQUEST
        ############
        ############
        ############

        response = multi_agent_workflow.run(request_with_date)

        # Update state
        report = generate_financial_report(request_date)
        current_cash = report["cash_balance"]
        current_inventory = report["inventory_value"]
        print(f"Response: {response.message}")
        csvResponse=response.message
        if response.status == "ORDER_COMPLETED":
            csvResponse = csvResponse + "\n" + response.invoice_text
            print(f"Invoice:\n{response.invoice_text}\n")

        print(f"Updated Cash: ${current_cash:.2f}")
        print(f"Updated Inventory: ${current_inventory:.2f}")

        results.append(
            {
                "request_id": idx + 1,
                "request_date": request_date,
                "cash_balance": current_cash,
                "inventory_value": current_inventory,
                "response": csvResponse,
            }
        )

        time.sleep(1)

    # Final report
    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")

    # Save results
    pd.DataFrame(results).to_csv("test_results.csv", index=False)
    return results


if __name__ == "__main__":
    results = run_test_scenarios()
