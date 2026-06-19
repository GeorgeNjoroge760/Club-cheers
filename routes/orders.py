from flask import Blueprint, render_template, request, session, redirect, url_for
from models import db, Sale, SaleItem
from datetime import datetime, timezone

orders_bp = Blueprint('orders', __name__)


def admin_required():
    return session.get('role') == 'admin'


@orders_bp.route('/admin/orders')
def orders():
    if not admin_required():
        return redirect(url_for('auth.admin_login'))

    page = request.args.get('page', 1, type=int)
    per_page = 20

    sales = Sale.query.order_by(Sale.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    orders_data = []
    for s in sales.items:
        orders_data.append({
            'id': s.id,
            'staff': s.staff.name,
            'total': s.total,
            'payment_method': 'M-Pesa' if s.payment_method == 'mpesa' else s.payment_method.title(),
            'order_items': [{
                'name': si.product.name,
                'qty': si.qty,
                'unit_price': si.unit_price,
                'total': si.qty * si.unit_price
            } for si in s.items],
            'time': s.created_at.strftime('%d/%m/%Y %H:%M')
        })

    return render_template('orders.html',
                           orders=orders_data,
                           page=page,
                           total_pages=sales.pages)