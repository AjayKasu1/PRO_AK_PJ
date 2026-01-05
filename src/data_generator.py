
import sqlite3
import pandas as pd
import numpy as np
import datetime
import random
import os

# Configuration
DB_PATH = 'data/affiliate_commerce.db'
NUM_PARTNERS = 25
NUM_CAMPAIGNS = 100
START_DATE = datetime.date.today() - datetime.timedelta(days=180) # 6 months ago
END_DATE = datetime.date.today()

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
            partner_name TEXT,
            vertical TEXT,
            tier TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE campaigns (
            campaign_id INTEGER PRIMARY KEY,
            partner_id INTEGER,
            campaign_name TEXT,
            vertical TEXT,
            start_date DATE,
            end_date DATE,
            landing_page_variant TEXT,
            FOREIGN KEY(partner_id) REFERENCES partners(partner_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE traffic (
            traffic_id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER,
            date DATE,
            impressions INTEGER,
            clicks INTEGER,
            device_type TEXT,
            channel TEXT,
            FOREIGN KEY(campaign_id) REFERENCES campaigns(campaign_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE conversions (
            conversion_id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER,
            date DATE,
            orders INTEGER,
            revenue REAL,
            commission_paid REAL,
            new_customer_flag BOOLEAN,
            FOREIGN KEY(campaign_id) REFERENCES campaigns(campaign_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database schema initialized.")

def generate_data():
    """Generates synthetic data for the affiliate platform."""
    
    np.random.seed(42)
    random.seed(42)
    
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Partners
    verticals = ['Tech', 'Fashion', 'Home', 'Beauty', 'Finance']
    tiers = ['Gold', 'Silver', 'Bronze']
    
    partners = []
    for i in range(1, NUM_PARTNERS + 1):
        partners.append({
            'partner_id': i,
            'partner_name': f"Partner_{i}_{random.choice(['Media', 'Blog', 'News', 'Reviews'])}",
            'vertical': random.choice(verticals),
            'tier': random.choice(tiers)
        })
    pd.DataFrame(partners).to_sql('partners', conn, if_exists='append', index=False)
    
    # 2. Campaigns
    campaigns = []
    for i in range(1, NUM_CAMPAIGNS + 1):
        partner = random.choice(partners)
        campaigns.append({
            'campaign_id': i,
            'partner_id': partner['partner_id'],
            'campaign_name': f"{partner['vertical']}_Promo_{i}",
            'vertical': partner['vertical'],
            'start_date': START_DATE,
            'end_date': END_DATE,
            'landing_page_variant': random.choice(['A', 'B'])
        })
    pd.DataFrame(campaigns).to_sql('campaigns', conn, if_exists='append', index=False)
    
    # 3. Traffic & Conversions
    # Generate daily data
    
    date_range = pd.date_range(start=START_DATE, end=END_DATE)
    
    traffic_data = []
    conversion_data = []
    
    device_types = ['Mobile', 'Desktop', 'Tablet']
    channels = ['Organic', 'Social', 'Email', 'Paid Search']
    
    print("Generating daily traffic and conversion data...")
    
    for date in date_range:
        is_weekend = date.weekday() >= 5
        seasonality_factor = 1.2 if is_weekend else 1.0
        
        for camp in campaigns:
            # Skip some campaigns on some days for realism
            if random.random() < 0.1:
                continue
                
            # Base Impressions
            # Certain verticals/partners get more traffic
            base_impressions = np.random.lognormal(mean=6, sigma=1) * seasonality_factor # ~400-1000 range
            impressions = int(base_impressions)
            
            # Clicks (CTR 0.5% - 3%)
            ctr_base = np.random.beta(2, 100) # shape for low probabilities
            clicks = int(impressions * ctr_base)
            if clicks > impressions: clicks = impressions
            if clicks == 0: continue # No conversions if no clicks
            
            # Traffic Entry
            # Distribute across devices/channels (simplified: one entry per campaign/day aggregate to keep DB small, 
            # or we create multiple rows? Prompt implies 'traffic' table has these cols. 
            # To show granularity, let's create 1-2 rows per campaign per day with split metrics)
            
            # Simplified: 1 row per campaign/day
            traffic_data.append({
                'campaign_id': camp['campaign_id'],
                'date': date.date(),
                'impressions': impressions,
                'clicks': clicks,
                'device_type': random.choice(device_types), # Predominant device
                'channel': random.choice(channels)
            })
            
            # Conversions (CVR 2% - 8%)
            # Some variance based on Landing Page Variant
            cvr_boost = 1.15 if camp['landing_page_variant'] == 'B' else 1.0
            cvr = np.random.uniform(0.02, 0.08) * cvr_boost
            
            orders = np.random.binomial(clicks, cvr)
            
            if orders > 0:
                # Revenue (AOV $15 - $120)
                aov = np.random.normal(60, 20)
                if aov < 15: aov = 15
                
                revenue = orders * aov
                commission_rate = np.random.uniform(0.20, 0.40)
                commission = revenue * commission_rate
                
                conversion_data.append({
                    'campaign_id': camp['campaign_id'],
                    'date': date.date(),
                    'orders': orders,
                    'revenue': round(revenue, 2),
                    'commission_paid': round(commission, 2),
                    'new_customer_flag': random.choice([True, False]) # Simplified aggregate flag or dominant type
                })
            else:
                 conversion_data.append({
                    'campaign_id': camp['campaign_id'],
                    'date': date.date(),
                    'orders': 0,
                    'revenue': 0.0,
                    'commission_paid': 0.0,
                    'new_customer_flag': False
                })

    # Bulk Insert
    print("Inserting data into DB...")
    traffic_df = pd.DataFrame(traffic_data)
    pd.DataFrame(traffic_data).to_sql('traffic', conn, if_exists='append', index=False)
    
    conversion_df = pd.DataFrame(conversion_data)
    pd.DataFrame(conversion_data).to_sql('conversions', conn, if_exists='append', index=False)
    
    conn.commit()
    conn.close()
    print(f"Data generation complete. Database saved to {DB_PATH}")

if __name__ == "__main__":
    if not os.path.exists('data'):
        os.makedirs('data')
    init_db()
    generate_data()
