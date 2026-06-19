from flask import Blueprint, render_template, request, session, redirect, url_for
from models import db, Sale, SaleItem, StockMovement, Product, Category, Staff
from datetime import datetime, timedelta, timezone

reports_bp = Blueprint('reports', __name__)


def admin_required():
    return session.get('role') == 'admin'


@reports_bp.route('/reports')
def reports():
    if not admin_required():
        return redirect(url_for('auth.admin_login'))

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    today_sales = Sale.query.filter(Sale.created_at >= today).all()
    week_sales = Sale.query.filter(Sale.created_at >= week_start).all()
    month_sales = Sale.query.filter(Sale.created_at >= month_start).all()
    all_sales = Sale.query.order_by(Sale.created_at.desc()).limit(100).all()

    def calc_stats(sales):
        total = sum(s.total for s in sales)
        cost = 0
        for s in sales:
            for si in s.items:
                cost += (si.cost_price or 0) * si.qty
        count = len(sales)
        return {'total': round(total, 2), 'cost': round(cost, 2),
                'profit': round(total - cost, 2), 'count': count}

    today_stats = calc_stats(today_sales)
    week_stats = calc_stats(week_sales)
    month_stats = calc_stats(month_sales)

    top_products = db.session.query(
        Product.name,
        db.func.sum(SaleItem.qty).label('qty')
    ).join(SaleItem, Product.id == SaleItem.product_id
    ).join(Sale, Sale.id == SaleItem.sale_id
    ).filter(Sale.created_at >= today
    ).group_by(Product.id
    ).order_by(db.desc('qty')
    ).limit(10).all()

    staff_sales = db.session.query(
        Staff.name,
        db.func.count(Sale.id).label('count'),
        db.func.sum(Sale.total).label('total')
    ).join(Sale, Staff.id == Sale.staff_id
    ).filter(Sale.created_at >= today
    ).group_by(Staff.id).all()

    return render_template('reports.html',
                           today_stats=today_stats,
                           week_stats=week_stats,
                           month_stats=month_stats,
                           top_products=top_products,
                           staff_sales=staff_sales,
                           all_sales=all_sales)
