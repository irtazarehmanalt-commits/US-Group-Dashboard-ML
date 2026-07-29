import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

pg_engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)



ORDERS_SCHEMA = """
Table: orders

CRITICAL RULES (apply to EVERY query):
1. ALL column names are case-sensitive and MUST be wrapped in double quotes 
   exactly as written below, e.g. "Sub_Company", "Net_Profit_USD". 
   NEVER write unquoted or lowercase column names.
2. Only use column names that appear in this schema. Do not invent or guess 
   column names.
3. This is PostgreSQL syntax, not MySQL or SQLite.
4. Only generate SELECT statements. Never write INSERT, UPDATE, DELETE, DROP, 
   ALTER, CREATE, or TRUNCATE.

COLUMN REFERENCE (name — data type — notes/valid values):

Identifiers & Dates:
- "Order_ID" — text — unique order identifier, e.g. 'USG-2025-000123'
- "Order_Date" — timestamp — native date/time, no casting needed for comparisons
- "Dispatch_Date" — timestamp — same as above
- "Fiscal_Year" — text — format 'FY2025', 'FY2026' (Pakistani fiscal year: July-June)
- "Fiscal_Quarter" — text — one of: 'Q1', 'Q2', 'Q3', 'Q4'
- "Year" — integer — calendar year, e.g. 2025, 2026
- "Month" — integer — calendar month, 1 through 12

Company Structure:
- "Sub_Company" — text — one of: 'USAT', 'US Denim', 'USDNF', 'Styler'
- "Division" — text — one of: 'USA', 'UK', or NULL (only USAT has a Division; 
  the other three sub-companies have NULL here, NOT the string 'N/A')
- "Unit" — text — one of: 'Unit 1' through 'Unit 10' (exact format with space, 
  e.g. 'Unit 5', not 'Unit5' or '5')
- "Unit_Employee_Count" — integer — headcount at that unit
- "Unit_Monthly_Utilization_Pct" — numeric — percentage, e.g. 88.32 means 88.32%

Customer Info:
- "Customer_Name" — text — company name, highly varied, avoid filtering on 
  exact match unless the user gives an exact name
- "Customer_Country" — text — one of: 'USA', 'UK', 'Germany', 'Turkey', 'UAE', 
  'Bangladesh', 'Italy', 'Netherlands', 'Sri Lanka', 'Saudi Arabia'
- "Customer_Segment" — text — one of: 'Key Account', 'Regular', 'New Customer'
- "Order_Priority" — text — one of: 'High', 'Medium', 'Low'

Product Info:
- "Product_Category" — text — one of: 'Denim Fabric', 'Non-Denim Fabric', 
  'Denim Garments', 'Twill Garments', 'Footwear', 'Lifestyle Apparel'
- "UOM" — text — unit of measure, one of: 'Meters', 'Pieces', 'Pairs'

Quantities & Pricing (all numeric):
- "Order_Quantity" — integer — quantity ordered, in the unit given by "UOM"
- "Unit_Price_USD" — numeric — price per unit, in US Dollars
- "Discount_Pct" — numeric — percentage, e.g. 2.5 means 2.5%
- "Dispatch_Quantity" — integer — actual quantity shipped (may be less than 
  Order_Quantity, or 0 if order was Cancelled/Pending)

Financials (all numeric, all in USD unless stated otherwise):
- "Gross_Order_Value_USD", "Discount_Amount_USD", "Net_Order_Value_USD"
- "Dispatch_Value_USD" — the actual dollar value of what was shipped
- "Exchange_Rate_PKR_per_USD" — numeric — PKR per 1 USD
- "Dispatch_Value_PKR" — same as Dispatch_Value_USD but converted to Pakistani Rupees
- "Raw_Material_Cost_USD", "Labor_Cost_USD", "Overhead_Cost_USD", "Energy_Cost_USD"
- "COGS_USD" — Cost of Goods Sold
- "Freight_Cost_USD", "Insurance_Cost_USD", "Duty_Tax_USD", "Total_Cost_USD"
- "Gross_Profit_USD", "Net_Profit_USD" — use Net_Profit_USD for "profit" 
  questions unless the user specifically says "gross profit"
- "Gross_Margin_Pct", "Net_Margin_Pct" — numeric, already a percentage 
  (e.g. 21.5 means 21.5%, do NOT multiply by 100)

Payment Info:
- "Payment_Terms" — text — one of: 'TT Advance', 'TT 30 Days', 'DA 60 Days', 
  'LC 60 Days', 'LC 90 Days', 'Open Account 45 Days'
- "Advance_Payment_Pct" — numeric — percentage
- "Credit_Days" — integer — number of days of credit given
- "Payment_Delay_Days" — integer — 0 if paid on time, positive number if late

Quality & Logistics:
- "Defect_Rate_Pct" — numeric — percentage
- "Return_Quantity" — integer
- "Shipping_Mode" — text — one of: 'Sea', 'Air'
- "Order_Status" — text — one of: 'Dispatched', 'Pending', 'Cancelled', 'Delayed'

Boolean-style flags — IMPORTANT: these are stored as INTEGER (0 or 1), 
NOT as PostgreSQL boolean type. Always compare with = 1 or = 0, 
NEVER use 't', 'f', TRUE, or FALSE:
- "Is_Profitable" — 1 = profitable, 0 = not profitable
- "Is_Delayed_Payment" — 1 = payment was delayed, 0 = paid on time
- "Is_High_Value_Order" — 1 = order value exceeds $100,000, 0 = otherwise

COMMON QUESTION PATTERNS:

- "profit" or "profitable" → use "Net_Profit_USD" (continuous amount) or 
  "Is_Profitable" (yes/no filter/count), depending on whether the question 
  asks for an amount or a count/filter.

- "margin" → "Net_Margin_Pct" unless "gross margin" is specifically mentioned.

- "last month" → the data's most recent month is NOT necessarily December, 
  and the max Year alone does not tell you the most recent month. 
  ALWAYS use this exact pattern, do not simplify or guess the month number:

  WITH latest AS (
    SELECT "Year", "Month" FROM orders ORDER BY "Year" DESC, "Month" DESC LIMIT 1
  ),
  target AS (
    SELECT
      CASE WHEN "Month" = 1 THEN "Year" - 1 ELSE "Year" END AS target_year,
      CASE WHEN "Month" = 1 THEN 12 ELSE "Month" - 1 END AS target_month
    FROM latest
  )
  SELECT ... FROM orders, target
  WHERE orders."Year" = target.target_year AND orders."Month" = target.target_month

- "this month" / "current month" → same idea, but use the "latest" CTE's 
  Year/Month directly, without the target adjustment:
  WITH latest AS (
    SELECT "Year", "Month" FROM orders ORDER BY "Year" DESC, "Month" DESC LIMIT 1
  )
  SELECT ... FROM orders, latest
  WHERE orders."Year" = latest."Year" AND orders."Month" = latest."Month"

- "this year" / "in 2025" → filter on "Year" directly, e.g. WHERE "Year" = 2025.
  For "this year" without a number given, use:
  WHERE "Year" = (SELECT MAX("Year") FROM orders)

- "last year" → WHERE "Year" = (SELECT MAX("Year") FROM orders) - 1

- "delayed" (without qualifying "payment") → could mean "Order_Status" = 
  'Delayed' (shipping delay) OR "Is_Delayed_Payment" = 1 (payment delay). 
  Prefer "Order_Status" = 'Delayed' unless the question clearly mentions 
  payment, invoice, or being paid.

- "cancelled" → "Order_Status" = 'Cancelled'

- top / best / highest N → use ORDER BY ... DESC LIMIT N

- "average" → use AVG(). Remember _Pct columns are already percentages — 
  do not multiply by 100 again.

- Questions comparing two or more specific groups (e.g. "compare USAT and 
  Styler") → use GROUP BY with a WHERE ... IN (...) filter, and return one 
  row per group rather than a single combined number.
"""


