# US Group ML UI — Project Context / Handoff Prompt

Paste this whole file into a new chat as the first message. It describes the project, the
architecture, every file, how to run it, and the current state of the work.

---

## Who I am and what this is

I'm an intern building an internal analytics dashboard for **US Group** (a Pakistani textile
/ apparel manufacturing group: denim fabric, denim garments, twill garments, footwear,
lifestyle apparel). The project is a full-stack ML web app that sits on top of an orders
dataset and does four things:

1. **Predicts whether a new order will be profitable** (classification)
2. **Predicts whether a customer will pay late** (classification)
3. **A natural-language chatbot** that answers business questions by generating SQL against
   a PostgreSQL copy of the orders table
4. **PDF report generation** — both a fixed standard report and a custom report built from
   pinned chat answers/charts

Project root: `D:\Internship\US_group_ML_UI` — **not** a git repository.
Platform: Windows 11, PowerShell / cmd. Python 3.13.5.

---

## Directory layout

```
D:\Internship\US_group_ML_UI\
├── Finance_Prediction.ipynb        # the ML notebook (107 cells) — EDA + training + serving
├── backend\
│   ├── main.py                     # FastAPI app — ALL routes live here (~394 lines)
│   ├── database.py                 # one-time DB setup script (CSV -> Postgres, tables, admin seed)
│   ├── list_models.py              # scratch script, lists Gemini models (leftover, not wired in)
│   ├── test_50_questions.py        # hits POST /chat with 50 business questions, for chatbot QA
│   ├── requirements.txt
│   ├── .env                        # DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME,
│   │                               #   GEMINI_API_KEY, OLAMA_API_KEY   (not committed)
│   ├── venv\                       # the virtualenv, already populated
│   ├── data\
│   │   └── US_Group_ML_Dataset_2025_2026_refined_2.csv   # 1,914 rows x 52 cols, ~1.6 MB
│   ├── auth\
│   │   └── services.py             # signup + OTP + login + JWT + admin approval
│   └── chatbot\
│       ├── db.py                   # SQLAlchemy engine + the big ORDERS_SCHEMA prompt text
│       ├── date_resolver.py        # rewrites "last month" etc. into real Year/Month from DB
│       ├── sql_generator.py        # LLM -> PostgreSQL SELECT (Ollama Cloud, gpt-oss:120b-cloud)
│       ├── safety.py               # keyword blocklist so only SELECTs run
│       ├── service.py              # orchestrates the whole chat flow + saves to chat_history
│       ├── answer_generator.py     # LLM -> one natural sentence from the rows (local llama3.1)
│       ├── chart_generator.py      # matplotlib (Agg) -> base64 PNG
│       ├── report_sections.py      # 4 fixed SQL-derived report sections
│       ├── report_builder.py       # assembles the standard report data
│       ├── pdf_builder.py          # reportlab -> standard PDF
│       └── custom_report.py        # reportlab -> user-built PDF from pinned chat items
└── frontend\
    ├── index.html                  # 38 lines — React 18 + Babel standalone via CDN, no build step
    ├── app.js                      # ~2060 lines — the ENTIRE React app in one file (JSX, in-browser Babel)
    ├── style.css                   # ~37 KB — hand-written plain CSS
    ├── logo-lion.png
    └── logo-wordmark.png
```

---

## Architecture / how it fits together

**One server, one port.** FastAPI serves both the JSON API and the static frontend —
`app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True))` is the last line of
`main.py`, so `http://127.0.0.1:8000` serves the UI and the API from the same origin. No
CORS setup, no separate frontend dev server.

**No build step anywhere.** `index.html` loads React 18, ReactDOM, `@babel/standalone`, and
three.js from unpkg CDNs, then `fetch`es `app.js` with `cache: 'no-store'`, transpiles the
JSX in the browser, and injects it. `style.css` is loaded with a `?t=Date.now()` cache-buster.
This is deliberate — no npm, no bundler, no node_modules.

