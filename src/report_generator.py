
import pandas as pd
from analytics import DataLoader, KPIEngine

def generate_report():
    loader = DataLoader()
    df = loader.get_data()
    
    kpis, metrics = KPIEngine.calculate_kpis(df)
    partner_perf = KPIEngine.get_partner_performance(df)
    
    # Identify key insights
    top_partners = partner_perf.sort_values('revenue', ascending=False).head(5)
    underperformers = partner_perf[partner_perf['ROI'] < 1.0]
    
    report = f"""
# Affiliate Commerce Stakeholder Report 📈
**Generated on**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
* **Total Revenue**: ${metrics['revenue']:,.2f}
* **Total Commission Paid**: ${metrics['commission_paid']:,.2f}
* **ROI**: {kpis['ROI']*100:.1f}%
* **Total Orders**: {metrics['orders']}

## Top Recommendations
1. **Scale Top Performers**:
   - {top_partners.iloc[0]['partner_name']} (Rev: ${top_partners.iloc[0]['revenue']:.2f}, ROI: {top_partners.iloc[0]['ROI']:.2f})
   - {top_partners.iloc[1]['partner_name']} (Rev: ${top_partners.iloc[1]['revenue']:.2f}, ROI: {top_partners.iloc[1]['ROI']:.2f})

2. **Address Underperformance**:
   - Found {len(underperformers)} partners with ROI < 1.0 (Negative Return).
   - Review agreements with: {', '.join(underperformers.head(3)['partner_name'].tolist())}...

## Partner Leaderboard (Top 5)
| Partner | Revenue | ROI | EPC |
|---------|---------|-----|-----|
"""
    for _, row in top_partners.iterrows():
        report += f"| {row['partner_name']} | ${row['revenue']:.2f} | {row['ROI']:.2f} | ${row['EPC']:.2f} |\n"

    report += """
## Next Steps
* Deploy budget to high-ROI partners.
* Investigate 'Zero Conversation' campaigns.
* Monitor daily anomalies via Dashboard.

---
*New York Post Commerce Analytics Team*
"""
    
    with open("Stakeholder_Report.md", "w") as f:
        f.write(report)
    print("Report generated: Stakeholder_Report.md")

if __name__ == "__main__":
    generate_report()
