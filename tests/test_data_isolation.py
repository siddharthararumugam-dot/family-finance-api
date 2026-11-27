"""One user must never see or change another user's data."""


def seed_alice(client, alice):
    expense = client.post(
        "/expenses",
        json={"category": "Rent", "amount": 12000, "date": "2026-11-02"},
        headers=alice,
    ).json()

    income = client.post(
        "/income",
        json={"source": "Salary", "amount": 45000, "date": "2026-11-01"},
        headers=alice,
    ).json()

    return expense, income


def test_other_user_sees_empty_lists(client, alice, bob):
    seed_alice(client, alice)

    assert client.get("/expenses", headers=bob).json() == []
    assert client.get("/income", headers=bob).json() == []


def test_other_user_cannot_update_expense(client, alice, bob):
    expense, _ = seed_alice(client, alice)

    response = client.put(
        f"/expenses/{expense['id']}",
        json={"category": "Hacked", "amount": 1, "date": "2026-11-02"},
        headers=bob,
    )

    assert response.status_code == 404

    original = client.get("/expenses", headers=alice).json()[0]

    assert original["category"] == "Rent"
    assert original["amount"] == 12000


def test_other_user_cannot_delete_expense(client, alice, bob):
    expense, _ = seed_alice(client, alice)

    response = client.delete(f"/expenses/{expense['id']}", headers=bob)

    assert response.status_code == 404
    assert len(client.get("/expenses", headers=alice).json()) == 1


def test_other_user_cannot_update_income(client, alice, bob):
    _, income = seed_alice(client, alice)

    response = client.put(
        f"/income/{income['id']}",
        json={"source": "Hacked", "amount": 1, "date": "2026-11-01"},
        headers=bob,
    )

    assert response.status_code == 404

    original = client.get("/income", headers=alice).json()[0]

    assert original["source"] == "Salary"
    assert original["amount"] == 45000


def test_other_user_cannot_delete_income(client, alice, bob):
    _, income = seed_alice(client, alice)

    response = client.delete(f"/income/{income['id']}", headers=bob)

    assert response.status_code == 404
    assert len(client.get("/income", headers=alice).json()) == 1


def test_balance_only_counts_own_data(client, alice, bob):
    seed_alice(client, alice)

    assert client.get("/balance", headers=bob).json() == {
        "total_income": 0,
        "total_expenses": 0,
        "balance": 0,
    }


def test_monthly_summary_only_counts_own_data(client, alice, bob):
    seed_alice(client, alice)

    data = client.get(
        "/monthly-summary?year=2026&month=11", headers=bob
    ).json()

    assert data["income"] == 0
    assert data["expenses"] == 0


def test_expense_total_only_counts_own_data(client, alice, bob):
    """Regression test: this endpoint once returned everyone's data."""
    seed_alice(client, alice)

    assert client.get("/expenses/total", headers=bob).json() == {"total": 0}


def test_expense_summary_only_counts_own_data(client, alice, bob):
    """Regression test: this endpoint once returned everyone's data."""
    seed_alice(client, alice)

    assert client.get("/expenses/summary", headers=bob).json() == []


def test_income_total_only_counts_own_data(client, alice, bob):
    seed_alice(client, alice)

    assert client.get("/income/total", headers=bob).json() == {
        "total_income": 0
    }
