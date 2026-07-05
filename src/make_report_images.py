"""Generates all chart images used in the README / reports, matching the notebook's analysis."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

sns.set_theme(style="whitegrid", palette="viridis")
plt.rcParams["figure.figsize"] = (10, 6)

df = pd.read_csv("data/ecommerce_transactions.csv", parse_dates=["transaction_date", "signup_date"])
df = df.drop_duplicates().reset_index(drop=True)
df["device_type"] = df["device_type"].fillna(df["device_type"].mode()[0])
df["is_rated"] = df["rating"].notna().astype(int)
df["order_month"] = df["transaction_date"].dt.to_period("M").astype(str)
df["order_weekday"] = df["transaction_date"].dt.day_name()

# 1. Monthly revenue trend
monthly_revenue = df.groupby("order_month")["final_amount"].sum().sort_index()
plt.figure(figsize=(12, 5))
monthly_revenue.plot(kind="line", marker="o", color="#4C72B0")
plt.title("Monthly Revenue Trend", fontsize=14, fontweight="bold")
plt.xlabel("Month"); plt.ylabel("Revenue (₹)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("images/monthly_revenue_trend.png", dpi=150)
plt.close()

# 2. Category performance
category_stats = df.groupby("category").agg(
    orders=("transaction_id", "nunique"),
    revenue=("final_amount", "sum"),
).sort_values("revenue", ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(15, 6))
category_stats["revenue"].sort_values().plot(kind="barh", ax=axes[0], color="#55A868")
axes[0].set_title("Revenue by Category"); axes[0].set_xlabel("Revenue (₹)")
category_stats["orders"].sort_values().plot(kind="barh", ax=axes[1], color="#C44E52")
axes[1].set_title("Order Count by Category"); axes[1].set_xlabel("Number of Orders")
plt.tight_layout()
plt.savefig("images/category_performance.png", dpi=150)
plt.close()

# 3. Payment / device share
fig, axes = plt.subplots(1, 2, figsize=(15, 6))
df["payment_method"].value_counts().plot(kind="pie", autopct="%1.1f%%", ax=axes[0], cmap="viridis")
axes[0].set_title("Payment Method Share"); axes[0].set_ylabel("")
df["device_type"].value_counts().plot(kind="pie", autopct="%1.1f%%", ax=axes[1], cmap="magma")
axes[1].set_title("Device Type Share"); axes[1].set_ylabel("")
plt.tight_layout()
plt.savefig("images/payment_device_share.png", dpi=150)
plt.close()

# 4. Weekday revenue
weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekday_sales = df.groupby("order_weekday")["final_amount"].sum().reindex(weekday_order)
plt.figure(figsize=(10, 5))
sns.barplot(x=weekday_sales.index, y=weekday_sales.values, color="#8172B2")
plt.title("Revenue by Day of Week"); plt.ylabel("Revenue (₹)"); plt.xlabel("")
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig("images/revenue_by_weekday.png", dpi=150)
plt.close()

# 5. Returns vs rating
plt.figure(figsize=(8, 5))
sns.countplot(data=df.dropna(subset=["rating"]), x="rating", hue="returned", palette="Set2")
plt.title("Return Behaviour vs Rating"); plt.xlabel("Rating"); plt.ylabel("Order Count")
plt.legend(title="Returned", labels=["No", "Yes"])
plt.tight_layout()
plt.savefig("images/returns_vs_rating.png", dpi=150)
plt.close()

# RFM
snapshot_date = df["transaction_date"].max() + pd.Timedelta(days=1)
rfm = df.groupby("customer_id").agg(
    recency=("transaction_date", lambda x: (snapshot_date - x.max()).days),
    frequency=("transaction_id", "nunique"),
    monetary=("final_amount", "sum")
).reset_index()

rfm["R_score"] = pd.qcut(rfm["recency"], 4, labels=[4, 3, 2, 1]).astype(int)
rfm["F_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
rfm["M_score"] = pd.qcut(rfm["monetary"], 4, labels=[1, 2, 3, 4]).astype(int)
rfm["RFM_score"] = rfm["R_score"] + rfm["F_score"] + rfm["M_score"]

def segment_customer(score):
    if score >= 10: return "Champions"
    elif score >= 8: return "Loyal Customers"
    elif score >= 6: return "Potential Loyalists"
    elif score >= 4: return "At Risk"
    else: return "Lost Customers"

rfm["segment"] = rfm["RFM_score"].apply(segment_customer)

# 6. RFM segments
segment_counts = rfm["segment"].value_counts()
plt.figure(figsize=(9, 6))
sns.barplot(x=segment_counts.values, y=segment_counts.index, palette="viridis")
plt.title("Customer Segments (RFM)", fontsize=14, fontweight="bold")
plt.xlabel("Number of Customers")
plt.tight_layout()
plt.savefig("images/rfm_segments.png", dpi=150)
plt.close()

# 7. Elbow + clusters
rfm_features = rfm[["recency", "frequency", "monetary"]]
scaler = StandardScaler()
rfm_scaled = scaler.fit_transform(rfm_features)

inertias = []
K_range = range(1, 10)
for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(rfm_scaled)
    inertias.append(km.inertia_)

plt.figure(figsize=(8, 5))
plt.plot(K_range, inertias, marker="o", color="#4C72B0")
plt.title("Elbow Method for Optimal k")
plt.xlabel("Number of Clusters (k)"); plt.ylabel("Inertia")
plt.tight_layout()
plt.savefig("images/elbow_method.png", dpi=150)
plt.close()

kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
rfm["cluster"] = kmeans.fit_predict(rfm_scaled)

fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(projection="3d")
ax.scatter(rfm["recency"], rfm["frequency"], rfm["monetary"], c=rfm["cluster"], cmap="viridis", s=40, alpha=0.7)
ax.set_xlabel("Recency (days)"); ax.set_ylabel("Frequency (orders)"); ax.set_zlabel("Monetary (₹)")
ax.set_title("Customer Clusters based on RFM", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig("images/rfm_clusters_3d.png", dpi=150)
plt.close()

# 8. Cohort retention
df["signup_month"] = df["signup_date"].dt.to_period("M")
df["order_period"] = df["transaction_date"].dt.to_period("M")
df["cohort_index"] = (df["order_period"] - df["signup_month"]).apply(lambda x: x.n)
cohort_data = df.groupby(["signup_month", "cohort_index"])["customer_id"].nunique().reset_index()
cohort_pivot = cohort_data.pivot(index="signup_month", columns="cohort_index", values="customer_id")
cohort_size = cohort_pivot.iloc[:, 0]
retention = cohort_pivot.divide(cohort_size, axis=0)
retention_display = retention.iloc[:12, :12]

plt.figure(figsize=(14, 8))
sns.heatmap(retention_display, annot=True, fmt=".0%", cmap="Blues", cbar_kws={"label": "Retention Rate"})
plt.title("Monthly Cohort Retention Heatmap", fontsize=14, fontweight="bold")
plt.xlabel("Months Since Signup"); plt.ylabel("Signup Cohort")
plt.tight_layout()
plt.savefig("images/cohort_retention_heatmap.png", dpi=150)
plt.close()

print("All images generated in images/")
