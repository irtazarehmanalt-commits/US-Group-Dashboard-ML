import base64
import json

import os
import tempfile
from pathlib import Path
from typing import Literal, Optional
import pandas as pd
import papermill as pm
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator
from chatbot.service import ask_chatbot
from blog import fetch_textile_news
# added: web-scraping (market data) support
from scraper.selenium_scraper import scrape_category, save_to_json, load_from_json
from scraper.scheduler import start_scheduler
from database import save_products
from audit import log_action, get_user_timeline
from user_warnings import (
    generate_warning_letter,
    create_warning,
    get_warnings_for_user,
    get_all_sent_warnings,
    send_warning_email,
    build_warning_pdf,
)
from auth.services import (
    start_signup,
    verify_otp_and_create_account,
    login as auth_login,
    google_login,
    verify_token,
    verify_user_password,
    approve_user,
    delete_user,
    GOOGLE_CLIENT_ID,
)


os.environ.setdefault("MPLBACKEND", "Agg")

#Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK_PATH = PROJECT_ROOT / "Finance_Prediction.ipynb"
DATASET_CSV_PATH = Path(__file__).resolve().parent / "data" / "US_Group_ML_Dataset_2025_2026_refined_2.csv"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

#Dropdown options
SUB_COMPANIES = ["USAT", "US Denim", "USDNF", "Styler"]
UNITS_BY_SUB_COMPANY = {
    "USAT": {
        "USA": ["Unit 2", "Unit 5"],
        "UK": ["Unit 1", "Unit 3", "Unit 4"],
    },
    "US Denim": ["Unit 6", "Unit 7"],
    "USDNF": ["Unit 8", "Unit 9"],
    "Styler": ["Unit 10"],
}
CUSTOMER_COUNTRIES = [
    "Bangladesh", "Germany", "Italy", "Netherlands", "Saudi Arabia",
    "Sri Lanka", "Turkey", "UAE", "UK", "USA",
]
CUSTOMER_SEGMENTS = ["Key Account", "Regular", "New Customer"]
ORDER_PRIORITIES = ["High", "Medium", "Low"]
PRODUCT_CATEGORIES = [
    "Denim Fabric", "Denim Garments", "Footwear",
    "Lifestyle Apparel", "Non-Denim Fabric", "Twill Garments",
]
UOM_OPTIONS = ["Meters", "Pairs", "Pieces"]
PAYMENT_TERMS = ["TT Advance", "TT 30 Days", "DA 60 Days", "LC 60 Days", "LC 90 Days", "Open Account 45 Days"]
SHIPPING_MODES = ["Sea", "Air"]


#Schemas
class OrderInput(BaseModel):
    Sub_Company: Literal["USAT", "US Denim", "USDNF", "Styler"]
    Division: Optional[Literal["USA", "UK"]] = None
    Unit: str
    Customer_Country: str
    Customer_Segment: Literal["Key Account", "Regular", "New Customer"]
    Order_Priority: Literal["High", "Medium", "Low"]
    Product_Category: str
    UOM: Literal["Meters", "Pairs", "Pieces"]
    Order_Quantity: float = Field(..., gt=0)
    Unit_Price_USD: float = Field(..., gt=0)
    Discount_Pct: float = Field(..., ge=0, le=10)
    Payment_Terms: str
    Shipping_Mode: Literal["Sea", "Air"]

    @model_validator(mode="after")
    def validate_division_consistency(self):
        if self.Sub_Company == "USAT" and self.Division is None:
            raise ValueError("Division is required when Sub_Company is 'USAT'")
        if self.Sub_Company != "USAT" and self.Division is not None:
            raise ValueError("Division must be omitted unless Sub_Company is 'USAT'")
        return self


class PredictionResponse(BaseModel):
    prediction: str
    is_positive: bool
    confidence: float = Field(..., ge=0, le=100)
    explanation: str
    key_factors: list[str]
    model_source: Literal["model"]


class HealthResponse(BaseModel):
    status: str
    dataset_found: bool
    notebook_found: bool


