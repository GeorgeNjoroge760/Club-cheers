from flask import Blueprint, render_template, request, session, redirect, url_for
from models import db, Sale, SaleItem, Product, Staff
from datetime import datetime, timedelta, timezone

analytics_bp = Blueprint('analytics', __name__)


def admin_required():
    return session.get('role') == 'admin'


@analytics_bp.route('/admin/analytics')
def analytics():
    if not admin_required():
        return redirect(url_for('auth.admin_login'))

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Daily sales for last 30 days
    daily_sales = []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        next_day = day + timedelta(days=1)
        day_sales = Sale.query.filter(Sale.created_at >= day, Sale.created_at < next_day).all()
        total = sum(s.total for s in day_sales)
        count = len(day_sales)
        daily_sales.append({
            'date': day.strftime('%d/%m'),
            'total': round(total, 2),
            'count': count
        })

    # Top products this month
    month_start = today.replace(day=1)
    top_products = db.session.query(
        Product.name,
        db.func.sum(SaleItem.qty).label('qty'),
        db.func.sum(SaleItem.qty * SaleItem.unit_price).label('total')
    ).join(SaleItem, Product.id == SaleItem.product_id
    ).join(Sale, Sale.id == SaleItem.sale_id
    ).filter(Sale.created_at >= month_start
    ).group_by(Product.id
    ).order_by(db.desc('total')
    ).limit(10).all()

    # Staff performance this month
    staff_perf = db.session.query(
        Staff.name,
        db.func.count(Sale.id).label('count'),
        db.func.sum(Sale.total).label('total')
    ).join(Sale, Staff.id == Sale.staff_id
    ).filter(Sale.created_at >= month_start
    ).group_by(Staff.id
    ).order_by(db.desc('total')).all()

    # Payment method breakdown this month
    payment_breakdown = db.session.query(
        Sale.payment_method,
        db.func.count(Sale.id).label('count'),
        db.func.sum(Sale.total).label('total')
    ).filter(Sale.created_at >= month_start
    ).group_by(Sale.payment_method).all()

    monthly_total = sum(s.total for s in Sale.query.filter(Sale.created_at >= month_start).all())
    monthly_count = Sale.query.filter(Sale.created_at >= month_start).count()

    return render_template('analytics.html',
                           daily_sales=daily_sales,
                           top_products=top_products,
                           staff_perf=staff_perf,
                           payment_breakdown=payment_breakdown,
                           monthly_total=round(monthly_total, 2),
                           monthly_count=monthly_count)