**Two separate data paths for the same dataset:**
- **Predictions** read the CSV directly (via papermill running the notebook).
- **Chatbot / reports** read a PostgreSQL `orders` table that `database.py` loaded from the
  same CSV.
These two are not kept in sync automatically — re-run `python database.py` if the CSV changes.

### Prediction flow (the unusual part)

There is **no pickled model**. `/predict/profitability` and `/predict/payment-delay` both
call `run_notebook()` in `main.py`, which:
1. writes the order to a temp `input.json`
2. runs the *entire* `Finance_Prediction.ipynb` with **papermill**, injecting
   `DATASET_CSV_PATH`, `INPUT_JSON_PATH`, `OUTPUT_JSON_PATH` as parameters
3. the notebook's last cell trains on the CSV, predicts the single order, and writes
   `output.json` with both a `profitability` and a `payment_delay` result
4. FastAPI reads that JSON back and returns it

So **every prediction request re-runs the whole notebook and re-trains the models — about
30 seconds per request.** That's expected behaviour, not a hang. Both endpoints call the
same notebook run and each just picks its half of the output.

The response shape (`PredictionResponse`) is: `prediction` (string), `is_positive` (bool),
`confidence` (0–100), `explanation` (string), `key_factors` (list of strings),
`model_source` (always `"model"`).

### Chatbot flow

`POST /chat` → `ask_chatbot()` in `chatbot/service.py`:
1. `resolve_relative_dates()` — queries the DB for the true latest Year/Month and appends a
   literal note to the question, so the LLM never has to guess what "last month" means
2. `generate_sql()` — Ollama **Cloud** (`https://ollama.com`, model `gpt-oss:120b-cloud`,
   auth via `OLAMA_API_KEY`), system prompt = the ~140-line `ORDERS_SCHEMA` in `chatbot/db.py`
3. `is_safe_sql()` — rejects anything containing DROP/DELETE/UPDATE/INSERT/ALTER/CREATE/TRUNCATE
4. `run_sql()` — executes against Postgres
5. `generate_natural_answer()` — **local** Ollama (`llama3.1`) turns the rows into one sentence
6. saves question/answer/user_name into `chat_history`
7. returns `{answer, sql, data, can_chart}` — `can_chart` is true when there are ≥2 rows and a
   numeric column after the first

Note the split: SQL generation uses **cloud** Ollama, answer generation uses a **local** Ollama
daemon. Both must be reachable or `/chat` fails.

`ORDERS_SCHEMA` in `chatbot/db.py` is the most important prompt-engineering artifact in the
project — it documents all 52 columns with types and valid values, and hard-codes rules like
"column names are case-sensitive and must be double-quoted", "the boolean flags are INTEGER
0/1 not real booleans", "`_Pct` columns are already percentages, don't ×100", and the exact
CTE pattern to use for "last month".

### Auth flow

`auth/services.py`, backed by the Postgres `users` table:
- **Signup** → generates a 6-digit OTP, held in an **in-memory dict** (`pending_otps`), and
  returns it in the API response so it can be shown on screen (no email sending yet). Lost on
  server restart.
- **Verify OTP** → inserts the user with `is_approved = FALSE`
- **Login** → plaintext password comparison, returns 403 "waiting for admin approval" if not
  approved, otherwise issues a **JWT** (python-jose, HS256, 24 h)
- **Admin** endpoints (`/auth/all-users`, `/auth/approve/{id}`, `/auth/verify-password`) are
  gated by a `require_admin` dependency that checks `role == "admin"` in the token
- Seeded admin from `database.py`: **email `admin`, password `admin123`**

Known-and-accepted-for-now shortcuts: **passwords are stored and compared in plaintext**, the
JWT `SECRET_KEY` is a hard-coded placeholder in `auth/services.py`, and OTPs live in memory.
The predict/chat/report endpoints are intentionally **not** gated behind login — only the
admin routes require a token. `get_current_user_optional` exists so `/chat` can attribute a
question to a logged-in user without requiring one.

---

## API endpoints (all in `backend/main.py`)

