# Cheers Club POS

A mobile-friendly point-of-sale system for the Cheers Club bar/restaurant built with Flask.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3, Flask |
| Database | SQLite (dev), MySQL (production) |
| Frontend | Bootstrap 5.3, Bootstrap Icons |
| Charts | Chart.js |
| ORM | SQLAlchemy |

## Features

### Point-of-Sale
- Product grid grouped by category with category filter
- Cart with qty +/- controls
- Payment selection (Cash / Card / M-Pesa)
- Receipt modal with print capability
- Stock auto-deduction on checkout

### Admin Dashboard
- Today's sales total & transaction count
- Monthly sales total
- Active product & staff counts
- Recent orders table with quick links

### Orders
- Paginated order history with item-level breakdown
- Each order card shows products, quantities, totals

### Sales History
- Paginated table with staff & payment method filters
- Receipt button per sale (JSON endpoint + modal view)

### Inventory Management
- Product CRUD (name, category, sell/cost price, stock, unit)
- Category management
- Stock-in recording with cost price tracking

### Staff Management
- Add / edit / toggle active staff
- Role: admin or attendant
- Change password for admin account

### Analytics
- 30-day revenue bar chart (Chart.js)
- Top 5 selling products
- Staff performance breakdown
- Payment method distribution

### Reports
- Daily, weekly, monthly, or custom date range
- Sales, orders, revenue, profit summaries

## Installation

```bash
# Clone
git clone https://github.com/GeorgeNjoroge760/Club-cheers.git
cd Club-cheers

# Create virtual env
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate # Linux/Mac

# Install deps
pip install -r requirements.txt

# Seed database
python seed.py

# Run
python app.py
```

Visit `http://127.0.0.1:5000`

### Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Attendant | Alice | _(none — select from list)_ |
| Attendant | Bob | _(none — select from list)_ |

## Usage

### Attendant Flow
1. Open the app → select your name from the staff list
2. Tap products to add to cart
3. Adjust quantities with +/- buttons
4. Select payment method (Cash / Card / M-Pesa)
5. Tap **Charge** to complete the sale
6. Receipt modal appears → tap **Print** to print via browser

### Admin Flow
1. Go to `/admin/login` → log in as admin
2. **Dashboard** — quick overview of today's performance
3. **Orders** — view all orders with item breakdowns
4. **Products** — add/edit products, manage stock-in
5. **Sales** — filtered sales history with receipt viewer
6. **Users** — manage staff accounts
7. **Analytics** — charts and performance data
8. **Reports** — date-range reports

## Deployment (PythonAnywhere)

```bash
# Pull latest
cd ~/Club-cheers
git pull

# Install any new deps
source venv/bin/activate
pip install -r requirements.txt

# Reload web app from PythonAnywhere dashboard
```

Set `DATABASE_URL` environment variable to switch to MySQL on a paid plan.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Staff selection page |
| POST | `/select-staff` | Select an attendant |
| GET | `/admin/login` | Admin login page |
| POST | `/admin/login` | Admin login |
| GET | `/pos` | POS page |
| POST | `/pos/cart/add` | Add item to cart |
| POST | `/pos/cart/update` | Update item qty |
| POST | `/pos/cart/clear` | Clear cart |
| POST | `/pos/checkout` | Complete sale |
| GET | `/sales` | Sales history |
| GET | `/sales/<id>/receipt` | Receipt JSON |
| GET | `/admin/dashboard` | Dashboard page |
| GET | `/admin/dashboard/data` | Dashboard chart data |
| GET | `/admin/orders` | Orders page |
| GET | `/admin/analytics` | Analytics page |
| GET | `/admin/analytics/data` | Analytics JSON data |
| GET | `/inventory` | Product list |
| POST | `/inventory/product/add` | Add product |
| POST | `/inventory/product/edit/<id>` | Edit product |
| POST | `/inventory/product/toggle/<id>` | Toggle active |
| POST | `/inventory/stock-in` | Record stock-in |
| GET | `/reports` | Reports page |
| GET | `/reports/data` | Reports JSON data |
| GET | `/admin/staff` | Staff list |
| POST | `/admin/staff/add` | Add staff |
| POST | `/admin/staff/edit/<id>` | Edit staff |
| POST | `/admin/staff/toggle/<id>` | Toggle active |
| GET/POST | `/admin/change-password` | Change admin password |
| GET | `/logout` | Logout |

## Database Schema

```
Staff (id, name, role, password_hash, active, created_at)
Category (id, name, sort_order)
Product (id, name, category_id, sell_price, cost_price, stock_qty, unit, active, created_at)
Sale (id, staff_id, total, payment_method, created_at)
SaleItem (id, sale_id, product_id, qty, unit_price, cost_price)
StockMovement (id, product_id, qty, type, cost_per_unit, note, created_at)
```
