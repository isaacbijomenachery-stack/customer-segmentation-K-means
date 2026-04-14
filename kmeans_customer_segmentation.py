# =============================================================================
# CUSTOMER SEGMENTATION USING K-MEANS CLUSTERING
# =============================================================================
# Description : Segments customers using RFM (Recency, Frequency, Monetary)
#               features and K-Means clustering algorithm.
# Dataset     : Online Retail Dataset (UCI / Kaggle)
# Libraries   : pandas, numpy, scikit-learn, matplotlib, seaborn
# =============================================================================

# ── 1. IMPORTS ────────────────────────────────────────────────────────────────
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import seaborn as sns
import warnings

from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, silhouette_samples

warnings.filterwarnings('ignore')
plt.style.use('seaborn-v0_8-darkgrid')


# ── 2. LOAD DATA ──────────────────────────────────────────────────────────────
# Option A: Load from CSV (Online Retail Dataset)
# df = pd.read_csv('OnlineRetail.csv', encoding='ISO-8859-1')

# Option B: Generate synthetic data for demonstration
def generate_synthetic_data(n=1000, seed=42):
    """Generate synthetic customer transaction data."""
    np.random.seed(seed)
    now = datetime(2011, 12, 31)

    customer_ids = np.random.randint(10000, 18000, n)
    days_ago = np.concatenate([
        np.random.randint(1, 30, 200),    # Champions - recent
        np.random.randint(100, 300, 250), # At-Risk - inactive
        np.random.randint(20, 80, 300),   # Potential Loyalists
        np.random.randint(200, 365, 250)  # Hibernating - very old
    ])
    invoice_dates = [now - pd.Timedelta(days=int(d)) for d in days_ago[:n]]
    quantities = np.random.randint(1, 20, n)
    unit_prices = np.round(np.random.uniform(1.0, 50.0, n), 2)

    df = pd.DataFrame({
        'CustomerID': customer_ids,
        'InvoiceDate': invoice_dates,
        'InvoiceNo': ['INV' + str(i) for i in range(n)],
        'Quantity': quantities,
        'UnitPrice': unit_prices
    })
    return df

df = generate_synthetic_data(n=2000)
print("Dataset Shape:", df.shape)
print(df.head())


# ── 3. DATA PREPROCESSING ─────────────────────────────────────────────────────
# Remove nulls and negative quantities/prices
df.dropna(subset=['CustomerID'], inplace=True)
df = df[df['Quantity'] > 0]
df = df[df['UnitPrice'] > 0]

# Compute TotalPrice per transaction
df['TotalPrice'] = df['Quantity'] * df['UnitPrice']

print(f"\nCleaned Dataset Shape: {df.shape}")
print(f"Unique Customers: {df['CustomerID'].nunique()}")


# ── 4. RFM FEATURE ENGINEERING ────────────────────────────────────────────────
snapshot_date = df['InvoiceDate'].max() + pd.Timedelta(days=1)

rfm = df.groupby('CustomerID').agg(
    Recency   = ('InvoiceDate', lambda x: (snapshot_date - x.max()).days),
    Frequency = ('InvoiceNo',   'count'),
    Monetary  = ('TotalPrice',  'sum')
).reset_index()

# Log-transform Monetary and Frequency to reduce skewness
rfm['Monetary_log']  = np.log1p(rfm['Monetary'])
rfm['Frequency_log'] = np.log1p(rfm['Frequency'])

print("\nRFM Feature Summary:")
print(rfm[['Recency', 'Frequency', 'Monetary']].describe().round(2))


# ── 5. FEATURE SCALING ────────────────────────────────────────────────────────
features = ['Recency', 'Frequency_log', 'Monetary_log']
X = rfm[features].values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print(f"\nScaled Feature Shape: {X_scaled.shape}")


# ── 6. ELBOW METHOD – Find Optimal K ──────────────────────────────────────────
inertia_values = []
k_range = range(1, 11)