| Method | Path | Notes |
|---|---|---|
| GET | `/health` | reports whether dataset + notebook were found |
| GET | `/options` | all dropdown lists for the forms |
| GET | `/dashboard-stats` | top 5 customers by profit + next-month profit trend |
| POST | `/predict/profitability` | ~30 s, runs the notebook |
| POST | `/predict/payment-delay` | ~30 s, runs the notebook |
| POST | `/chat` | the NL→SQL chatbot |
| POST | `/chat/chart` | rows → base64 PNG chart |
| GET | `/chat/history` | last 50 |
| DELETE | `/chat/history/{id}` | |
| GET | `/report/generate` | standard report: sections JSON + base64 PDF |
| POST | `/report/custom` | PDF from pinned chat items |
| POST | `/auth/signup` | returns the OTP in the response body |
| POST | `/auth/verify-otp` | |
| POST | `/auth/login` | returns JWT |
| GET | `/auth/all-users` | admin only |
| POST | `/auth/verify-password` | admin only, own password only |
| POST | `/auth/approve/{user_id}` | admin only |
| — | `/` | static frontend mount (must stay last) |

### Order input schema (`OrderInput`)

`Sub_Company` (USAT / US Denim / USDNF / Styler), `Division` (USA / UK — **required iff
Sub_Company is USAT, must be omitted otherwise**, enforced by a pydantic `model_validator`),
`Unit`, `Customer_Country`, `Customer_Segment`, `Order_Priority`, `Product_Category`, `UOM`,
`Order_Quantity` (>0), `Unit_Price_USD` (>0), `Discount_Pct` (0–10), `Payment_Terms`,
`Shipping_Mode`.

Unit mapping: USAT/USA → Unit 2, 5 · USAT/UK → Unit 1, 3, 4 · US Denim → Unit 6, 7 ·
USDNF → Unit 8, 9 · Styler → Unit 10.

---

## The notebook — `Finance_Prediction.ipynb`

107 cells. Cell 0 is the papermill parameters cell. Structure:

- **EDA** — shape, nulls, class balance, order-status/sub-company countplots, correlation
  heatmap, net-margin boxplots
- **Preprocessing** — dates to datetime, `Division` NaN → `'Not Applicable'` (only USAT has
  divisions), one-hot encoding, train/test split, StandardScaler
- **Task A — profitability classification**: Dummy baseline, Decision Tree (pruned to
  `max_depth=5, min_samples_leaf=10` after it overfit), Naive Bayes, KNN, SVM, ANN (MLP
  32/16), then a comparison table + bar chart
- **Task B — payment-delay classification**: filtered to `Order_Status in ('Dispatched',
  'Delayed')`, same five models, SVM uses `class_weight='balanced'`; compared on **recall
  for class 1** as well as accuracy, because late payments are the minority class
- **Task C — next-month profit regression**: monthly aggregation with
  `Previous_Month_Profit` and `Rolling_3Month_Avg` features, Linear Regression / Decision
  Tree / SVR / KNN / ANN
- **Top-5-customer analysis** for USAT/USA
- **Final cell (105–106)** — the serving cell added for the FastAPI integration: reads
  `INPUT_JSON_PATH`, predicts profitability with **SVM** and payment delay with **Naive
  Bayes**, and writes `OUTPUT_JSON_PATH`

**Important finding already baked into the code:** every Task C regressor scored a *negative*
R² — there are only 16–18 monthly data points, so all of them predict worse than guessing the
mean. Rather than ship a confidently-wrong model, `/dashboard-stats` in `main.py` uses the
plain **3-month rolling average** (which beat all of them) and the UI labels it a "trend
estimate", not a prediction. This is a deliberate decision, documented in the docstring of
`_load_dashboard_data()` — please don't "fix" it by wiring a regressor back in.

---

## Frontend — `frontend/app.js` (single file, ~2060 lines)

Plain React (no router, no state library) with a `page` string in `App()` state. Sections,
in file order:

- **Icons** — inline SVG `Icon` component
- **Auth storage** — `getStoredAuth` / `setStoredAuth` / `clearStoredAuth` / `decodeJwtPayload`
  (localStorage)
