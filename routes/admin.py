from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, Staff, Sale, Product
from datetime import datetime, timezone

admin_bp = Blueprint('admin', __name__)


def admin_required():
    return session.get('role') == 'admin'


@admin_bp.route('/admin')
def dashboard():
    if not admin_required():
        return redirect(url_for('auth.admin_login'))

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today.replace(day=1)

    today_sales = Sale.query.filter(Sale.created_at >= today).all()
    month_sales = Sale.query.filter(Sale.created_at >= month_start).all()
    recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(5).all()

    today_total = round(sum(s.total for s in today_sales), 2)
    today_count = len(today_sales)
    month_total = round(sum(s.total for s in month_sales), 2)

    cost = 0
    for s in today_sales:
        for si in s.items:
            cost += (si.cost_price or 0) * si.qty
    today_profit = round(today_total - cost, 2)

    product_count = Product.query.filter_by(active=True).count()
    staff_count = Staff.query.filter_by(active=True).count()

    return render_template('admin_dashboard.html',
                           today_total=today_total,
                           today_count=today_count,
                           today_profit=today_profit,
                           month_total=month_total,
                           product_count=product_count,
                           staff_count=staff_count,
                           recent_sales=recent_sales)


@admin_bp.route('/admin/staff')
def staff_list():
    if not admin_required():
        return redirect(url_for('auth.admin_login'))
    staff = Staff.query.order_by(Staff.role, Staff.name).all()
    return render_template('admin_staff.html', staff=staff)


@admin_bp.route('/admin/staff/add', methods=['GET', 'POST'])
def staff_add():
    if not admin_required():
        return redirect(url_for('auth.admin_login'))
    if request.method == 'POST':
        name = request.form.get('name')
        role = request.form.get('role', 'attendant')
        password = request.form.get('password', '')
        staff = Staff(name=name, role=role)
        if password:
            staff.set_password(password)
        db.session.add(staff)
        db.session.commit()
        return redirect(url_for('admin.staff_list'))
    return render_template('staff_form.html', staff=None)


@admin_bp.route('/admin/staff/edit/<int:staff_id>', methods=['GET', 'POST'])
def staff_edit(staff_id):
    if not admin_required():
        return redirect(url_for('auth.admin_login'))
    staff = Staff.query.get_or_404(staff_id)
    if request.method == 'POST':
        staff.name = request.form.get('name')
        password = request.form.get('password', '')
        if password:
            staff.set_password(password)
        db.session.commit()
        return redirect(url_for('admin.staff_list'))
    return render_template('staff_form.html', staff=staff)


@admin_bp.route('/admin/staff/toggle/<int:staff_id>', methods=['POST'])
def staff_toggle(staff_id):
    if not admin_required():
        return redirect(url_for('auth.admin_login'))
    staff = Staff.query.get_or_404(staff_id)
    if staff.role != 'admin':
        staff.active = not staff.active
        db.session.commit()
    return redirect(url_for('admin.staff_list'))


@admin_bp.route('/admin/change-password', methods=['GET', 'POST'])
def change_password():
    if not admin_required():
        return redirect(url_for('auth.admin_login'))
    staff = Staff.query.get(session['staff_id'])
    if request.method == 'POST':
        current = request.form.get('current_password')
        new = request.form.get('new_password')
        confirm = request.form.get('confirm_password')
        if not staff.check_password(current):
            return render_template('change_password.html', error='Current password is incorrect')
        if new != confirm:
            return render_template('change_password.html', error='Passwords do not match')
        if len(new) < 4:
            return render_template('change_password.html', error='Password must be at least 4 characters')
        staff.set_password(new)
        db.session.commit()
        return render_template('change_password.html', success='Password changed successfully')
    return render_template('change_password.html')
