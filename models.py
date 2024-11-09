from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    print("DB Init")
    db.init_app(app)
    with app.app_context():
        db.create_all()

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    institution = db.Column(db.String(100), nullable=False)
    owner = db.Column(db.String(50), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    line_color = db.Column(db.String(7), nullable=True)
    currency = db.Column(db.String(3), nullable=False, default='USD')
    values = db.relationship('AccountValue', backref='account', lazy=True)

class AccountValue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float, nullable=False)
    __table_args__ = (db.UniqueConstraint('account_id', 'date', name='unique_account_month'),)