# Dashboard stats
def _load_dashboard_data():
    """Top 5 customers by profit, and a next-month profit trend.

    The notebook's own "next month profit" regressors (Linear Regression,
    Decision Tree, SVR, KNN, ANN) all scored a NEGATIVE R^2 on this dataset -
    every one of them predicts worse than just guessing the average, because
    there are only 16-18 monthly data points to train on. Rather than wire up
    a model that's confidently wrong, this uses the same 3-month rolling
    average that already outperformed all of them, labeled honestly as a
    trend estimate rather than a validated prediction.
    """
    from chatbot.db import pg_engine
    try:
        df = pd.read_sql("SELECT * FROM orders", pg_engine)
    except Exception:
        return None

    top_customers = (
        df.groupby("Customer_Name")["Net_Profit_USD"].sum().sort_values(ascending=False).head(5)
    )

    monthly = (
        df.groupby(["Year", "Month"])["Net_Profit_USD"]
        .sum()
        .reset_index(name="Total_Profit_USD")
        .sort_values(["Year", "Month"])
        .reset_index(drop=True)
    )

    last_year, last_month = int(monthly.iloc[-1]["Year"]), int(monthly.iloc[-1]["Month"])
    forecast_month, forecast_year = last_month + 1, last_year
    if forecast_month > 12:
        forecast_month, forecast_year = 1, forecast_year + 1

    recent = monthly.tail(3)

    return {
        "top_customers": [
            {"name": name, "total_profit_usd": round(float(value), 2)}
            for name, value in top_customers.items()
        ],
        "profit_trend": {
            "forecast_year": forecast_year,
            "forecast_month": forecast_month,
            "forecast_usd": round(float(recent["Total_Profit_USD"].mean()), 2),
            "basis_months": [
                {
                    "year": int(row.Year),
                    "month": int(row.Month),
                    "total_profit_usd": round(float(row.Total_Profit_USD), 2),
                }
                for row in recent.itertuples()
            ],
        },
    }


_DASHBOARD_DATA = _load_dashboard_data()


#Notebook execution
def run_notebook(order: OrderInput) -> dict:
    if not DATASET_CSV_PATH.exists():
        raise HTTPException(status_code=500, detail=f"Dataset not found at {DATASET_CSV_PATH}")
    if not NOTEBOOK_PATH.exists():
        raise HTTPException(status_code=500, detail=f"Notebook not found at {NOTEBOOK_PATH}")

    with tempfile.TemporaryDirectory(prefix="usgroup_pred_") as tmpdir:
        tmp = Path(tmpdir)
        input_path = tmp / "input.json"
        output_path = tmp / "output.json"
        executed_notebook_path = tmp / "executed.ipynb"

        input_path.write_text(json.dumps(order.model_dump()), encoding="utf-8")

        try:
            pm.execute_notebook(
                str(NOTEBOOK_PATH),
                str(executed_notebook_path),
                parameters={
                    "DATASET_CSV_PATH": str(DATASET_CSV_PATH),
                    "INPUT_JSON_PATH": str(input_path),
                    "OUTPUT_JSON_PATH": str(output_path),
                },
                progress_bar=False,
                execution_timeout=300,
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Notebook execution failed: {exc}") from exc

        if not output_path.exists():
            raise HTTPException(status_code=500, detail="Notebook ran but did not produce output.json")

        return json.loads(output_path.read_text(encoding="utf-8"))


#FastAPI app

app = FastAPI(title="US Group Analytics API", version="1.0.0")

def get_current_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    payload = verify_token(authorization.removeprefix("Bearer ").strip())
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# Same as get_current_user, but for endpoints that aren't gated behind login
# (chat/predict/etc. stay reachable without a token) - if a valid token IS
# present we still want to know who's asking, e.g. to attribute a chat
# question to the logged-in user. Returns None instead of raising on a
# missing/invalid token.
def get_current_user_optional(authorization: str = Header(None)) -> Optional[dict]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return verify_token(authorization.removeprefix("Bearer ").strip())

#chatbot


class ChatRequest(BaseModel):
    question: str
    history: Optional[list[dict]] = None  # recent [{role, content}] turns for follow-up context

@app.post("/chat")
def chat(req: ChatRequest, user: Optional[dict] = Depends(get_current_user_optional)):
    user_name = user.get("name") if user else None
    return ask_chatbot(req.question, user_name=user_name, history=req.history)


class ChartRequest(BaseModel):
    data: list[dict]

@app.post("/chat/chart")
def generate_chat_chart(req: ChartRequest):
    from chatbot.chart_generator import generate_chart
    image = generate_chart(req.data)
    if image is None:
        raise HTTPException(status_code=400, detail="Not enough data to build a chart.")
    return {"image_base64": image}




@app.get("/chat/history")
def get_chat_history():
    from chatbot.db import run_sql
    rows = run_sql('SELECT id, question, answer, user_name, created_at FROM chat_history ORDER BY created_at DESC LIMIT 50')
    return rows


@app.delete("/chat/history/{item_id}")
def delete_chat_history_item(item_id: int):
    from sqlalchemy import text
    from chatbot.db import pg_engine
    with pg_engine.connect() as conn:
        result = conn.execute(text("DELETE FROM chat_history WHERE id = :id"), {"id": item_id})
        conn.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="History item not found")
    return {"deleted": item_id}