for k in k_range:
    km_temp = KMeans(n_clusters=k, init='k-means++', n_init=10,
                     max_iter=300, random_state=42)
    km_temp.fit(X_scaled)
    inertia_values.append(km_temp.inertia_)

plt.figure(figsize=(9, 5))
plt.plot(k_range, inertia_values, 'o-', color='#6c63ff', linewidth=2.5,
         markersize=8, markerfacecolor='white', markeredgewidth=2)
plt.axvline(x=4, color='#ff6584', linestyle='--', linewidth=1.5,
            label='Optimal K = 4')
plt.title('Elbow Method – Optimal Number of Clusters', fontsize=14, fontweight='bold')
plt.xlabel('Number of Clusters (K)')
plt.ylabel('Inertia (Within-Cluster Sum of Squares)')
plt.xticks(k_range)
plt.legend()
plt.tight_layout()
plt.savefig('elbow_method.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saved: elbow_method.png")


# ── 7. SILHOUETTE ANALYSIS ────────────────────────────────────────────────────
silhouette_scores = []
for k in range(2, 11):
    km_s = KMeans(n_clusters=k, init='k-means++', n_init=10,
                  random_state=42)
    labels_s = km_s.fit_predict(X_scaled)
    score = silhouette_score(X_scaled, labels_s)
    silhouette_scores.append(score)
    print(f"  K={k:2d}  Silhouette Score: {score:.4f}")

best_k = np.argmax(silhouette_scores) + 2
print(f"\nBest K by Silhouette: {best_k}")


# ── 8. FIT FINAL K-MEANS MODEL ────────────────────────────────────────────────
K = 4
kmeans = KMeans(n_clusters=K, init='k-means++', n_init=10,
                max_iter=300, random_state=42)
rfm['Cluster'] = kmeans.fit_predict(X_scaled)

final_score = silhouette_score(X_scaled, rfm['Cluster'])
print(f"\nFinal Model  →  K={K}  |  Silhouette Score: {final_score:.4f}")
print(f"Inertia: {kmeans.inertia_:.2f}")


# ── 9. CLUSTER PROFILING ──────────────────────────────────────────────────────
cluster_profile = rfm.groupby('Cluster').agg(
    Count     = ('CustomerID',  'count'),
    Recency   = ('Recency',     'mean'),
    Frequency = ('Frequency',   'mean'),
    Monetary  = ('Monetary',    'mean')
).round(2)

cluster_profile['% Share'] = (
    cluster_profile['Count'] / cluster_profile['Count'].sum() * 100
).round(1)

# Assign intuitive labels
segment_labels = {
    cluster_profile['Monetary'].idxmax():  '🏆 Champions',
    cluster_profile['Recency'].idxmax():   '💤 Hibernating',
    cluster_profile['Monetary'].nlargest(2).index[-1]: '⚠️ At-Risk',
}
# Remaining cluster = Potential Loyalists
remaining = [i for i in range(K) if i not in segment_labels]
for r in remaining:
    segment_labels[r] = '🌱 Potential Loyalists'

cluster_profile['Segment'] = cluster_profile.index.map(segment_labels)
print("\nCluster Profile:")
print(cluster_profile.to_string())


# ── 10. VISUALIZATION ─────────────────────────────────────────────────────────
COLORS = ['#6c63ff', '#ff6584', '#43e97b', '#f7971e']

# ── 10a. Scatter: Recency vs Monetary ────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('K-Means Customer Segmentation (K=4)', fontsize=16, fontweight='bold')

# Plot 1: Recency vs Frequency
ax = axes[0]
for i in range(K):
    mask = rfm['Cluster'] == i
    ax.scatter(rfm.loc[mask, 'Recency'],
               rfm.loc[mask, 'Frequency'],
               c=COLORS[i], alpha=0.6, s=50,
               label=segment_labels.get(i, f'Cluster {i}'))
centers = scaler.inverse_transform(kmeans.cluster_centers_)
for i, c in enumerate(centers):
    ax.scatter(c[0], np.expm1(c[1]), marker='X', s=200,
               c=COLORS[i], edgecolors='white', linewidths=1.5, zorder=5)
ax.set_xlabel('Recency (days)')
ax.set_ylabel('Frequency (purchases)')
ax.set_title('Recency vs Frequency')
ax.legend(fontsize=8)

# Plot 2: Frequency vs Monetary
ax = axes[1]
for i in range(K):
    mask = rfm['Cluster'] == i
    ax.scatter(rfm.loc[mask, 'Frequency'],
               rfm.loc[mask, 'Monetary'],
               c=COLORS[i], alpha=0.6, s=50,
               label=segment_labels.get(i, f'Cluster {i}'))
for i, c in enumerate(centers):
    ax.scatter(np.expm1(c[1]), np.expm1(c[2]), marker='X', s=200,
               c=COLORS[i], edgecolors='white', linewidths=1.5, zorder=5)
ax.set_xlabel('Frequency (purchases)')
ax.set_ylabel('Monetary Value (£)')
ax.set_title('Frequency vs Monetary Value')
ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig('cluster_scatter.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saved: cluster_scatter.png")

# ── 10b. RFM Heatmap ─────────────────────────────────────────────────────────
pivot = cluster_profile[['Recency', 'Frequency', 'Monetary']].copy()
pivot_norm = (pivot - pivot.min()) / (pivot.max() - pivot.min())

fig, ax = plt.subplots(figsize=(8, 4))
sns.heatmap(pivot_norm, annot=pivot.round(1), fmt='g',
            cmap='RdYlGn', linewidths=0.5, ax=ax,
            yticklabels=[segment_labels.get(i, f'C{i}') for i in pivot_norm.index])
ax.set_title('RFM Heatmap by Cluster (normalized)', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('rfm_heatmap.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saved: rfm_heatmap.png")

# ── 10c. Cluster Size Bar Chart ───────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 4))
segments = [segment_labels.get(i, f'C{i}') for i in range(K)]
counts = [cluster_profile.loc[i, 'Count'] for i in range(K)]
bars = ax.bar(segments, counts, color=COLORS, edgecolor='white', linewidth=0.8)
for bar, count in zip(bars, counts):
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 5, str(count),
            ha='center', va='bottom', fontweight='bold')
ax.set_title('Number of Customers per Segment', fontsize=13, fontweight='bold')
ax.set_ylabel('Customer Count')
ax.set_xlabel('Segment')
plt.xticks(rotation=15, ha='right')
plt.tight_layout()
plt.savefig('cluster_bar.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saved: cluster_bar.png")


# ── 11. EXPORT RESULTS ────────────────────────────────────────────────────────
rfm['Segment'] = rfm['Cluster'].map(segment_labels)
output = rfm[['CustomerID', 'Recency', 'Frequency', 'Monetary', 'Cluster', 'Segment']]
output.to_csv('customer_segments.csv', index=False)
print("\nSegmented data saved to: customer_segments.csv")
print("\nFinal Segment Distribution:")
print(rfm['Segment'].value_counts())


# ── 12. MARKETING RECOMMENDATIONS ─────────────────────────────────────────────
recommendations = {
    '🏆 Champions':         'Reward with loyalty programs, early access, VIP perks.',
    '⚠️ At-Risk':           'Send win-back campaigns with personalized discounts.',
    '🌱 Potential Loyalists':'Nurture with recommendations, membership incentives.',
    '💤 Hibernating':       'Re-engage with aggressive offers or suppress from lists.'
}

print("\n" + "="*60)
print("MARKETING RECOMMENDATIONS BY SEGMENT")
print("="*60)
for seg, rec in recommendations.items():
    print(f"\n{seg}\n  → {rec}")
print("="*60)