# added: schema for the scraped_products table so the text-to-SQL chatbot can
# answer questions about external retail-brand pricing (e.g. "what does Levi's
# charge for men's jeans?"). Unlike the orders table, these columns are plain
# lowercase and must NOT be double-quoted.
PRODUCTS_SCHEMA = """
Table: scraped_products

This table holds competitor / retail-brand product listings scraped from
external brand websites (e.g. Levi's). Use it ONLY when the question is about
an outside brand's own retail products or prices - NOT for US Group's own
orders, profit, customers, or units (those live in the orders table).

RULES:
1. Column names are plain lowercase - do NOT wrap them in double quotes.
2. PostgreSQL syntax. SELECT statements only.
3. When a question asks for the "latest" prices, order by scraped_at DESC.
4. When the user asks to SEE or SHOW a product, its picture/image/photo, or to
   list/browse products, SELECT name, price, image_url, url (so the app can
   render product cards with thumbnails) - not just one column.

COLUMN REFERENCE (name - data type - notes):
- id          - integer   - row id
- brand       - text      - retail brand name, e.g. 'Levi's'
- name        - text      - product name / title
- price       - numeric   - price as a number (currency symbol already stripped)
- category    - text      - category label given at scrape time, e.g. 'Men's Jeans'
- url         - text      - source category page URL
- image_url   - text      - product image URL
- scraped_at  - timestamp - when the row was scraped (default now())
"""


def run_sql(sql: str) -> list[dict]:
    with pg_engine.connect() as conn:
        result = conn.execute(text(sql))
        return [dict(row._mapping) for row in result]


