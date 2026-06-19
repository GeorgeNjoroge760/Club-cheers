from flask import Blueprint, render_template, request, session, redirect, url_for, make_response
from models import db, Sale, SaleItem, Product, Staff
from datetime import datetime, timedelta, timezone
from io import BytesIO
from xhtml2pdf import pisa
from jinja2 import Template

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
        cost = 0
        for s in day_sales:
            for si in s.items:
                cost += (si.cost_price or 0) * si.qty
        daily_sales.append({
            'date': day.strftime('%d/%m'),
            'total': round(total, 2),
            'profit': round(total - cost, 2),
            'count': count
        })

    # Top products this month
    month_start = today.replace(day=1)
    top_products = db.session.query(
        Product.name,
        db.func.sum(SaleItem.qty).label('qty'),
        db.func.sum(SaleItem.qty * SaleItem.unit_price).label('total'),
        db.func.sum(SaleItem.qty * (SaleItem.unit_price - (SaleItem.cost_price or 0))).label('profit')
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

    # Compute profit per staff (separate query to avoid multiplying counts)
    staff_profit_map = {}
    for s in Sale.query.filter(Sale.created_at >= month_start).all():
        sname = s.staff.name
        sp = staff_profit_map.get(sname, 0)
        for si in s.items:
            sp += (si.unit_price - (si.cost_price or 0)) * si.qty
        staff_profit_map[sname] = sp
    staff_perf = [(name, count, total, round(staff_profit_map.get(name, 0), 2))
                  for name, count, total in staff_perf]

    # Payment method breakdown this month
    payment_breakdown = db.session.query(
        Sale.payment_method,
        db.func.count(Sale.id).label('count'),
        db.func.sum(Sale.total).label('total')
    ).filter(Sale.created_at >= month_start
    ).group_by(Sale.payment_method).all()

    monthly_total = sum(s.total for s in Sale.query.filter(Sale.created_at >= month_start).all())
    monthly_count = Sale.query.filter(Sale.created_at >= month_start).count()
    monthly_cost = 0
    for s in Sale.query.filter(Sale.created_at >= month_start).all():
        for si in s.items:
            monthly_cost += (si.cost_price or 0) * si.qty
    monthly_profit = round(monthly_total - monthly_cost, 2)

    return render_template('analytics.html',
                           daily_sales=daily_sales,
                           top_products=top_products,
                           staff_perf=staff_perf,
                           payment_breakdown=payment_breakdown,
                           monthly_total=round(monthly_total, 2),
                           monthly_count=monthly_count,
                           monthly_profit=monthly_profit)


def render_pdf(template_path, context):
    html = render_template(template_path, **context)
    buf = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buf)
    if pisa_status.err:
        return None
    buf.seek(0)
    return buf


@analytics_bp.route('/admin/analytics/pdf')
def analytics_pdf():
    if not admin_required():
        return redirect(url_for('auth.admin_login'))

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today.replace(day=1)

    daily_sales = []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        next_day = day + timedelta(days=1)
        day_sales = Sale.query.filter(Sale.created_at >= day, Sale.created_at < next_day).all()
        total = sum(s.total for s in day_sales)
        count = len(day_sales)
        cost = 0
        for s in day_sales:
            for si in s.items:
                cost += (si.cost_price or 0) * si.qty
        daily_sales.append({
            'date': day.strftime('%d/%m'),
            'total': round(total, 2),
            'profit': round(total - cost, 2),
            'count': count
        })

    top_products = db.session.query(
        Product.name,
        db.func.sum(SaleItem.qty).label('qty'),
        db.func.sum(SaleItem.qty * SaleItem.unit_price).label('total'),
        db.func.sum(SaleItem.qty * (SaleItem.unit_price - (SaleItem.cost_price or 0))).label('profit')
    ).join(SaleItem, Product.id == SaleItem.product_id
    ).join(Sale, Sale.id == SaleItem.sale_id
    ).filter(Sale.created_at >= month_start
    ).group_by(Product.id
    ).order_by(db.desc('total')
    ).limit(10).all()

    staff_perf = db.session.query(
        Staff.name,
        db.func.count(Sale.id).label('count'),
        db.func.sum(Sale.total).label('total')
    ).join(Sale, Staff.id == Sale.staff_id
    ).filter(Sale.created_at >= month_start
    ).group_by(Staff.id
    ).order_by(db.desc('total')).all()

    staff_profit_map = {}
    for s in Sale.query.filter(Sale.created_at >= month_start).all():
        sname = s.staff.name
        sp = staff_profit_map.get(sname, 0)
        for si in s.items:
            sp += (si.unit_price - (si.cost_price or 0)) * si.qty
        staff_profit_map[sname] = sp
    staff_perf = [(name, count, total, round(staff_profit_map.get(name, 0), 2))
                  for name, count, total in staff_perf]

    payment_breakdown = db.session.query(
        Sale.payment_method,
        db.func.count(Sale.id).label('count'),
        db.func.sum(Sale.total).label('total')
    ).filter(Sale.created_at >= month_start
    ).group_by(Sale.payment_method).all()

    monthly_total = sum(s.total for s in Sale.query.filter(Sale.created_at >= month_start).all())
    monthly_count = Sale.query.filter(Sale.created_at >= month_start).count()
    monthly_cost = 0
    for s in Sale.query.filter(Sale.created_at >= month_start).all():
        for si in s.items:
            monthly_cost += (si.cost_price or 0) * si.qty
    monthly_profit = round(monthly_total - monthly_cost, 2)

    now = datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')

    context = dict(
        daily_sales=daily_sales,
        top_products=top_products,
        staff_perf=staff_perf,
        payment_breakdown=payment_breakdown,
        monthly_total=round(monthly_total, 2),
        monthly_count=monthly_count,
        monthly_profit=monthly_profit,
        now=now
    )

    buf = render_pdf('analytics_pdf.html', context)
    if buf is None:
        return "PDF generation failed", 500

    resp = make_response(buf.read())
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = 'inline; filename=analytics_report.pdf'
    return resp