"""
generate_data.py
-----------------
Generates a realistic synthetic e-commerce customer transaction dataset
for the Customer Behaviour Analysis project.

Run:
    python src/generate_data.py

Output:
    data/ecommerce_transactions.csv
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

N_CUSTOMERS = 1000
N_TRANSACTIONS = 8000

CATEGORIES = [
    "Electronics", "Fashion", "Home & Kitchen", "Beauty & Personal Care",
    "Sports & Outdoors", "Books", "Toys & Games", "Grocery"
]

PAYMENT_METHODS = ["Credit Card", "Debit Card", "UPI", "Net Banking", "Cash on Delivery", "Wallet"]

CITIES = [
    "Hyderabad", "Mumbai", "Delhi", "Bangalore", "Chennai",
    "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Lucknow"
]

GENDERS = ["Male", "Female", "Other"]

DEVICE_TYPES = ["Mobile", "Desktop", "Tablet"]

START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2025, 12, 31)


def random_dates(start, end, n):
    delta = (end - start).days
    offsets = np.random.randint(0, delta, size=n)
    return [start + timedelta(days=int(o), hours=int(np.random.randint(0, 24))) for o in offsets]


def generate_customers(n):
    customer_ids = [f"CUST{str(i).zfill(5)}" for i in range(1, n + 1)]
    ages = np.random.randint(18, 65, size=n)
    genders = np.random.choice(GENDERS, size=n, p=[0.48, 0.48, 0.04])
    cities = np.random.choice(CITIES, size=n)
    signup_dates = random_dates(START_DATE, END_DATE, n)

    df = pd.DataFrame({
        "customer_id": customer_ids,
        "age": ages,
        "gender": genders,
        "city": cities,
        "signup_date": signup_dates
    })
    return df


def generate_transactions(customers_df, n):
    customer_ids = customers_df["customer_id"].values

    # Give some customers much higher purchase frequency (realistic skew - power users)
    weights = np.random.exponential(scale=1.0, size=len(customer_ids))
    weights = weights / weights.sum()

    txn_customer_ids = np.random.choice(customer_ids, size=n, p=weights)
    txn_ids = [f"TXN{str(i).zfill(6)}" for i in range(1, n + 1)]
    categories = np.random.choice(
        CATEGORIES, size=n,
        p=[0.20, 0.18, 0.14, 0.12, 0.10, 0.08, 0.09, 0.09]
    )

    # Price depends loosely on category
    base_price_map = {
        "Electronics": 8000, "Fashion": 1200, "Home & Kitchen": 2000,
        "Beauty & Personal Care": 700, "Sports & Outdoors": 1800,
        "Books": 400, "Toys & Games": 900, "Grocery": 500
    }
    prices = []
    for c in categories:
        base = base_price_map[c]
        price = max(50, np.random.normal(loc=base, scale=base * 0.4))
        prices.append(round(price, 2))

    quantities = np.random.choice([1, 2, 3, 4, 5], size=n, p=[0.55, 0.2, 0.13, 0.08, 0.04])
    discounts = np.random.choice([0, 5, 10, 15, 20, 30], size=n, p=[0.35, 0.2, 0.2, 0.13, 0.08, 0.04])
    payment_methods = np.random.choice(PAYMENT_METHODS, size=n, p=[0.28, 0.2, 0.25, 0.1, 0.12, 0.05])
    device_types = np.random.choice(DEVICE_TYPES, size=n, p=[0.62, 0.30, 0.08])

    txn_dates = random_dates(START_DATE, END_DATE, n)

    # Ratings: most orders 3-5 stars, some unrated (NaN) to simulate real messy data
    ratings = np.random.choice([np.nan, 1, 2, 3, 4, 5], size=n, p=[0.15, 0.03, 0.05, 0.17, 0.30, 0.30])

    # Returned flag - correlated with low rating
    returned = []
    for r in ratings:
        if pd.isna(r):
            returned.append(np.random.choice([0, 1], p=[0.92, 0.08]))
        elif r <= 2:
            returned.append(np.random.choice([0, 1], p=[0.55, 0.45]))
        else:
            returned.append(np.random.choice([0, 1], p=[0.95, 0.05]))

    df = pd.DataFrame({
        "transaction_id": txn_ids,
        "customer_id": txn_customer_ids,
        "transaction_date": txn_dates,
        "category": categories,
        "unit_price": prices,
        "quantity": quantities,
        "discount_percent": discounts,
        "payment_method": payment_methods,
        "device_type": device_types,
        "rating": ratings,
        "returned": returned
    })

    df["gross_amount"] = (df["unit_price"] * df["quantity"]).round(2)
    df["final_amount"] = (df["gross_amount"] * (1 - df["discount_percent"] / 100)).round(2)

    return df


def inject_missing_and_dupes(df):
    """Introduce a small amount of realistic messiness for cleaning practice."""
    df = df.copy()
    # A few missing device types
    idx = np.random.choice(df.index, size=int(0.01 * len(df)), replace=False)
    df.loc[idx, "device_type"] = np.nan

    # A handful of duplicate rows
    dupe_rows = df.sample(n=15, random_state=1)
    df = pd.concat([df, dupe_rows], ignore_index=True)

    return df


if __name__ == "__main__":
    customers = generate_customers(N_CUSTOMERS)
    transactions = generate_transactions(customers, N_TRANSACTIONS)
    transactions = inject_missing_and_dupes(transactions)

    merged = transactions.merge(customers, on="customer_id", how="left")
    merged = merged.sort_values("transaction_date").reset_index(drop=True)

    customers.to_csv("data/customers.csv", index=False)
    merged.to_csv("data/ecommerce_transactions.csv", index=False)

    print(f"Generated {len(customers)} customers and {len(merged)} transactions.")
    print("Files saved to data/customers.csv and data/ecommerce_transactions.csv")
