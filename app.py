from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///networth.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the Account model
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    institution = db.Column(db.String(100), nullable=False)
    owner = db.Column(db.String(50), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)  # New field for account number
    line_color = db.Column(db.String(7), nullable=True)
    #background_color = db.Column(db.String(7), nullable=True)

# Define the AccountValue model
class AccountValue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float, nullable=False)

    # Ensure one entry per account per month
    __table_args__ = (db.UniqueConstraint('account_id', 'date', name='unique_account_month'),)

# Initialize the database
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return redirect(url_for('summary'))

@app.route('/summary')
def summary():
    accounts = Account.query.all()
    account_values = AccountValue.query.order_by(AccountValue.date).all()
    
    # Convert accounts and account_values to dictionaries for JSON serialization
    accounts_data = [{
        "id": account.id,
        "name": account.name,
        "type": account.type,
        "institution": account.institution,
        "owner": account.owner,
        "line_color": account.line_color,  # Include line color
        #"background_color": account.background_color  # Include background color
    } for account in accounts]
    
    account_values_data = [{
        "id": value.id,
        "account_id": value.account_id,
        "date": value.date.isoformat(),
        "value": value.value
    } for value in account_values]

        # Debugging prints
    #print("Accounts Data:", accounts_data)
    #print("Account Values Data:", account_values_data)

    return render_template('summary.html', accounts=accounts_data, account_values=account_values_data)

@app.route('/add_account', methods=['GET', 'POST'])
def add_account():
    if request.method == 'POST':
        name = request.form['name']
        type_ = request.form['type']
        institution = request.form['institution']
        owner = request.form['owner']
        account_number = request.form['account_number']
        line_color = request.form['line_color']
        #background_color = request.form['background_color']
        
        new_account = Account(name=name, type=type_, institution=institution, owner=owner,
                              account_number=account_number, line_color=line_color) #, background_color=background_color)
        db.session.add(new_account)
        db.session.commit()
        flash('Account added successfully')
        return redirect(url_for('summary'))
    return render_template('add_account.html')

@app.route('/add_value', methods=['GET', 'POST'])
def add_value():
    accounts = Account.query.all()
    if request.method == 'POST':
        account_id = request.form['account_id']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        value = float(request.form['value'])
        
        # Check for duplicate entry
        existing_value = AccountValue.query.filter_by(account_id=account_id, date=date).first()
        if existing_value:
            flash('Value for this account and month already exists.')
        else:
            new_value = AccountValue(account_id=account_id, date=date, value=value)
            db.session.add(new_value)
            db.session.commit()
            flash('Value added successfully')
        return redirect(url_for('summary'))
    return render_template('add_value.html', accounts=accounts)

if __name__ == '__main__':
    app.run(debug=True)
