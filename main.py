from jose import jwt
from datetime import date
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import Date, Float, Integer, String, create_engine, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from passlib.context import CryptContext



# ============================================================
# DATABASE CONFIGURATION
# ============================================================

load_dotenv()

print("DATABASE_URL loaded:", bool(os.getenv("DATABASE_URL")))

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# DATABASE MODELS
# ============================================================

class Base(DeclarativeBase):
    pass


class ExpenseDB(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String)
    amount: Mapped[float] = mapped_column(Float)
    date: Mapped[date] = mapped_column(Date)
    user_id: Mapped[int] = mapped_column(Integer)


class IncomeDB(Base):
    __tablename__ = "income"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String)
    amount: Mapped[float] = mapped_column(Float)
    date: Mapped[date] = mapped_column(Date)
    user_id: Mapped[int] = mapped_column(Integer)

class UserDB(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    password_hash: Mapped[str] = mapped_column(String)


Base.metadata.create_all(engine)


# ============================================================
# DATABASE CONNECTION TEST
# ============================================================

with engine.connect() as connection:
    result = connection.execute(text("SELECT 1"))
    print("Database connection successful:", result.scalar())


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

def create_access_token(username: str):
    payload = {
        "sub": username
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token

def verify_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")

        if username is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        return username

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    username = verify_access_token(token)

    return username


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================

class Expense(BaseModel):
    category: str = Field(min_length=1)
    amount: float = Field(gt=0)
    date: date


class ExpenseResponse(BaseModel):
    id: int
    category: str
    amount: float
    date: date


class Income(BaseModel):
    source: str = Field(min_length=1)
    amount: float = Field(gt=0)
    date: date


class IncomeResponse(BaseModel):
    id: int
    source: str
    amount: float
    date: date

class UserCreate(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str

class DeleteResponse(BaseModel):
    message: str


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {"message": "Family Finance API is running!"}


# ============================================================
# AUTHENTICATION
# ============================================================

# REGISTER
@app.post("/register")
def register_user(
    user: UserCreate,
    db=Depends(get_db)
):
    existing_user = db.query(UserDB).filter(
        UserDB.username == user.username
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    password_hash = pwd_context.hash(user.password)

    db_user = UserDB(
        username=user.username,
        password_hash=password_hash
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {
        "message": "User registered successfully",
        "username": db_user.username
    }

@app.post("/login")
def login_user(
    user: UserLogin,
    db=Depends(get_db)
):
    existing_user = db.query(UserDB).filter(
        UserDB.username == user.username
    ).first()

    if existing_user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    password_correct = pwd_context.verify(
        user.password,
        existing_user.password_hash
    )

    if not password_correct:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    access_token = create_access_token(
        existing_user.username
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# ============================================================
# EXPENSES
# ============================================================

# GET ALL EXPENSES
@app.get("/expenses", response_model=list[ExpenseResponse])
def get_expenses(
    date: date | None = None,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    user = db.query(UserDB).filter(
        UserDB.username == current_user
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    query = db.query(ExpenseDB).filter(
        ExpenseDB.user_id == user.id
    )

    if date:
        query = query.filter(
            ExpenseDB.date == date
        )

    return query.all()


# GET EXPENSE SUMMARY
@app.get("/expenses/summary")
def get_summary(
    date: date | None = None,
    db=Depends(get_db)
):
    query = db.query(
        ExpenseDB.category,
        func.sum(ExpenseDB.amount)
    )

    if date:
        query = query.filter(ExpenseDB.date == date)

    results = query.group_by(
        ExpenseDB.category
    ).order_by(
        func.sum(ExpenseDB.amount).desc()
    ).all()

    return [
        {
            "category": category,
            "total": total
        }
        for category, total in results
    ]


# GET TOTAL EXPENSES
@app.get("/expenses/total")
def get_total(
    date: date | None = None,
    db=Depends(get_db)
):
    query = db.query(ExpenseDB)

    if date:
        query = query.filter(ExpenseDB.date == date)

    total = query.with_entities(
        func.sum(ExpenseDB.amount)
    ).scalar() or 0

    return {"total": total}


# CREATE EXPENSE
@app.post("/expenses", response_model=ExpenseResponse)
def create_expense(
    expense: Expense,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    user = db.query(UserDB).filter(
        UserDB.username == current_user
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    db_expense = ExpenseDB(
        category=expense.category,
        amount=expense.amount,
        date=expense.date,
        user_id=user.id
    )

    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)

    return db_expense


# UPDATE EXPENSE
@app.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense: Expense,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    user = db.query(UserDB).filter(
        UserDB.username == current_user
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    db_expense = db.query(ExpenseDB).filter(
        ExpenseDB.id == expense_id,
        ExpenseDB.user_id == user.id
    ).first()

    if db_expense is None:
        raise HTTPException(
            status_code=404,
            detail="Expense not found"
        )

    db_expense.category = expense.category
    db_expense.amount = expense.amount
    db_expense.date = expense.date

    db.commit()
    db.refresh(db_expense)

    return db_expense


# DELETE EXPENSE
@app.delete("/expenses/{expense_id}", response_model=DeleteResponse)
def delete_expense(
    expense_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    user = db.query(UserDB).filter(
        UserDB.username == current_user
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    db_expense = db.query(ExpenseDB).filter(
        ExpenseDB.id == expense_id,
        ExpenseDB.user_id == user.id
    ).first()

    if db_expense is None:
        raise HTTPException(
            status_code=404,
            detail="Expense not found"
        )

    db.delete(db_expense)
    db.commit()

    return {
        "message": "Expense deleted successfully"
    }


# ============================================================
# INCOME
# ============================================================

# GET INCOME
@app.get("/income", response_model=list[IncomeResponse])
def get_income(
    date: date | None = None,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    user = db.query(UserDB).filter(
        UserDB.username == current_user
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    query = db.query(IncomeDB).filter(
        IncomeDB.user_id == user.id
    )

    if date:
        query = query.filter(
            IncomeDB.date == date
        )

    return query.all()


# GET TOTAL INCOME
@app.get("/income/total")
def get_total_income(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    user = db.query(UserDB).filter(
        UserDB.username == current_user
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    total = db.query(
        func.sum(IncomeDB.amount)
    ).filter(
        IncomeDB.user_id == user.id
    ).scalar()

    return {
        "total_income": total or 0
    }


# CREATE INCOME
@app.post("/income", response_model=IncomeResponse)
def create_income(
    income: Income,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    user = db.query(UserDB).filter(
        UserDB.username == current_user
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    db_income = IncomeDB(
        source=income.source,
        amount=income.amount,
        date=income.date,
        user_id=user.id
    )

    db.add(db_income)
    db.commit()
    db.refresh(db_income)

    return db_income


# UPDATE INCOME
@app.put("/income/{income_id}", response_model=IncomeResponse)
def update_income(
    income_id: int,
    income: Income,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    user = db.query(UserDB).filter(
        UserDB.username == current_user
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    db_income = db.query(IncomeDB).filter(
        IncomeDB.id == income_id,
        IncomeDB.user_id == user.id
    ).first()

    if db_income is None:
        raise HTTPException(
            status_code=404,
            detail="Income not found"
        )

    db_income.source = income.source
    db_income.amount = income.amount
    db_income.date = income.date

    db.commit()
    db.refresh(db_income)

    return db_income


# DELETE INCOME
@app.delete("/income/{income_id}", response_model=DeleteResponse)
def delete_income(
    income_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    user = db.query(UserDB).filter(
        UserDB.username == current_user
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    db_income = db.query(IncomeDB).filter(
        IncomeDB.id == income_id,
        IncomeDB.user_id == user.id
    ).first()

    if db_income is None:
        raise HTTPException(
            status_code=404,
            detail="Income not found"
        )

    db.delete(db_income)
    db.commit()

    return {
        "message": "Income deleted successfully"
    }


# ============================================================
# FINANCIAL REPORTS
# ============================================================

# GET BALANCE
@app.get("/balance")
def get_balance(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    user = db.query(UserDB).filter(
        UserDB.username == current_user
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    total_income = db.query(
        func.sum(IncomeDB.amount)
    ).filter(
        IncomeDB.user_id == user.id
    ).scalar() or 0

    total_expenses = db.query(
        func.sum(ExpenseDB.amount)
    ).filter(
        ExpenseDB.user_id == user.id
    ).scalar() or 0

    balance = total_income - total_expenses

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": balance
    }

# MONTHLY SUMMARY
@app.get("/monthly-summary")
def monthly_summary(
    year: int,
    month: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    user = db.query(UserDB).filter(
        UserDB.username == current_user
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    monthly_income = db.query(
        func.sum(IncomeDB.amount)
    ).filter(
        IncomeDB.user_id == user.id,
        func.extract("year", IncomeDB.date) == year,
        func.extract("month", IncomeDB.date) == month
    ).scalar() or 0

    monthly_expenses = db.query(
        func.sum(ExpenseDB.amount)
    ).filter(
        ExpenseDB.user_id == user.id,
        func.extract("year", ExpenseDB.date) == year,
        func.extract("month", ExpenseDB.date) == month
    ).scalar() or 0

    return {
        "year": year,
        "month": month,
        "income": monthly_income,
        "expenses": monthly_expenses,
        "balance": monthly_income - monthly_expenses
    }