from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, Staff

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def staff_select():
    staff = Staff.query.filter_by(active=True, role='attendant').all()
    return render_template('staff_select.html', staff=staff)


@auth_bp.route('/select-staff', methods=['POST'])
def select_staff():
    staff_id = request.form.get('staff_id')
    staff = Staff.query.get(staff_id)
    if staff and staff.active and staff.role == 'attendant':
        session['staff_id'] = staff.id
        session['staff_name'] = staff.name
        session['role'] = 'attendant'
        return redirect(url_for('pos.pos'))
    return redirect(url_for('auth.staff_select'))


@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        staff = Staff.query.filter_by(name=username, role='admin').first()
        if staff and staff.check_password(password):
            session['staff_id'] = staff.id
            session['staff_name'] = staff.name
            session['role'] = 'admin'
            return redirect(url_for('admin.dashboard'))
        return render_template('admin_login.html', error='Invalid credentials')
    return render_template('admin_login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.staff_select'))
