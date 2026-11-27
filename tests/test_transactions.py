"""Create, read, update, delete and validation tests for expenses and income."""

import pytest


def expense(category="Groceries", amount=500, date="2026-11-10"):
    return {"category": category, "amount": amount, "date": date}


def income(source="Salary", amount=45000, date="2026-11-01"):
    return {"source": source, "amount": amount, "date": date}


# ----------------------------------------------------------------
# Expenses: create, read, update, delete
# ----------------------------------------------------------------

def test_create_and_list_expense(client, alice):
    created = client.post("/expenses", json=expense(), headers=alice)

    assert created.status_code == 200
    assert created.json()["category"] == "Groceries"
    assert created.json()["amount"] == 500

    listed = client.get("/expenses", headers=alice)

    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["id"] == created.json()["id"]


def test_filter_expenses_by_date(client, alice):
    client.post("/expenses", json=expense(date="2026-11-10"), headers=alice)
    client.post("/expenses", json=expense(date="2026-11-12"), headers=alice)

    response = client.get("/expenses?date=2026-11-10", headers=alice)

    assert len(response.json()) == 1
    assert response.json()[0]["date"] == "2026-11-10"


def test_update_expense(client, alice):
    created = client.post("/expenses", json=expense(), headers=alice).json()

    response = client.put(
        f"/expenses/{created['id']}",
        json=expense(category="Rent", amount=12000),
        headers=alice,
    )

    assert response.status_code == 200
    assert response.json()["category"] == "Rent"
    assert response.json()["amount"] == 12000


def test_delete_expense(client, alice):
    created = client.post("/expenses", json=expense(), headers=alice).json()

    response = client.delete(f"/expenses/{created['id']}", headers=alice)

    assert response.status_code == 200
    assert client.get("/expenses", headers=alice).json() == []


def test_update_missing_expense_returns_404(client, alice):
    response = client.put("/expenses/9999", json=expense(), headers=alice)

    assert response.status_code == 404


def test_delete_missing_expense_returns_404(client, alice):
    response = client.delete("/expenses/9999", headers=alice)

    assert response.status_code == 404


# ----------------------------------------------------------------
# Income: create, read, update, delete
# ----------------------------------------------------------------

def test_create_and_list_income(client, alice):
    created = client.post("/income", json=income(), headers=alice)

    assert created.status_code == 200
    assert created.json()["source"] == "Salary"

    listed = client.get("/income", headers=alice)

    assert len(listed.json()) == 1


def test_update_income(client, alice):
    created = client.post("/income", json=income(), headers=alice).json()

    response = client.put(
        f"/income/{created['id']}",
        json=income(source="Bonus", amount=5000),
        headers=alice,
    )

    assert response.status_code == 200
    assert response.json()["source"] == "Bonus"
    assert response.json()["amount"] == 5000


def test_delete_income(client, alice):
    created = client.post("/income", json=income(), headers=alice).json()

    response = client.delete(f"/income/{created['id']}", headers=alice)

    assert response.status_code == 200
    assert client.get("/income", headers=alice).json() == []


def test_update_missing_income_returns_404(client, alice):
    response = client.put("/income/9999", json=income(), headers=alice)

    assert response.status_code == 404


def test_delete_missing_income_returns_404(client, alice):
    response = client.delete("/income/9999", headers=alice)

    assert response.status_code == 404


# ----------------------------------------------------------------
# Validation: bad input must be rejected, not saved
# ----------------------------------------------------------------

@pytest.mark.parametrize("bad_amount", [0, -1, -50.5])
def test_expense_rejects_non_positive_amount(client, alice, bad_amount):
    response = client.post(
        "/expenses", json=expense(amount=bad_amount), headers=alice
    )

    assert response.status_code == 422


@pytest.mark.parametrize("bad_category", ["", " ", "     "])
def test_expense_rejects_blank_category(client, alice, bad_category):
    response = client.post(
        "/expenses", json=expense(category=bad_category), headers=alice
    )

    assert response.status_code == 422


@pytest.mark.parametrize("bad_date", ["not-a-date", "2026-13-26", "2026-02-31"])
def test_expense_rejects_invalid_date(client, alice, bad_date):
    response = client.post(
        "/expenses", json=expense(date=bad_date), headers=alice
    )

    assert response.status_code == 422


@pytest.mark.parametrize("bad_amount", [0, -1])
def test_income_rejects_non_positive_amount(client, alice, bad_amount):
    response = client.post(
        "/income", json=income(amount=bad_amount), headers=alice
    )

    assert response.status_code == 422


@pytest.mark.parametrize("bad_source", ["", "   "])
def test_income_rejects_blank_source(client, alice, bad_source):
    response = client.post(
        "/income", json=income(source=bad_source), headers=alice
    )

    assert response.status_code == 422


def test_text_is_trimmed_before_saving(client, alice):
    response = client.post(
        "/expenses", json=expense(category="  Rent  "), headers=alice
    )

    assert response.status_code == 200
    assert response.json()["category"] == "Rent"


def test_rejected_entries_are_not_saved(client, alice):
    client.post("/expenses", json=expense(amount=-5), headers=alice)
    client.post("/expenses", json=expense(category=" "), headers=alice)

    assert client.get("/expenses", headers=alice).json() == []
