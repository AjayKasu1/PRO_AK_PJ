
import sqlite3
import pandas as pd
import numpy as np
import os

# Configuration
CSV_PATH = 'dataset/amazon_affiliate_clicks.csv'
DB_PATH = 'data/affiliate_commerce.db'

def init_db():
    """Initialize the SQLite database schema."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tables
    cursor.execute('''
        CREATE TABLE partners (
            partner_id INTEGER PRIMARY KEY,
            partner_name TEXT UNIQUE,
            vertical TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE campaigns (
            campaign_id INTEGER PRIMARY KEY,
            partner_id INTEGER,
            campaign_name TEXT,
            landing_page_variant TEXT,
            FOREIGN KEY(partner_id) REFERENCES partners(partner_id)
        )
    ''')
    
    # Traffic table: Daily aggregation of impressions/clicks
    cursor.execute('''
        CREATE TABLE traffic (
            traffic_id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER,
            date DATE,
            device_type TEXT,
            channel TEXT,
            impressions INTEGER,
            clicks INTEGER,
            FOREIGN KEY(campaign_id) REFERENCES campaigns(campaign_id)
        )
    ''')
    
    # Conversions table: Daily aggregation of sales
    cursor.execute('''
        CREATE TABLE conversions (
            conversion_id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER,
            date DATE,
            orders INTEGER,
            revenue REAL,
            commission_paid REAL,
            FOREIGN KEY(campaign_id) REFERENCES campaigns(campaign_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database schema initialized.")

def ingest_and_augment():
    print(f"Reading {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    
    # Preprocessing
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    
    # specific fix for 'device_type' if needed, assuming column exists as per head command
    # Columns seen: click_id,user_id,session_id,timestamp,product_asin,... device_type ... utm_source, utm_medium, utm_campaign
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Populate Partners (from utm_source)
    print("Populating Partners...")
    unique_partners = df['utm_source'].unique()
    partners_df = pd.DataFrame({'partner_name': unique_partners})
    # Assign a random vertical for variety if not inferable
    verticals = ['Tech', 'Fashion', 'Home', 'Beauty', 'Finance']
    partners_df['vertical'] = [np.random.choice(verticals) for _ in range(len(partners_df))]
    partners_df.reset_index(inplace=True)
    partners_df.rename(columns={'index': 'partner_id'}, inplace=True)
    partners_df['partner_id'] += 1 # 1-based ID
    
    partners_df.to_sql('partners', conn, if_exists='append', index=False)
    
    # Helper map for partner mapping later
    partner_map = dict(zip(partners_df['partner_name'], partners_df['partner_id']))
    
    # 2. Populate Campaigns (from utm_campaign)
    print("Populating Campaigns...")
    # diverse campaigns: distinct (utm_source, utm_campaign) pairs? 
    # A campaign usually belongs to a partner.
    unique_campaigns = df[['utm_source', 'utm_campaign']].drop_duplicates()
    unique_campaigns['partner_id'] = unique_campaigns['utm_source'].map(partner_map)
    unique_campaigns['campaign_name'] = unique_campaigns['utm_campaign']
    unique_campaigns['landing_page_variant'] = [np.random.choice(['A', 'B']) for _ in range(len(unique_campaigns))]
    
    unique_campaigns.reset_index(drop=True, inplace=True)
    unique_campaigns.reset_index(inplace=True)
    unique_campaigns.rename(columns={'index': 'campaign_id'}, inplace=True)
    unique_campaigns['campaign_id'] += 1
    
    # Select cols for DB
    campaigns_db = unique_campaigns[['campaign_id', 'partner_id', 'campaign_name', 'landing_page_variant']]
    campaigns_db.to_sql('campaigns', conn, if_exists='append', index=False)
    
    # Map for later
    # Create a compound key dict: (source, campaign_name) -> campaign_id
    camp_map = dict(zip(zip(unique_campaigns['utm_source'], unique_campaigns['utm_campaign']), unique_campaigns['campaign_id']))
    
    # 3. Process Traffic (Impressions & Click counts)
    print("Processing Traffic...")
    # Group by key dims
    traffic_groups = df.groupby(['date', 'utm_source', 'utm_campaign', 'device_type', 'utm_medium']).size().reset_index(name='clicks')
    
    traffic_rows = []
    
    for _, row in traffic_groups.iterrows():
        camp_id = camp_map.get((row['utm_source'], row['utm_campaign']))
        if not camp_id: continue
        
        clicks = row['clicks']
        
        # Back-calculate Impressions
        # Random CTR between 0.5% and 3.5%
        ctr = np.random.uniform(0.005, 0.035) 
        impressions = int(clicks / ctr)
        if impressions < clicks: impressions = clicks # Safety
        
        traffic_rows.append({
            'campaign_id': camp_id,
            'date': row['date'],
            'device_type': row['device_type'],
            'channel': row['utm_medium'],
            'impressions': impressions,
            'clicks': clicks
        })
        
    pd.DataFrame(traffic_rows).to_sql('traffic', conn, if_exists='append', index=False)
    
    # 4. Simulate Conversions
    print("Simulating Conversions...")
    # We can iterate through the raw DataFrame to "simulate" based on product price/category
    # Or just do it at the aggregate level for simplicity and speed.
    # Let's do it at aggregate level using the traffic_rows but we need to know what products were clicked to be accurate about Revenue...
    # Actually, the CSV has 'product_price'. We should probably aggregate by product too? 
    # Or just average product price for that day/campaign?
    # Let's go back to the raw DF for accurate Revenue simulation.
    
    # Add campaign_id to main df
    df['campaign_id'] = df.apply(lambda x: camp_map.get((x['utm_source'], x['utm_campaign'])), axis=1)
    
    conversion_rows = []
    
    # Group by date/campaign to output daily conversion stats
    # But first, determine 'is_converted' row by row
    
    # Vectorized conversion simulation
    # Base CVR 5%. Product Category modifiers could be added.
    np.random.seed(42)
    df['random_draw'] = np.random.random(len(df))
    # Higher price -> Lower conversion
    # Simple logic: CVR = Base * (100 / Price) ... clamped
    # Let's say baseline CVR is ~5%
    # Adjust based on price: Cheap items convert higher.
    # We don't have infinite time, simple heuristic:
    df['cvr_prob'] = 0.05 * (50.0 / (df['product_price'] + 10)) # Heuristic
    df['cvr_prob'] = df['cvr_prob'].clip(0.01, 0.15) # Cap between 1% and 15%
    
    df['is_converted'] = df['random_draw'] < df['cvr_prob']
    
    # Calculate revenue for converted rows
    # Commission rate 20-30%
    df['commission_rate'] = np.random.uniform(0.20, 0.30, len(df))
    df['revenue_amt'] = np.where(df['is_converted'], df['product_price'], 0)
    df['commission_amt'] = df['revenue_amt'] * df['commission_rate']
    
    # Aggregate to creation Convs table
    conv_agg = df.groupby(['date', 'campaign_id']).agg({
        'is_converted': 'sum',
        'revenue_amt': 'sum',
        'commission_amt': 'sum'
    }).reset_index()
    
    conv_agg.rename(columns={
        'is_converted': 'orders',
        'revenue_amt': 'revenue',
        'commission_amt': 'commission_paid'
    }, inplace=True)
    
    # Filter out days with 0 conversions? No, keep them as 0 for data completeness if campaign was active.
    # The traffic table defines 'active', so only insert if there's traffic?
    # Actually, just inserting non-zero rows is fine, or all rows. 
    # Let's insert all rows where traffic existed (which matches our grouping).
    
    conv_agg.to_sql('conversions', conn, if_exists='append', index=False)
    
    conn.commit()
    conn.close()
    
    print(f"Data ingestion complete. {len(traffic_rows)} traffic records, {len(conv_agg)} conversion records.")

if __name__ == "__main__":
    if not os.path.exists('data'):
        os.makedirs('data')
    init_db()
    ingest_and_augment()
