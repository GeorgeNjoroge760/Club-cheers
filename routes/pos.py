from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from models import db, Product, Category, Sale, SaleItem, StockMovement, Staff
from printer import print_receipt
from datetime import datetime, timezone

pos_bp = Blueprint('pos', __name__)


def pos_required():
    if 'role' not in session or session['role'] not in ('attendant', 'admin'):
        return False
    return True


@pos_bp.route('/pos')
def pos():
    if not pos_required():
        return redirect(url_for('auth.staff_select'))
    categories = Category.query.order_by(Category.sort_order).all()
    products = Product.query.filter_by(active=True).order_by(Product.category_id, Product.name).all()
    cart = session.get('cart', [])

    receipt = None
    receipt_id = request.args.get('receipt')
    if receipt_id:
        sale = Sale.query.get(int(receipt_id))
        if sale:
            receipt = {
                'id': sale.id,
                'items': [{
                    'name': si.product.name,
                    'qty': si.qty,
                    'total': si.qty * si.unit_price
                } for si in sale.items],
                'total': sale.total,
                'payment_method': 'M-Pesa' if sale.payment_method == 'mpesa' else sale.payment_method.title(),
                'staff': sale.staff.name,
                'time': sale.created_at.strftime('%d/%m/%Y %H:%M')
            }

    return render_template('pos.html', categories=categories, products=products, cart=cart, receipt=receipt)


@pos_bp.route('/pos/cart/add', methods=['POST'])
def cart_add():
    if not pos_required():
        return jsonify({'error': 'Unauthorized'}), 401
    product_id = int(request.form.get('product_id'))
    product = Product.query.get(product_id)
    if not product or not product.active:
        return jsonify({'error': 'Product not found'}), 404

    cart = session.get('cart', [])
    for item in cart:
        if item['product_id'] == product_id:
            item['qty'] += 1
            item['total'] = round(item['qty'] * item['unit_price'], 2)
            session['cart'] = cart
            return jsonify({'cart': cart, 'total': calc_total(cart)})

    cart.append({
        'product_id': product.id,
        'name': product.name,
        'qty': 1,
        'unit_price': product.sell_price,
        'total': product.sell_price
    })
    session['cart'] = cart
    return jsonify({'cart': cart, 'total': calc_total(cart)})


@pos_bp.route('/pos/cart/update', methods=['POST'])
def cart_update():
    if not pos_required():
        return jsonify({'error': 'Unauthorized'}), 401
    product_id = int(request.form.get('product_id'))
    qty = int(request.form.get('qty'))
    cart = session.get('cart', [])

    if qty <= 0:
        cart = [i for i in cart if i['product_id'] != product_id]
    else:
        for item in cart:
            if item['product_id'] == product_id:
                item['qty'] = qty
                item['total'] = round(qty * item['unit_price'], 2)
                break

    session['cart'] = cart
    return jsonify({'cart': cart, 'total': calc_total(cart)})


@pos_bp.route('/pos/cart/clear', methods=['POST'])
def cart_clear():
    session['cart'] = []
    return jsonify({'cart': [], 'total': 0})


@pos_bp.route('/pos/checkout', methods=['POST'])
def checkout():
    if not pos_required():
        return redirect(url_for('auth.staff_select'))

    cart = session.get('cart', [])
    if not cart:
        return redirect(url_for('pos.pos'))

    payment_method = request.form.get('payment_method', 'cash')
    staff_id = session.get('staff_id')

    total = calc_total(cart)
    sale = Sale(staff_id=staff_id, total=total, payment_method=payment_method)
    db.session.add(sale)
    db.session.flush()

    sale_items_data = []
    for item in cart:
        product = Product.query.get(item['product_id'])
        sale_item = SaleItem(
            sale_id=sale.id,
            product_id=item['product_id'],
            qty=item['qty'],
            unit_price=item['unit_price'],
            cost_price=product.cost_price
        )
        db.session.add(sale_item)

        product.stock_qty -= item['qty']
        movement = StockMovement(
            product_id=item['product_id'],
            qty=-item['qty'],
            type='sale',
            note=f"Sale #{sale.id}"
        )
        db.session.add(movement)

        sale_items_data.append({
            'name': item['name'],
            'qty': item['qty'],
            'total': item['total']
        })

    db.session.commit()

    print_receipt({
        'items': sale_items_data,
        'total': total,
        'payment_method': payment_method.title(),
        'staff': session.get('staff_name', '')
    })

    session['cart'] = []
    return redirect(url_for('pos.pos', receipt=sale.id))


def calc_total(cart):
    return round(sum(item['total'] for item in cart), 2)


@pos_bp.route('/sales')
def sales_history():
    if not pos_required():
        return redirect(url_for('auth.staff_select'))

    staff_id = session.get('staff_id')
    role = session.get('role')

    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = Sale.query
    if role != 'admin':
        query = query.filter_by(staff_id=staff_id)

    sales = query.order_by(Sale.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    sales_data = []
    for s in sales.items:
        sales_data.append({
            'id': s.id,
            'staff': s.staff.name,
            'total': s.total,
            'payment_method': 'M-Pesa' if s.payment_method == 'mpesa' else s.payment_method.title(),
            'items_count': sum(si.qty for si in s.items),
            'time': s.created_at.strftime('%d/%m/%Y %H:%M')
        })

    return render_template('sales_history.html',
                           sales=sales_data,
                           page=page,
                           total_pages=sales.pages,
                           role=role)
