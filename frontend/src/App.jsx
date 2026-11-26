import { useEffect, useState } from "react"
import "./App.css"

// Turns a backend error into readable text.
// FastAPI sends either a string or a list of validation errors.
function getErrorMessage(data, fallback) {
  if (!data || !data.detail) {
    return fallback
  }

  if (typeof data.detail === "string") {
    return data.detail
  }

  if (Array.isArray(data.detail)) {
    return data.detail.map((item) => item.msg).join(", ")
  }

  return fallback
}

function App() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")

  const [token, setToken] = useState(
    localStorage.getItem("token")
  )

  const [error, setError] = useState("")

  // Register
  const [isRegister, setIsRegister] = useState(false)
  const [registerMessage, setRegisterMessage] = useState("")

  const [balanceData, setBalanceData] = useState(null)
  const [monthlyData, setMonthlyData] = useState(null)

  const [expenses, setExpenses] = useState([])
  const [income, setIncome] = useState([])

  // Refresh + delete
  const [refreshKey, setRefreshKey] = useState(0)
  const [deleteError, setDeleteError] = useState("")

  // Add Expense
  const [category, setCategory] = useState("")
  const [amount, setAmount] = useState("")
  const [expenseDate, setExpenseDate] = useState("")
  const [expenseError, setExpenseError] = useState("")
  const [expenseSuccess, setExpenseSuccess] = useState("")

  // Add Income
  const [source, setSource] = useState("")
  const [incomeAmount, setIncomeAmount] = useState("")
  const [incomeDate, setIncomeDate] = useState("")
  const [incomeError, setIncomeError] = useState("")
  const [incomeSuccess, setIncomeSuccess] = useState("")

  // LOGIN

  async function handleLogin(event) {
    event.preventDefault()

    setError("")

    const response = await fetch(
      "http://127.0.0.1:8000/login",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          username: username,
          password: password
        })
      }
    )

    const data = await response.json()

    if (!response.ok) {
      setError(getErrorMessage(data, "Login failed"))
      return
    }

    localStorage.setItem("token", data.access_token)

    setToken(data.access_token)
  }

  // REGISTER

  async function handleRegister(event) {
    event.preventDefault()

    setError("")
    setRegisterMessage("")

    const response = await fetch(
      "http://127.0.0.1:8000/register",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          username: username,
          password: password
        })
      }
    )

    const data = await response.json()

    if (!response.ok) {
      setError(getErrorMessage(data, "Registration failed"))
      return
    }

    setPassword("")
    setIsRegister(false)
    setRegisterMessage("Account created! Please log in.")
  }

  // SWITCH BETWEEN LOGIN AND REGISTER

  function switchMode() {
    setIsRegister((current) => !current)
    setError("")
    setRegisterMessage("")
  }

  // FETCH DATA

  useEffect(() => {
    if (!token) {
      return
    }

    async function fetchData() {
      // Balance
      const balanceResponse = await fetch(
        "http://127.0.0.1:8000/balance",
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      )

      const balance = await balanceResponse.json()

      if (balanceResponse.ok) {
        setBalanceData(balance)
      }

      // Current month
      const now = new Date()

      const year = now.getFullYear()
      const month = now.getMonth() + 1

      // Monthly summary
      const monthlyResponse = await fetch(
        `http://127.0.0.1:8000/monthly-summary?year=${year}&month=${month}`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      )

      const monthly = await monthlyResponse.json()

      if (monthlyResponse.ok) {
        setMonthlyData(monthly)
      }

      // Expenses
      const expensesResponse = await fetch(
        "http://127.0.0.1:8000/expenses",
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      )

      const expensesData = await expensesResponse.json()

      if (expensesResponse.ok) {
        setExpenses(expensesData)
      }

      // Income
      const incomeResponse = await fetch(
        "http://127.0.0.1:8000/income",
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      )

      const incomeData = await incomeResponse.json()

      if (incomeResponse.ok) {
        setIncome(incomeData)
      }
    }

    fetchData()

  }, [token, refreshKey])

  // ADD EXPENSE

  async function handleAddExpense(event) {
    event.preventDefault()

    setExpenseError("")
    setExpenseSuccess("")

    const response = await fetch(
      "http://127.0.0.1:8000/expenses",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          category: category,
          amount: Number(amount),
          date: expenseDate
        })
      }
    )

    const data = await response.json()

    if (!response.ok) {
      setExpenseError(getErrorMessage(data, "Could not add expense"))
      return
    }

    setExpenses((currentExpenses) => [
      ...currentExpenses,
      data
    ])

    setBalanceData((currentBalance) => ({
      ...currentBalance,
      total_expenses:
        currentBalance.total_expenses + data.amount,
      balance:
        currentBalance.balance - data.amount
    }))

    setCategory("")
    setAmount("")
    setExpenseDate("")

    setExpenseSuccess("Expense added successfully")

    // Reload data so the Monthly Overview updates too
    setRefreshKey((key) => key + 1)
  }

  // ADD INCOME

  async function handleAddIncome(event) {
    event.preventDefault()

    setIncomeError("")
    setIncomeSuccess("")

    const response = await fetch(
      "http://127.0.0.1:8000/income",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          source: source,
          amount: Number(incomeAmount),
          date: incomeDate
        })
      }
    )

    const data = await response.json()

    if (!response.ok) {
      setIncomeError(getErrorMessage(data, "Could not add income"))
      return
    }

    setIncome((currentIncome) => [
      ...currentIncome,
      data
    ])

    setBalanceData((currentBalance) => ({
      ...currentBalance,
      total_income:
        currentBalance.total_income + data.amount,
      balance:
        currentBalance.balance + data.amount
    }))

    setSource("")
    setIncomeAmount("")
    setIncomeDate("")

    setIncomeSuccess("Income added successfully")

    // Reload data so the Monthly Overview updates too
    setRefreshKey((key) => key + 1)
  }

  // DELETE

  async function handleDelete(transaction) {
    if (!window.confirm("Delete this entry?")) {
      return
    }

    setDeleteError("")

    const path =
      transaction.type === "expense" ? "expenses" : "income"

    const response = await fetch(
      `http://127.0.0.1:8000/${path}/${transaction.rawId}`,
      {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    )

    if (!response.ok) {
      setDeleteError("Could not delete this entry.")
      return
    }

    setRefreshKey((key) => key + 1)
  }

  // LOGOUT

  function handleLogout() {
    localStorage.removeItem("token")

    setToken(null)
    setBalanceData(null)
    setMonthlyData(null)
    setExpenses([])
    setIncome([])
  }

  // LOGIN SCREEN

  if (!token) {
    return (
      <div className="login-page">

        <form
          className="login-card"
          onSubmit={isRegister ? handleRegister : handleLogin}
        >

          <h1>Family Finance</h1>

          <p>
            {isRegister
              ? "Create an account to get started."
              : "Sign in to manage your finances."}
          </p>

          {registerMessage && (
            <p className="success">
              {registerMessage}
            </p>
          )}

          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(event) =>
              setUsername(event.target.value)
            }
          />

          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(event) =>
              setPassword(event.target.value)
            }
          />

          {error && (
            <p className="error">
              {error}
            </p>
          )}

          <button type="submit">
            {isRegister ? "Create account" : "Login"}
          </button>

          <button
            type="button"
            className="link-button"
            onClick={switchMode}
          >
            {isRegister
              ? "Already have an account? Login"
              : "New here? Create an account"}
          </button>

        </form>

      </div>
    )
  }

  // TRANSACTIONS

  const transactions = [
    ...expenses.map((expense) => ({
      id: `expense-${expense.id}`,
      rawId: expense.id,
      name: expense.category,
      amount: -expense.amount,
      date: expense.date,
      type: "expense"
    })),

    ...income.map((item) => ({
      id: `income-${item.id}`,
      rawId: item.id,
      name: item.source,
      amount: item.amount,
      date: item.date,
      type: "income"
    }))
  ]

  transactions.sort(
    (a, b) =>
      new Date(b.date) - new Date(a.date)
  )

  // DASHBOARD

  return (
    <div className="app">

      <header className="header">

        <div>
          <h1>Family Finance</h1>
          <p>Track your money, simply.</p>
        </div>

        <button
          className="logout-button"
          onClick={handleLogout}
        >
          Logout
        </button>

      </header>

      <main>

        {/* SUMMARY */}

        <section className="summary-grid">

          <div className="card">
            <p className="card-label">
              Balance
            </p>

            <h2>
              ₹{balanceData?.balance ?? 0}
            </h2>
          </div>

          <div className="card">
            <p className="card-label">
              Income
            </p>

            <h2>
              ₹{balanceData?.total_income ?? 0}
            </h2>
          </div>

          <div className="card">
            <p className="card-label">
              Expenses
            </p>

            <h2>
              ₹{balanceData?.total_expenses ?? 0}
            </h2>
          </div>

        </section>

        {/* FORMS */}

        <section className="forms-grid">

          {/* EXPENSE */}

          <div className="card add-expense">

            <h2>Add Expense</h2>

            <form onSubmit={handleAddExpense}>

              <input
                type="text"
                placeholder="Category"
                value={category}
                onChange={(event) =>
                  setCategory(event.target.value)
                }
                required
              />

              <input
                type="number"
                placeholder="Amount"
                value={amount}
                onChange={(event) =>
                  setAmount(event.target.value)
                }
                min="0.01"
                step="0.01"
                required
              />

              <input
                type="date"
                value={expenseDate}
                onChange={(event) =>
                  setExpenseDate(event.target.value)
                }
                required
              />

              <button type="submit">
                Add Expense
              </button>

            </form>

            {expenseError && (
              <p className="error">
                {expenseError}
              </p>
            )}

            {expenseSuccess && (
              <p className="success">
                {expenseSuccess}
              </p>
            )}

          </div>

          {/* INCOME */}

          <div className="card add-income">

            <h2>Add Income</h2>

            <form onSubmit={handleAddIncome}>

              <input
                type="text"
                placeholder="Source"
                value={source}
                onChange={(event) =>
                  setSource(event.target.value)
                }
                required
              />

              <input
                type="number"
                placeholder="Amount"
                value={incomeAmount}
                onChange={(event) =>
                  setIncomeAmount(event.target.value)
                }
                min="0.01"
                step="0.01"
                required
              />

              <input
                type="date"
                value={incomeDate}
                onChange={(event) =>
                  setIncomeDate(event.target.value)
                }
                required
              />

              <button type="submit">
                Add Income
              </button>

            </form>

            {incomeError && (
              <p className="error">
                {incomeError}
              </p>
            )}

            {incomeSuccess && (
              <p className="success">
                {incomeSuccess}
              </p>
            )}

          </div>

        </section>

        {/* TRANSACTIONS + MONTHLY OVERVIEW */}

        <section className="content-grid">

          <div className="card transactions">

            <h2>Recent Transactions</h2>

            {deleteError && (
              <p className="error">
                {deleteError}
              </p>
            )}

            {transactions.length === 0 ? (

              <p>No transactions yet.</p>

            ) : (

              transactions.slice(0, 5).map((transaction) => (

                <div
                  className={`transaction ${transaction.type}`}
                  key={transaction.id}
                >
                  <div className="transaction-info">
                    <div className="transaction-icon">
                      {transaction.type === "income" ? "↑" : "↓"}
                    </div>

                    <div>
                      <span className="transaction-name">
                        {transaction.name}
                      </span>

                      <span className="transaction-date">
                        {transaction.date}
                      </span>
                    </div>
                  </div>

                  <div className="transaction-right">
                    <strong>
                      {transaction.amount > 0
                        ? `+ ₹${transaction.amount}`
                        : `- ₹${Math.abs(transaction.amount)}`
                      }
                    </strong>

                    <button
                      className="delete-button"
                      onClick={() => handleDelete(transaction)}
                    >
                      Delete
                    </button>
                  </div>
                </div>

              ))

            )}

          </div>

          <div className="card monthly-overview">

            <h2>Monthly Overview</h2>

            {monthlyData && (
              <>

                <p className="month-label">
                  {monthlyData.month}/{monthlyData.year}
                </p>

                <div className="monthly-stats">

                  <div>
                    <span>Income</span>

                    <strong>
                      ₹{monthlyData.income}
                    </strong>
                  </div>

                  <div>
                    <span>Expenses</span>

                    <strong>
                      ₹{monthlyData.expenses}
                    </strong>
                  </div>

                  <div>
                    <span>Remaining</span>

                    <strong>
                      ₹{monthlyData.balance}
                    </strong>
                  </div>

                </div>

                <div className="bar-chart">

                  <div className="bar-group">

                    <span>Income</span>

                    <div className="bar-track">

                      <div
                        className="bar income-bar"
                        style={{
                          width: `${
                            monthlyData.income > 0
                              ? 100
                              : 0
                          }%`
                        }}
                      />

                    </div>

                  </div>

                  <div className="bar-group">

                    <span>Expenses</span>

                    <div className="bar-track">

                      <div
                        className="bar expense-bar"
                        style={{
                          width: `${
                            monthlyData.income > 0
                              ? Math.min(
                                  (monthlyData.expenses /
                                    monthlyData.income) *
                                    100,
                                  100
                                )
                              : 0
                          }%`
                        }}
                      />

                    </div>

                  </div>

                </div>

              </>
            )}

          </div>

        </section>

      </main>

    </div>
  )
}

export default App
