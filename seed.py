from app import create_app
from models import db, Staff, Category, Product

app = create_app()

with app.app_context():
    db.create_all()

    if Staff.query.first():
        print("Database already seeded")
        exit()

    admin = Staff(name='admin', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)

    for name in ['Alice', 'Bob']:
        staff = Staff(name=name, role='attendant')
        staff.set_password('1234')
        db.session.add(staff)

    categories = ['Beer', 'Spirits', 'Wine', 'Soft Drinks', 'Snacks']
    for i, cat in enumerate(categories):
        db.session.add(Category(name=cat, sort_order=i))

    db.session.commit()

    beer = Category.query.filter_by(name='Beer').first()
    spirits = Category.query.filter_by(name='Spirits').first()
    soft = Category.query.filter_by(name='Soft Drinks').first()
    snacks = Category.query.filter_by(name='Snacks').first()

    products = [
        ('Tusker', beer.id, 250, 180, 50, 'bottle'),
        ('Tusker Lite', beer.id, 250, 180, 50, 'bottle'),
        ('White Cap', beer.id, 220, 160, 50, 'bottle'),
        ('Guinness', beer.id, 350, 260, 30, 'bottle'),
        ('Jameson', spirits.id, 400, 300, 20, 'measure'),
        ('Johnnie Walker', spirits.id, 450, 340, 20, 'measure'),
        ('Smirnoff', spirits.id, 300, 220, 25, 'measure'),
        ('Coke', soft.id, 100, 60, 100, 'bottle'),
        ('Sprite', soft.id, 100, 60, 100, 'bottle'),
        ('Soda Water', soft.id, 80, 45, 100, 'bottle'),
        ('Chips', snacks.id, 150, 100, 40, 'pack'),
        ('Groundnuts', snacks.id, 100, 60, 40, 'pack'),
    ]

    for name, cat_id, sell, cost, qty, unit in products:
        p = Product(name=name, category_id=cat_id, sell_price=sell,
                    cost_price=cost, stock_qty=qty, unit=unit)
        db.session.add(p)

    db.session.commit()
    print("Database seeded successfully!")
    print("Admin login: admin / admin123")
    print("Attendants: Alice (PIN: 1234), Bob (PIN: 1234)")
