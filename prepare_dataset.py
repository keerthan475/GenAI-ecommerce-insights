import pandas as pd

# === Load all 9 datasets ===
orders = pd.read_csv("data/olist_orders_dataset.csv")
order_items = pd.read_csv("data/olist_order_items_dataset.csv")
products = pd.read_csv("data/olist_products_dataset.csv")
customers = pd.read_csv("data/olist_customers_dataset.csv")
payments = pd.read_csv("data/olist_order_payments_dataset.csv")
reviews = pd.read_csv("data/olist_order_reviews_dataset.csv")
sellers = pd.read_csv("data/olist_sellers_dataset.csv")
geo = pd.read_csv("data/olist_geolocation_dataset.csv")
category_translation = pd.read_csv("data/product_category_name_translation.csv")

# === Translate product category names ===
products = products.merge(category_translation, on="product_category_name", how="left")
products.rename(columns={"product_category_name_english": "category_name_en"}, inplace=True)

# === Merge all main datasets ===
df = (
    orders
    .merge(order_items, on="order_id", how="left")
    .merge(products, on="product_id", how="left")
    .merge(customers, on="customer_id", how="left")
    .merge(payments, on="order_id", how="left")
    .merge(reviews, on="order_id", how="left")
    .merge(sellers, on="seller_id", how="left")
)

# === Enrich with geolocation ===
geo_unique = geo.drop_duplicates(subset=["geolocation_zip_code_prefix"]).rename(
    columns={
        "geolocation_zip_code_prefix": "customer_zip_code_prefix",
        "geolocation_lat": "customer_lat",
        "geolocation_lng": "customer_lng",
        "geolocation_city": "customer_geo_city",
        "geolocation_state": "customer_geo_state"
    }
)
df = df.merge(geo_unique, on="customer_zip_code_prefix", how="left")

# === Convert date columns ===
date_cols = [col for col in df.columns if "date" in col or "timestamp" in col]
for col in date_cols:
    df[col] = pd.to_datetime(df[col], errors="coerce")

# === Clean duplicates ===
df.drop_duplicates(subset=["order_id", "product_id"], inplace=True)

# === Save merged dataset ===
df.to_csv("data/olist_merged_full.csv", index=False)
print(f"✅ Final dataset ready! Rows: {len(df)} | Columns: {len(df.columns)}")
print("Saved at: data/olist_merged_full.csv")
