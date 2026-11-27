"""Balance, totals, category summary and monthly summary tests."""


def add_sample_data(client, headers):
    client.post(
        "/income",
        json={"source": "Salary", "amount": 45000, "date": "2026-11-01"},
        headers=headers,
    )

    expenses = [
        ("Rent", 12000, "2026-11-02"),
        ("Groceries", 6500, "2026-11-05"),
        ("Groceries", 1500, "2026-11-20"),
        ("Rent", 12000, "2026-10-02"),  # a different month
    ]

    for category, amount, date in expenses:
        client.post(
            "/expenses",
            json={"category": category, "amount": amount, "date": date},
            headers=headers,
        )


def test_balance_for_new_user_is_zero(client, alice):
    response = client.get("/balance", headers=alice)

    assert response.status_code == 200
    assert response.json() == {
        "total_income": 0,
        "total_expenses": 0,
        "balance": 0,
    }


def test_balance_is_income_minus_expenses(client, alice):
    add_sample_data(client, alice)

    data = client.get("/balance", headers=alice).json()

    assert data["total_income"] == 45000
    assert data["total_expenses"] == 12000 + 6500 + 1500 + 12000
    assert data["balance"] == 45000 - 32000


def test_income_total(client, alice):
    add_sample_data(client, alice)

    response = client.get("/income/total", headers=alice)

    assert response.json() == {"total_income": 45000}


def test_expense_total(client, alice):
    add_sample_data(client, alice)

    response = client.get("/expenses/total", headers=alice)

    assert response.json() == {"total": 32000}


def test_expense_total_for_one_day(client, alice):
    add_sample_data(client, alice)

    response = client.get("/expenses/total?date=2026-11-05", headers=alice)

    assert response.json() == {"total": 6500}


def test_expense_summary_groups_by_category(client, alice):
    add_sample_data(client, alice)

    response = client.get("/expenses/summary", headers=alice)

    assert response.status_code == 200

    totals = {row["category"]: row["total"] for row in response.json()}

    assert totals == {"Rent": 24000, "Groceries": 8000}


def test_expense_summary_is_sorted_biggest_first(client, alice):
    add_sample_data(client, alice)

    rows = client.get("/expenses/summary", headers=alice).json()

    assert rows[0]["category"] == "Rent"


def test_monthly_summary_only_counts_that_month(client, alice):
    add_sample_data(client, alice)

    november = client.get(
        "/monthly-summary?year=2026&month=11", headers=alice
    ).json()

    assert november["income"] == 45000
    assert november["expenses"] == 12000 + 6500 + 1500
    assert november["balance"] == 45000 - 20000

    october = client.get(
        "/monthly-summary?year=2026&month=10", headers=alice
    ).json()

    assert october["income"] == 0
    assert october["expenses"] == 12000
    assert october["balance"] == -12000


def test_monthly_summary_for_empty_month(client, alice):
    response = client.get(
        "/monthly-summary?year=2026&month=1", headers=alice
    )

    assert response.json()["balance"] == 0


def test_deleting_an_entry_updates_the_balance(client, alice):
    created = client.post(
        "/expenses",
        json={"category": "Rent", "amount": 1000, "date": "2026-11-02"},
        headers=alice,
    ).json()

    client.delete(f"/expenses/{created['id']}", headers=alice)

    assert client.get("/balance", headers=alice).json()["balance"] == 0
