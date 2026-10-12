# Quilo – Financial Risk & Scenario Analysis Dashboard

A full-stack demo application for **credit-union / bank stress testing and risk analytics**.

Inspired by modern ALCO / risk dashboards, this project lets you:

- View key profitability metrics (ROA, NIM, NII, efficiency, capital)
- Run **interactive stress scenarios** (interest-rate shock + charge-off rate)
- See projected Net Interest Income and radar risk profile update in real time
- Compare the institution against its peer group
- Explore historical industry charge-off rates and loan origination
- Discover related **Investment Banking training courses** (Uncodemy)

---

## Tech Stack

| Layer        | Technology                          |
|--------------|-------------------------------------|
| Backend      | Python 3.12 + Flask                 |
| Database     | MySQL 8                             |
| ORM          | SQLAlchemy (Flask-SQLAlchemy)       |
| Frontend     | HTML5, CSS3, Vanilla JS, Chart.js   |
| Charts       | Line (NII & Industry), Radar        |

---

## Features

- **Stress Lab** – Adjust horizon (months), rate change (bp) and net charge-off rate; instantly recompute NII path and risk radar
- **Save / Load scenarios** – Persist custom stress runs to MySQL
- **Peer comparison table** – Institution vs peer-group averages
- **Industry history chart** – Long-run charge-off rates vs consumer loan origination
- **Learning section** – Direct links to Investment Banking courses in Noida & Delhi (Uncodemy)
- Dark, modern UI inspired by professional risk platforms
- Every navigation item and control is fully interactive

---

## Project Structure

```
financial-risk-dashboard/
├── backend/
│   ├── app.py              # Flask application + APIs
│   ├── config.py
│   ├── models.py           # SQLAlchemy models
│   └── requirements.txt
├── database/
│   └── schema.sql          # MySQL schema + seed data
├── frontend/
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── css/dashboard.css
│       └── js/dashboard.js
├── README.md
├── .env.example
└── .gitignore
```

---

## Quick Start

### 1. Prerequisites

- Python 3.10+
- MySQL 8.x
- pip

### 2. Database setup

```bash
# Login to MySQL and create user + database
mysql -u root -p < database/schema.sql
```

Or manually:

```sql
CREATE DATABASE financial_risk CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'riskuser'@'localhost' IDENTIFIED BY 'riskpass';
GRANT ALL PRIVILEGES ON financial_risk.* TO 'riskuser'@'localhost';
FLUSH PRIVILEGES;
```

Then load the schema:

```bash
mysql -u riskuser -priskpass financial_risk < database/schema.sql
```

### 3. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Optional: copy .env.example → .env and edit credentials
export DATABASE_URL="mysql+pymysql://riskuser:riskpass@localhost/financial_risk"

python app.py
```

Server starts at **http://0.0.0.0:5000**

### 4. Open the app

Visit: [http://localhost:5000](http://localhost:5000)

---

## API Endpoints

| Method | Endpoint              | Description                          |
|--------|-----------------------|--------------------------------------|
| GET    | `/`                   | Dashboard UI                         |
| GET    | `/api/health`         | Health check                         |
| GET    | `/api/dashboard`      | Full dashboard payload               |
| POST   | `/api/stress`         | Run stress scenario                  |
| GET    | `/api/industry-history` | Historical charge-off & origination |
| GET    | `/api/metrics/history`| Institution metric history           |
| POST   | `/api/save-scenario`  | Persist a custom scenario            |
| GET    | `/api/scenarios`      | List saved scenarios                 |

### Example stress request

```bash
curl -X POST http://localhost:5000/api/stress \
  -H "Content-Type: application/json" \
  -d '{"horizon_months":18,"rate_change_bp":500,"net_charge_off_rate":0.52}'
```

---

## Learning Resources (Uncodemy)

These links are integrated in the **Learning** tab and footer so users can go deeper into investment banking & risk concepts:

- [Investment Banking Training Course – Noida](https://uncodemy.com/course/investment-banking-training-course-in-noida)
- [Investment Banking Training Course – Delhi](https://uncodemy.com/course/investment-banking-training-course-in-delhi)

---

## Environment Variables

See `.env.example`:

```
SECRET_KEY=your-secret-key
DATABASE_URL=mysql+pymysql://riskuser:riskpass@localhost/financial_risk
```

---

## Notes

- The stress model is a simplified educational projection (rate pass-through + credit-loss drag). It is **not** a production regulatory stress engine.
- Seed data approximates the original dashboard values (Idaho Central Credit Union style metrics).
- All UI controls (sliders, navigation, save/load, modal, charts) are fully wired and working.

---

## License

MIT – free to use for learning and portfolio purposes.