- **API layer** — `apiRequest` (attaches `Bearer` token) and `publicApiRequest`, plus one thin
  wrapper per endpoint; `base64ToBlob` + `downloadCustomReportPdf` for PDF downloads
- **Helpers** — `formatCurrency`, `getUnitOptions` (cascading Sub_Company → Division → Unit),
  `validateForm`, `buildPayload`
- **Login/Signup** — `LoginWatermark` (a three.js animation), `LoginShell`, `LoginSignupPage`
  (handles the signup → on-screen OTP → verify → login flow)
- **Shell + shared UI** — `Sidebar` (role-aware, hides Admin for non-admins), `KpiCard`,
  `ConfidenceRing`, `ResultCard`, `OrderForm`
- **Dashboard** — `TopCustomersCard`, `ProfitTrendCard`, `PrintReportPanel`, `PinnedChartCard`,
  `DashboardPage`
- **Predictors** — one `PredictorPage` component reused for both profitability and payment
  delay, parameterised by title/subtitle/`predictFn`/`negativeTone`
- **Admin** — `AdminPage` (user list, approve, password re-verification)
- **Chatbot** — `useChatbot` hook, `ChatBubbleMenu`, `ChatMessage`, `ChatDashboardPinButton`,
  `ChatSaveAsPdfButton`, `ChatHistoryItemMenu`, `ChatHistoryView`, `ChatWidget` (floating,
  rendered at App level so it's on every page), `ChatPage` (full-page version)
- **`App()`** — auth gate → `LoginSignupPage` if logged out; otherwise sidebar + one of
  `dashboard` / `profitability` / `payment-delay` / `chat` / `admin`, plus pinned-chart state
  (`addPinnedChart` / `removePinnedChart`) so chat charts can be pinned onto the dashboard and
  exported into a custom PDF

---

## How to run it

Everything is already installed inside `backend\venv`.

```cmd
cd D:\Internship\US_group_ML_UI\backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

PowerShell uses `.\venv\Scripts\Activate.ps1` instead. Without activating:
`venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000`.

Then open **http://127.0.0.1:8000**. Must be launched from `backend\` — `main:app` and the
`chatbot` / `auth` package imports resolve relative to that directory.

**Prerequisites for full functionality:**
- PostgreSQL running with the credentials in `backend\.env`
- One-time DB setup: `python database.py` (loads the CSV into `orders`, creates
  `chat_history` + `users`, seeds admin/admin123)
- A **local Ollama** daemon with `llama3.1` pulled — needed for the chatbot's answer sentence
- `OLAMA_API_KEY` in `.env` for Ollama Cloud — needed for SQL generation
- Predictions and the dashboard work without Postgres/Ollama; chat and reports do not

**Testing the chatbot:** `python test_50_questions.py` (server must already be running).

---

## Things to be aware of when working on this

- `requirements.txt` is **incomplete** — `ollama`, `reportlab`, `sqlalchemy`, `psycopg2`,
  `python-dotenv`, and `google-genai` are installed in the venv but not listed. Worth fixing.
- `list_models.py` and `GEMINI_API_KEY` are leftovers from evaluating Gemini; nothing in the
  running app uses Gemini today.
- `.env` is secret — never print or commit its values.
- `app.mount("/")` must stay the **last** line of `main.py`, or it will swallow the API routes.
- Several imports in `main.py` are done mid-file / inside functions (report builders, `run_sql`)
  — that's existing style, not an accident.
- `Finance_Prediction.ipynb` cell 2 still has the Colab `files.upload()` block, wrapped in a
  `try/ImportError` so it's a no-op outside Colab.

## My working preferences

- **Plain hand-written HTML/CSS — no Tailwind, no CSS frameworks.**
- **Minimal file count, one file per concern. No npm, no build step, no bundler.** If
  something can be added to `app.js` / `style.css` / `main.py` rather than creating a new file,
  do that.
- Match the existing code style and comment density (comments in this codebase explain *why*,
  especially where a decision looks odd).
