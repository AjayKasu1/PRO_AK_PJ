
import sqlite3
import pandas as pd
import numpy as np

DB_PATH = 'data/affiliate_commerce.db'

class DataLoader:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def get_data(self):
        """Fetches joined data for analysis."""
        conn = sqlite3.connect(self.db_path)
        
        # We need to join Traffic and Conversions
        # Since both are daily aggregates by Campaign, we join on (campaign_id, date)
        
        query = '''
        SELECT 
            t.date,
            t.campaign_id,
            t.device_type,
            t.channel,
            t.clicks,
            t.impressions,
            c.orders,
            c.revenue,
            c.commission_paid,
            p.partner_name,
            p.vertical,
            camp.campaign_name,
            camp.landing_page_variant
        FROM traffic t
        LEFT JOIN conversions c ON t.campaign_id = c.campaign_id AND t.date = c.date
        JOIN campaigns camp ON t.campaign_id = camp.campaign_id
        JOIN partners p ON camp.partner_id = p.partner_id
        '''
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Fill NaNs from Left Join (days with traffic but no sales)
        df.fillna({
            'orders': 0, 
            'revenue': 0.0, 
            'commission_paid': 0.0
        }, inplace=True)
        
        df['date'] = pd.to_datetime(df['date'])
        return df

class KPIEngine:
    @staticmethod
    def calculate_kpis(df):
        """Calculates aggregated KPIs from the raw dataframe."""
        
        # Aggregations
        metrics = df.agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'orders': 'sum',
            'revenue': 'sum',
            'commission_paid': 'sum'
        })
        
        # Safe Division
        def safe_div(a, b):
            return a / b if b > 0 else 0.0

        kpis = {}
        kpis['CTR'] = safe_div(metrics['clicks'], metrics['impressions'])
        kpis['Conversion_Rate'] = safe_div(metrics['orders'], metrics['clicks'])
        kpis['EPC'] = safe_div(metrics['revenue'], metrics['clicks'])
        kpis['AOV'] = safe_div(metrics['revenue'], metrics['orders'])
        kpis['ROI'] = safe_div((metrics['revenue'] - metrics['commission_paid']), metrics['commission_paid'])
        
        return kpis, metrics

    @staticmethod
    def get_partner_performance(df):
        """Returns a DataFrame of KPIs grouped by Partner."""
        
        # Group by partner_name AND vertical to preserve it
        grouped = df.groupby(['partner_name', 'vertical']).agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'orders': 'sum',
            'revenue': 'sum',
            'commission_paid': 'sum'
        }).reset_index()
        
        # Vectorized KPI calc
        grouped['CTR'] = grouped['clicks'] / grouped['impressions']
        grouped['Conversion_Rate'] = grouped['orders'] / grouped['clicks']
        grouped['EPC'] = grouped['revenue'] / grouped['clicks']
        grouped['AOV'] = grouped['revenue'] / grouped['orders']
        grouped['ROI'] = (grouped['revenue'] - grouped['commission_paid']) / grouped['commission_paid']
        
        # Handle Inf/NaN
        grouped.fillna(0, inplace=True)
        return grouped

    @staticmethod
    def get_campaign_performance(df):
        """Returns a DataFrame of KPIs grouped by Campaign."""
        grouped = df.groupby(['campaign_name', 'landing_page_variant']).agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'orders': 'sum',
            'revenue': 'sum',
            'commission_paid': 'sum'
        }).reset_index()
        
        grouped['CTR'] = grouped['clicks'] / grouped['impressions']
        grouped['Conversion_Rate'] = grouped['orders'] / grouped['clicks']
        grouped['EPC'] = grouped['revenue'] / grouped['clicks']
        grouped['ROI'] = (grouped['revenue'] - grouped['commission_paid']) / grouped['commission_paid']
        
        grouped.fillna(0, inplace=True)
        return grouped

class DataQuality:
    @staticmethod
    def run_checks(df):
        """Runs data quality checks and returns a report list."""
        issues = []
        
        # 1. CTR > 100% (Clicks > Impressions)
        invalid_ctr = df[df['clicks'] > df['impressions']]
        if not invalid_ctr.empty:
            issues.append(f"CRITICAL: Found {len(invalid_ctr)} rows where Clicks > Impressions.")
            
        # 2. Negative Revenue or Commission
        neg_val = df[(df['revenue'] < 0) | (df['commission_paid'] < 0)]
        if not neg_val.empty:
            issues.append(f"CRITICAL: Found {len(neg_val)} rows with negative Revenue or Commission.")
            
        # 3. Nulls (should be handled by DataLoader, but checking raw cols)
        nulls = df.isnull().sum().sum()
        if nulls > 0:
            issues.append(f"WARNING: Found {nulls} missing values in dataset.")
            
        # 4. Outlier Detection (Z-Score on Revenue)
        # Filter for rows with revenue > 0
        rev_data = df[df['revenue'] > 0]['revenue']
        if not rev_data.empty:
            mean = rev_data.mean()
            std = rev_data.std()
            z_scores = (rev_data - mean) / std
            outliers = z_scores.abs() > 3
            if outliers.sum() > 0:
                issues.append(f"INFO: Detected {outliers.sum()} revenue outliers (>3 Std Dev).")
                
        if not issues:
            issues.append("PASSED: All data quality checks passed.")
            
        return issues

if __name__ == "__main__":
    loader = DataLoader()
    data = loader.get_data()
    print(f"Loaded {len(data)} rows.")
    
    print("\n--- Data Quality Checks ---")
    dq = DataQuality()
    for msg in dq.run_checks(data):
        print(msg)
        
    print("\n--- Overall KPIs ---")
    kpis, _ = KPIEngine.calculate_kpis(data)
    for k, v in kpis.items():
        print(f"{k}: {v:.4f}")
        
    print("\n--- Top 3 Partners by ROI ---")
    perf = KPIEngine.get_partner_performance(data)
    print(perf.sort_values('ROI', ascending=False).head(3)[['partner_name', 'ROI', 'revenue']])
