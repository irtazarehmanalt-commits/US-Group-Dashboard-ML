import pandas as pd
from .db import run_sql

def get_report_sections() -> list[dict]:
    """Each section = a title, a deterministic SQL-derived DataFrame, and a chart type.
    These are FIXED business decisions, not left up to the LLM."""

    sections = []

    profit_by_company = run_sql('''
        SELECT "Sub_Company", SUM("Net_Profit_USD") AS total_profit
        FROM orders GROUP BY "Sub_Company" ORDER BY total_profit DESC
    ''')
    sections.append({
        "title": "Total Profit by Sub-Company",
        "data": profit_by_company,
        "chart_type": "bar"
    })

    monthly_trend = run_sql('''
        SELECT "Year", "Month", SUM("Net_Profit_USD") AS total_profit
        FROM orders GROUP BY "Year", "Month" ORDER BY "Year", "Month"
    ''')
    sections.append({
        "title": "Monthly Profit Trend",
        "data": monthly_trend,
        "chart_type": "line"
    })

    payment_status = run_sql('''
        SELECT CASE WHEN "Is_Delayed_Payment" = 1 THEN 'Delayed' ELSE 'On Time' END AS status,
               COUNT(*) AS order_count
        FROM orders WHERE "Order_Status" IN ('Dispatched', 'Delayed')
        GROUP BY status
    ''')
    sections.append({
        "title": "Payment Timeliness",
        "data": payment_status,
        "chart_type": "pie"
    })

    top_customers = run_sql('''
        SELECT "Customer_Name", SUM("Net_Profit_USD") AS total_profit
        FROM orders GROUP BY "Customer_Name" ORDER BY total_profit DESC LIMIT 5
    ''')
    sections.append({
        "title": "Top 5 Customers by Profit",
        "data": top_customers,
        "chart_type": "bar"
    })

    return sections