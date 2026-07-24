from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
from models import db, Staff, Sale, Product, SaleItem, StockMovement, Category
from datetime import datetime, timezone, timedelta
import os
import shutil

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

    today_cost = 0
    for s in today_sales:
        for si in s.items:
            today_cost += (si.cost_price or 0) * si.qty
    today_profit = round(today_total - today_cost, 2)

    product_count = Product.query.filter_by(active=True).count()
    staff_count = Staff.query.filter_by(active=True).count()
    low_stock = Product.query.filter(Product.active == True, Product.stock_qty <= 10).order_by(Product.stock_qty).all()

    recent_sales_data = []
    for s in recent_sales:
        recent_sales_data.append({
            'id': s.id,
            'staff': s.staff,
            'total': s.total,
            'payment_method': s.payment_method,
            'time': (s.created_at + timedelta(hours=3)).strftime('%H:%M')
        })

    return render_template('admin_dashboard.html',
                           today_total=today_total,
                           today_count=today_count,
                           today_profit=today_profit,
                           month_total=month_total,
                           product_count=product_count,
                           staff_count=staff_count,
                           recent_sales=recent_sales_data,
                           low_stock=low_stock)


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


@admin_bp.route('/admin/reset-all', methods=['POST'])
def reset_all():
    if not admin_required():
        return redirect(url_for('auth.admin_login'))

    current_admin_id = session.get('staff_id')

    StockMovement.query.delete()
    SaleItem.query.delete()
    Sale.query.delete()
    Product.query.delete()
    Category.query.delete()
    Staff.query.filter(Staff.id != current_admin_id).delete()

    db.session.commit()
    flash('All data has been cleared. Your admin account was preserved.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/admin/backup')
def backup_database():
    if not admin_required():
        return redirect(url_for('auth.admin_login'))

    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'whispers_lounge.db')
    if not os.path.exists(db_path):
        flash('Database file not found.', 'danger')
        return redirect(url_for('admin.dashboard'))

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    return send_file(db_path, as_attachment=True,
                     download_name=f'whispers_lounge_backup_{timestamp}.db')


@admin_bp.route('/admin/restore', methods=['POST'])
def restore_database():
    if not admin_required():
        return redirect(url_for('auth.admin_login'))

    file = request.files.get('backup_file')
    if not file or not file.filename.endswith('.db'):
        flash('Please upload a valid .db backup file.', 'danger')
        return redirect(url_for('admin.dashboard'))

    instance_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')
    db_path = os.path.join(instance_dir, 'whispers_lounge.db')
    backup_path = db_path + '.old'

    shutil.copy2(db_path, backup_path)
    file.save(db_path)

    flash('Database restored successfully! Please reload the page.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/admin/daily-summary')
def daily_summary():
    if not admin_required():
        return redirect(url_for('auth.admin_login'))

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_sales = Sale.query.filter(Sale.created_at >= today).all()

    total_revenue = round(sum(s.total for s in today_sales), 2)
    total_cost = 0
    for s in today_sales:
        for si in s.items:
            total_cost += (si.cost_price or 0) * si.qty
    total_profit = round(total_revenue - total_cost, 2)
    transaction_count = len(today_sales)

    payment_breakdown = {}
    for s in today_sales:
        method = s.payment_method.title()
        if method not in payment_breakdown:
            payment_breakdown[method] = {'count': 0, 'total': 0}
        payment_breakdown[method]['count'] += 1
        payment_breakdown[method]['total'] += s.total

    staff_breakdown = {}
    for s in today_sales:
        name = s.staff.name
        if name not in staff_breakdown:
            staff_breakdown[name] = {'count': 0, 'total': 0}
        staff_breakdown[name]['count'] += 1
        staff_breakdown[name]['total'] += s.total

    item_summary = {}
    for s in today_sales:
        for si in s.items:
            pname = si.product.name
            if pname not in item_summary:
                item_summary[pname] = {'qty': 0, 'total': 0}
            item_summary[pname]['qty'] += si.qty
            item_summary[pname]['total'] += si.qty * si.unit_price
    top_items = sorted(item_summary.items(), key=lambda x: x[1]['total'], reverse=True)[:10]

    summary_time = (datetime.now(timezone.utc) + timedelta(hours=3)).strftime('%d/%m/%Y %H:%M EAT')

    return render_template('daily_summary.html',
                           total_revenue=total_revenue,
                           total_profit=total_profit,
                           total_cost=round(total_cost, 2),
                           transaction_count=transaction_count,
                           payment_breakdown=payment_breakdown,
                           staff_breakdown=staff_breakdown,
                           top_items=top_items,
                           summary_time=summary_time)