from fastapi.responses import Response
from chatbot.report_builder import build_report_data
from chatbot.pdf_builder import build_pdf

@app.get("/report/generate")
def generate_report(user: Optional[dict] = Depends(get_current_user_optional)):
    sections = build_report_data()
    pdf_bytes = build_pdf(sections)

    if user:
        log_action(user.get("email"), user.get("name"), "generate_report", "Generated the standard PDF report")

    return {
        "sections": sections,
        "pdf_base64": base64.b64encode(pdf_bytes).decode('utf-8')
    }



from chatbot.custom_report import build_custom_report_pdf

class ReportItem(BaseModel):
    question: str
    answer: str
    chart_image_base64: str | None = None

class CustomReportRequest(BaseModel):
    items: list[ReportItem]

@app.post("/report/custom")
def generate_custom_report(req: CustomReportRequest, user: Optional[dict] = Depends(get_current_user_optional)):
    pdf_bytes = build_custom_report_pdf([item.model_dump() for item in req.items])
    if user:
        count = len(req.items)
        log_action(user.get("email"), user.get("name"), "custom_report",
                    f"Generated a custom PDF report ({count} item{'s' if count != 1 else ''})")
    return {"pdf_base64": base64.b64encode(pdf_bytes).decode('utf-8')}



@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        dataset_found=DATASET_CSV_PATH.exists(),
        notebook_found=NOTEBOOK_PATH.exists(),
    )

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class OTPVerifyRequest(BaseModel):
    email: str
    otp: str

class LoginRequest(BaseModel):
    email: str
    password: str

class VerifyPasswordRequest(BaseModel):
    email: str
    password: str

@app.post("/auth/signup")
def signup(req: SignupRequest):
    result = start_signup(req.name, req.email, req.password)
    if result["emailed"]:
        return {"message": "A verification code has been sent to your email.", "emailed": True}
    # Dev fallback: SMTP not configured, so return the code so signup still works
    # and the frontend can show it on screen.
    return {"message": "OTP generated (email not configured)", "emailed": False, "otp": result["otp"]}


@app.get("/auth/config")
def auth_config():
    """Public auth config for the login page (Google client id is not secret)."""
    return {"google_client_id": GOOGLE_CLIENT_ID}


class GoogleAuthRequest(BaseModel):
    credential: str

@app.post("/auth/google")
def google_auth(req: GoogleAuthRequest):
    try:
        result = google_login(req.credential)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=401, detail="Google sign-in failed or token was invalid.")
    if result.get("pending"):
        raise HTTPException(status_code=403, detail="Your account is waiting for admin approval.")
    return result

@app.post("/auth/verify-otp")
def verify_otp(req: OTPVerifyRequest):
    success = verify_otp_and_create_account(req.email, req.otp)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    return {"message": "Account created successfully"}

