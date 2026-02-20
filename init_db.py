from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    db.create_all()
    if not User.query.first():
        u = User(username='DemoUser', email='demo@example.com')
        u.set_password('password')
        db.session.add(u)
        db.session.commit()
        print('Database initialized.')
