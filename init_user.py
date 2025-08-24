from app import app
from models import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User(username='admin', password=generate_password_hash('admin123'))
    db.session.add(admin)
    db.session.commit()
    print("Admin user berhasil ditambahkan.")
