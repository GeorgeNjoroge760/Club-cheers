from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, Product, Category, StockMovement

inventory_bp = Blueprint('inventory', __name__)


def admin_required():
    return session.get('role') == 'admin'


@inventory_bp.route('/inventory')
def inventory():
    if not admin_required():
        return redirect(url_for('auth.admin_login'))
    products = Product.query.order_by(Product.category_id, Product.name).all()
    categories = Category.query.order_by(Category.sort_order).all()
    return render_template('inventory.html', products=products, categories=categories)


@inventory_bp.route('/inventory/product/add', methods=['GET', 'POST'])
def product_add():
    if not admin_required():
        return redirect(url_for('auth.admin_login'))
    categories = Category.query.order_by(Category.sort_order).all()
    if request.method == 'POST':
        product = Product(
            name=request.form.get('name'),
            category_id=int(request.form.get('category_id')),
            sell_price=float(request.form.get('sell_price')),
            cost_price=float(request.form.get('cost_price')) if request.form.get('cost_price') else None,
            stock_qty=float(request.form.get('stock_qty', 0)),
            unit=request.form.get('unit', 'unit')
        )
        db.session.add(product)

        if product.stock_qty > 0 and product.cost_price:
            movement = StockMovement(
                product_id=product.id,
                qty=product.stock_qty,
                type='stock_in',
                cost_per_unit=product.cost_price,
                note='Initial stock'
            )
            db.session.add(movement)

        db.session.commit()
        return redirect(url_for('inventory.inventory'))
    return render_template('product_form.html', categories=categories, product=None)


@inventory_bp.route('/inventory/product/edit/<int:product_id>', methods=['GET', 'POST'])
def product_edit(product_id):
    if not admin_required():
        return redirect(url_for('auth.admin_login'))
    product = Product.query.get_or_404(product_id)
    categories = Category.query.order_by(Category.sort_order).all()
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.category_id = int(request.form.get('category_id'))
        product.sell_price = float(request.form.get('sell_price'))
        product.cost_price = float(request.form.get('cost_price')) if request.form.get('cost_price') else None
        product.unit = request.form.get('unit', 'unit')
        db.session.commit()
        return redirect(url_for('inventory.inventory'))
    return render_template('product_form.html', categories=categories, product=product)


@inventory_bp.route('/inventory/product/toggle/<int:product_id>', methods=['POST'])
def product_toggle(product_id):
    if not admin_required():
        return redirect(url_for('auth.admin_login'))
    product = Product.query.get_or_404(product_id)
    product.active = not product.active
    db.session.commit()
    return redirect(url_for('inventory.inventory'))


@inventory_bp.route('/inventory/stock-in', methods=['GET', 'POST'])
def stock_in():
    if not admin_required():
        return redirect(url_for('auth.admin_login'))
    products = Product.query.filter_by(active=True).order_by(Product.name).all()
    if request.method == 'POST':
        product_id = int(request.form.get('product_id'))
        qty = float(request.form.get('qty'))
        cost_per_unit = float(request.form.get('cost_per_unit', 0))
        note = request.form.get('note', '')

        product = Product.query.get(product_id)
        product.stock_qty += qty
        if cost_per_unit > 0:
            product.cost_price = cost_per_unit

        movement = StockMovement(
            product_id=product_id,
            qty=qty,
            type='stock_in',
            cost_per_unit=cost_per_unit if cost_per_unit > 0 else None,
            note=note
        )
        db.session.add(movement)
        db.session.commit()
        return redirect(url_for('inventory.inventory'))
    return render_template('stock_in.html', products=products)


@inventory_bp.route('/inventory/category/add', methods=['POST'])
def category_add():
    if not admin_required():
        return redirect(url_for('auth.admin_login'))
    name = request.form.get('name')
    if name:
        Category(name=name).save()
        db.session.commit()
    return redirect(url_for('inventory.inventory'))
