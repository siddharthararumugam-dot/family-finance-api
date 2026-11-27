# Family Finance Management System

A full-stack web app for tracking household income and expenses. Users register, log in, record income and expenses, and see their balance and monthly summary on a dashboard.

Built as a portfolio project with **FastAPI**, **PostgreSQL** and **React**.

## Screenshots

| Dashboard | Login |
|---|---|
| ![Dashboard](screenshots/dashboard.png) | ![Login](screenshots/login.png) |

| Register | API docs (Swagger) |
|---|---|
| ![Register](screenshots/register.png) | ![API docs](screenshots/api-docs.png) |

## Features

**Web app (React)**
- Register and log in with username and password
- Add income and expenses with date, amount and category or source
- Delete transactions
- Dashboard with total balance, total income and total expenses
- Recent transactions list
- Monthly overview with an income vs expenses bar

**API (FastAPI)**
- User registration and login with JWT authentication
- Full create, read, update and delete for income and expenses
- Balance, totals, category summary and monthly summary endpoints
- Input validation (positive amounts, valid dates, non-empty text)
- Each user can only see and change their own data
- 57 automated tests (pytest) covering authentication, validation, CRUD, reports and per-user data isolation

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy |
| Database | PostgreSQL |
| Authentication | JWT (python-jose), bcrypt password hashing (passlib) |
| Frontend | React, Vite |

## API endpoints

All endpoints except `/`, `/register` and `/login` need a login token (`Authorization: Bearer <token>`).

| Method | Endpoint | What it does |
|---|---|---|
| POST | `/register` | Create an account |
| POST | `/login` | Log in and get a token |
| GET, POST | `/income` | List or add income |
| PUT, DELETE | `/income/{id}` | Edit or delete an income entry |
| GET | `/income/total` | Total income |
| GET, POST | `/expenses` | List or add expenses |
| PUT, DELETE | `/expenses/{id}` | Edit or delete an expense |
| GET | `/expenses/total` | Total expenses |
| GET | `/expenses/summary` | Expenses grouped by category |
| GET | `/balance` | Income, expenses and balance |
| GET | `/monthly-summary?year=&month=` | Income, expenses and balance for a month |

When the backend is running, interactive API docs are at `http://127.0.0.1:8000/docs`.

## Getting started

### Requirements
- Python 3.10 or newer
- Node.js (LTS) and npm
- PostgreSQL

### 1. Clone the project
```bash
git clone https://github.com/siddharthararumugam-dot/family-finance-api.git
cd family-finance-api
```

### 2. Set up the database
Create an empty PostgreSQL database (for example `family_finance`). The tables are created automatically when the backend starts.

### 3. Set up the backend
```bash
python -m venv venv

# Windows (Git Bash)
source venv/Scripts/activate
# Windows (PowerShell): venv\Scripts\Activate.ps1
# macOS / Linux: source venv/bin/activate

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your own values:
```
DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/family_finance
SECRET_KEY=a-long-random-secret-string
```

Start the backend:
```bash
uvicorn main:app --reload
```
The API runs at `http://127.0.0.1:8000`.

### 4. Set up the frontend
Open a second terminal:
```bash
cd frontend
npm install
npm run dev
```
Open the link shown in the terminal (usually `http://localhost:5173`).

## Running the tests

The tests use a temporary SQLite database, so they never touch your real data.

```bash
pip install -r requirements-dev.txt
pytest
```

| Test file | What it checks |
|---|---|
| `tests/test_auth.py` | Registration, login, password hashing, protected routes |
| `tests/test_transactions.py` | Create, read, update and delete for income and expenses, plus input validation |
| `tests/test_reports.py` | Balance, totals, category summary and monthly summary |
| `tests/test_data_isolation.py` | One user can never read, change or delete another user's data |

## Project structure

```
family-finance-api/
├── main.py              # FastAPI app: models, schemas and endpoints
├── requirements.txt     # Python dependencies
├── requirements-dev.txt # Adds pytest for running tests
├── pytest.ini           # Test configuration
├── tests/               # Automated API tests
├── screenshots/         # Images used in this README
├── .env.example         # Example environment settings
└── frontend/            # React + Vite app
    └── src/
        ├── App.jsx      # Login, register and dashboard
        └── App.css      # Styles
```

## Security notes
- Passwords are hashed with bcrypt and never stored as plain text.
- Secrets live in a `.env` file that is not uploaded to GitHub.
- Every income and expense row belongs to a user, and every query filters by the logged-in user.

## Planned improvements
- Edit transactions, search, filters and pagination on the website
- Monthly budgets per category with warnings
- Spending-by-category charts
- Households with several family members sharing finances
- Recurring bills and transactions
- CSV export
- Deployment with a live demo

## Author
Siddharthar A — [GitHub](https://github.com/siddharthararumugam-dot) · [LinkedIn](https://linkedin.com/in/siddharthar-arumugam-02b083241)
