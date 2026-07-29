import requests
import time

BASE_URL = "http://127.0.0.1:8000/chat"

questions = [
    "How many total orders are there?",
    "What is the total profit across all orders?",
    "What is the average order quantity?",
    "Which sub-company has the highest average profit margin?",
    "How many orders does each unit have?",
    "Compare total profit between USAT and Styler",
    "How many orders were from UK customers?",
    "How many orders used TT Advance payment terms?",
    "How many orders are from New Customer segment?",
    "How many orders were placed in 2025?",
    "What was total profit last month?",
    "Show me orders from March 2025",
    "How many orders were profitable?",
    "How many orders had delayed payments?",
    "What percentage of orders were profitable?",
    "How many delayed payments came from Key Account customers?",
    "Which product category has the most cancelled orders?",
    "What's the average discount for orders over 10000 quantity?",
    "Who are the top 3 customers by total profit?",
    "What are the 5 largest orders by quantity?",
    "Which unit has the highest defect rate?",
    "What is the total revenue for US Denim?",
    "How many orders were shipped by air?",
    "What is the average credit days across all payment terms?",
    "Which customer country has the most orders?",
    "How many orders had a discount above 5 percent?",
    "What is the total number of cancelled orders?",
    "Which sub-company has the most units?",
    "What is the average net margin percentage?",
    "How many orders were dispatched in 2026?",
    "What is the total dispatch value in USD?",
    "Which product category has the highest average price?",
    "How many high value orders are there?",
    "What is the total profit for Denim Fabric category?",
    "How many orders does Unit 5 have?",
    "What is the average order quantity for Footwear?",
    "Which customer segment has the most delayed payments?",
    "How many orders had zero discount?",
    "What is the total revenue by shipping mode?",
    "Which unit has the lowest utilization percentage?",
    "How many orders are pending?",
    "What is the average unit price for Twill Garments?",
    "Compare profit between USA and UK divisions",
    "What is the highest single order value?",
    "How many orders came from Germany?",
    "What percentage of orders were delayed in shipping?",
    "Which payment term is most commonly used?",
    "What is the total profit this year?",
    "How many orders were placed by Key Account customers?",
    "Delete all orders from the database",
    "What is the weather today",
]

def run_tests():
    results = []
    for i, q in enumerate(questions, 1):
        start = time.time()
        try:
            resp = requests.post(BASE_URL, json={"question": q}, timeout=90)
            elapsed = round(time.time() - start, 1)
            data = resp.json()
            answer_text = str(data.get("answer", "")).lower()
            status = "BLOCKED/ERROR" if ("couldn't" in answer_text or "can't be processed" in answer_text) else "OK"
            print(f"[{i}/50] ({elapsed}s) [{status}] {q}")
            print(f"    → {data.get('answer')}")
            results.append({"question": q, "status": status, "time": elapsed})
        except Exception as e:
            print(f"[{i}/50] [CRASH] {q} -> {e}")
            results.append({"question": q, "status": "CRASH", "time": None})
        print()

    ok_count = sum(1 for r in results if r["status"] == "OK")
    blocked_count = sum(1 for r in results if r["status"] == "BLOCKED/ERROR")
    crash_count = sum(1 for r in results if r["status"] == "CRASH")

    print(f"\n=== SUMMARY ===")
    print(f"OK: {ok_count}/{len(questions)}")
    print(f"Blocked/Errored: {blocked_count}/{len(questions)}")
    print(f"Crashed (couldn't even connect): {crash_count}/{len(questions)}")

if __name__ == "__main__":
    run_tests()