@app.post("/auth/login")
def login_route(req: LoginRequest):
    result = auth_login(req.email, req.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if result.get("pending"):
        raise HTTPException(status_code=403, detail="Your account is waiting for admin approval.")
    return result

@app.get("/auth/all-users")
def all_users_route(admin: dict = Depends(require_admin)):
    from chatbot.db import run_sql
    return run_sql('SELECT id, name, email, role, is_approved, created_at FROM users ORDER BY created_at DESC')

@app.get("/audit-log/{user_id}")
def audit_log_route(user_id: int, admin: dict = Depends(require_admin)):
    """Step-by-step activity trail for one user (logins, predictions, reports,
    scrapes, chat questions, admin actions) - admin only."""
    from sqlalchemy import text
    from chatbot.db import pg_engine
    with pg_engine.connect() as conn:
        target = conn.execute(
            text("SELECT name, email, role, is_approved, created_at FROM users WHERE id = :id"),
            {"id": user_id},
        ).mappings().first()
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": dict(target), "actions": get_user_timeline(target["email"], target["name"])}

# Warnings - admin picks flagged actions from a user's audit log, an LLM
# drafts a formal letter (admin can edit before sending), then it's saved
# (visible to that user on their own Warnings tab) and optionally emailed.

def _lookup_user(user_id: int) -> dict:
    from sqlalchemy import text
    from chatbot.db import pg_engine
    with pg_engine.connect() as conn:
        row = conn.execute(
            text("SELECT name, email FROM users WHERE id = :id"), {"id": user_id}
        ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)

class GenerateWarningRequest(BaseModel):
    user_id: int
    actions: list[dict]

@app.post("/warnings/generate")
def generate_warning_route(req: GenerateWarningRequest, admin: dict = Depends(require_admin)):
    if not req.actions:
        raise HTTPException(status_code=400, detail="Select at least one action to warn about.")
    target = _lookup_user(req.user_id)
    letter = generate_warning_letter(target["name"], admin.get("name"), req.actions)
    return {"letter": letter}

class SendWarningRequest(BaseModel):
    user_id: int
    letter: str
    send_email: bool = False
    actions: list[dict] = []

@app.post("/warnings/send")
def send_warning_route(req: SendWarningRequest, admin: dict = Depends(require_admin)):
    target = _lookup_user(req.user_id)
    emailed = False
    if req.send_email:
        try:
            emailed = send_warning_email(target["email"], req.letter)
        except Exception as exc:
            print(f"[warnings] email failed for {target['email']}: {exc}")
    warning_id = create_warning(target["email"], target["name"], req.letter, req.actions,
                                 admin.get("email"), admin.get("name"), emailed)
    log_action(admin.get("email"), admin.get("name"), "issue_warning",
               f"Issued a warning to {target['name']} ({target['email']})" + (" - emailed" if emailed else ""))
    return {"id": warning_id, "emailed": emailed}

@app.get("/warnings/mine")
def my_warnings_route(user: dict = Depends(get_current_user)):
    return get_warnings_for_user(user.get("email"))

@app.get("/warnings/sent")
def sent_warnings_route(admin: dict = Depends(require_admin)):
    """Every warning issued, across all recipients - the admin's own
    'Warnings Sent' view, since no one sends the admin a warning."""
    return get_all_sent_warnings()

class WarningPdfRequest(BaseModel):
    letter: str

@app.post("/warnings/pdf")
def warning_pdf_route(req: WarningPdfRequest, user: dict = Depends(get_current_user)):
    """Renders whatever letter text the caller already has on screen - an
    admin's in-progress draft, or a user's own already-saved warning - as a
    PDF. No extra ownership check needed: the input is text the caller can
    already read, not a lookup by id."""
    pdf_bytes = build_warning_pdf(req.letter)
    return {"pdf_base64": base64.b64encode(pdf_bytes).decode("utf-8")}

@app.post("/auth/verify-password")
def verify_password_route(req: VerifyPasswordRequest, admin: dict = Depends(require_admin)):
    if req.email != admin.get("email"):
        raise HTTPException(status_code=403, detail="Can only verify your own password")
    return {"verified": verify_user_password(req.email, req.password)}

@app.post("/auth/approve/{user_id}")
def approve_user_route(user_id: int, admin: dict = Depends(require_admin)):
    if not approve_user(user_id, admin.get("email"), admin.get("name")):
        raise HTTPException(status_code=404, detail="User not found")
    return {"approved": user_id}

@app.delete("/auth/users/{user_id}")
def delete_user_route(user_id: int, admin: dict = Depends(require_admin)):
    # Used for both "reject pending request" and "delete account".
    try:
        deleted = delete_user(user_id, admin.get("email"), admin.get("name"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"deleted": user_id}

@app.get("/options")
def options():
    """Dropdown option lists for the frontend forms."""
    return {
        "sub_companies": SUB_COMPANIES,
        "units_by_sub_company": UNITS_BY_SUB_COMPANY,
        "customer_countries": CUSTOMER_COUNTRIES,
        "customer_segments": CUSTOMER_SEGMENTS,
        "order_priorities": ORDER_PRIORITIES,
        "product_categories": PRODUCT_CATEGORIES,
        "uom_options": UOM_OPTIONS,
        "payment_terms": PAYMENT_TERMS,
        "shipping_modes": SHIPPING_MODES,
    }

@app.get("/dashboard-stats")
def dashboard_stats():
    if _DASHBOARD_DATA is None:
        raise HTTPException(status_code=500, detail="Dashboard insights unavailable - could not read the orders table.")
    return _DASHBOARD_DATA

@app.post("/predict/profitability", response_model=PredictionResponse)
def predict_profitability(order: OrderInput, user: Optional[dict] = Depends(get_current_user_optional)):
    result = run_notebook(order)["profitability"]
    response = PredictionResponse(**result, model_source="model")
    if user:
        log_action(user.get("email"), user.get("name"), "predict_profitability",
                    f"Predicted profitability: {response.prediction} ({response.confidence:.0f}% confidence)")
    return response

@app.post("/predict/payment-delay", response_model=PredictionResponse)
def predict_payment_delay(order: OrderInput, user: Optional[dict] = Depends(get_current_user_optional)):
    result = run_notebook(order)["payment_delay"]
    response = PredictionResponse(**result, model_source="model")
    if user:
        log_action(user.get("email"), user.get("name"), "predict_payment_delay",
                    f"Predicted payment delay: {response.prediction} ({response.confidence:.0f}% confidence)")
    return response

#Blog - live textile industry news

class NewsArticle(BaseModel):
    title: str
    description: str
    url: str
    image: Optional[str] = None
    source: str
    published_at: Optional[str] = None


@app.get("/blog/news", response_model=list[NewsArticle])
def blog_news():
    return fetch_textile_news()

# Market data - live web scraping of retail brand product/pricing
# ---------------------------------------------------------------------------
# Workflow: POST /market-data/scrape runs Selenium and stages the result in a
# JSON file (nothing hits the DB yet). POST /market-data/save then loads that
# JSON file into the scraped_products table. GET /market-data/ reads recent
# saved rows. The chatbot queries scraped_products directly via text-to-SQL.

class ScrapeRequest(BaseModel):
    url: str
    brand: str
    category: str = ""  # optional - not collected from the UI anymore


@app.post("/market-data/scrape")
def market_data_scrape(req: ScrapeRequest, user: Optional[dict] = Depends(get_current_user_optional)):
    """Scrape a category page and stage the rows in the JSON file for review."""
    try:
        products = scrape_category(req.url, req.brand, req.category)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scrape failed: {exc}") from exc
    save_to_json(products)
    if user:
        log_action(user.get("email"), user.get("name"), "scrape",
                    f"Scraped {req.brand} ({len(products)} products)")
    return {"count": len(products), "products": products}


@app.post("/market-data/save")
def market_data_save(user: Optional[dict] = Depends(get_current_user_optional)):
    """Load the currently-staged JSON scrape into the scraped_products table."""
    products = load_from_json()
    if not products:
        raise HTTPException(status_code=400, detail="Nothing to save - run a scrape first.")
    inserted = save_products(products)
    if user:
        log_action(user.get("email"), user.get("name"), "save_scrape",
                    f"Saved {inserted} scraped products to the database")
    return {"inserted": inserted}


@app.get("/market-data/")
def market_data_list(brand: Optional[str] = None, category: Optional[str] = None):
    """Recent saved scraped products, optionally filtered by brand/category."""
    clauses, params = [], {}
    if brand:
        clauses.append("brand = :brand")
        params["brand"] = brand
    if category:
        clauses.append("category = :category")
        params["category"] = category
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    # run_sql doesn't take params, so inline safely via a small parameterized query
    from sqlalchemy import text
    from chatbot.db import pg_engine
    with pg_engine.connect() as conn:
        rows = conn.execute(
            text(f"SELECT id, brand, name, price, category, url, image_url, "
                 f"fit_category, fit_sub_category, scraped_at "
                 f"FROM scraped_products {where} ORDER BY scraped_at DESC LIMIT 200"),
            params,
        )
        return [dict(r._mapping) for r in rows]


@app.post("/market-data/scrape-brands")
def market_data_scrape_brands(admin: dict = Depends(require_admin)):
    """Scrape every configured brand's Women's/Men's jeans page (see
    scraper/batch_scrape.py's BRAND_TARGETS), tag each product with a fit
    category via the taxonomy, save everything to scraped_products, and write
    one JSON file per brand into backend/scraper_data/. Admin-only and
    synchronous - this hits 6 real retail sites (12 pages) and can take
    several minutes, unlike the single-URL manual scrape above."""
    from scraper.batch_scrape import scrape_all_configured_brands
    summary = scrape_all_configured_brands()
    total_scraped = sum(b["scraped"] for b in summary.values())
    log_action(admin.get("email"), admin.get("name"), "scrape_brands",
               f"Batch-scraped {len(summary)} brands ({total_scraped} products)")
    return {"summary": summary}


# added: kick off the 6-hourly background scraper when the server starts
@app.on_event("startup")
def _start_background_scraper():
    start_scheduler()


app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
