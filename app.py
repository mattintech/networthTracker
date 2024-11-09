from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
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
    account_number = db.Column(db.String(20), nullable=False)
    line_color = db.Column(db.String(7), nullable=True)
    
    # Define relationship to AccountValue
    values = db.relationship('AccountValue', backref='account', lazy=True)

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
    
    # Collect all unique dates
    unique_dates = sorted({value.date for value in account_values})
    
    # Prepare a dictionary to store the date-aligned values for each account
    account_data = {account.id: {} for account in accounts}
    
    # Fill in the dictionary with values, carrying forward the last known value
    for account in accounts:
        last_value = 0  # Default to 0 if no previous value
        for date in unique_dates:
            # Check if there is a value recorded on this date
            recorded_value = next((v.value for v in account_values if v.account_id == account.id and v.date == date), None)
            if recorded_value is not None:
                last_value = recorded_value  # Update last known value
            account_data[account.id][date] = last_value  # Carry forward the last known value

    # Prepare the accounts data for the template
    accounts_data = [{
        "id": account.id,
        "name": account.name,
        "type": account.type,
        "institution": account.institution,
        "owner": account.owner,
        "line_color": account.line_color,
    } for account in accounts]
    
    # Prepare the date-aligned data for each account for the template
    account_values_data = []
    for account_id, values in account_data.items():
        for date, value in values.items():
            account_values_data.append({
                "account_id": account_id,
                "date": date.isoformat(),
                "value": value
            })

    return render_template('summary.html', accounts=accounts_data, account_values=account_values_data)

@app.route('/accounts', methods=['GET', 'POST'])
def accounts():
    if request.method == 'POST':
        # Check if we're adding a new account or updating an existing one
        account_id = request.form.get('account_id')
        if account_id:
            # Update existing account
            account = Account.query.filter_by(id=account_id).first()  # Updated line
            if account:
                account.name = request.form['name']
                account.type = request.form['type']
                account.institution = request.form['institution']
                account.owner = request.form['owner']
                account.account_number = request.form['account_number']
                account.line_color = request.form['line_color']
                db.session.commit()
                flash('Account updated successfully')
        else:
            # Add a new account
            name = request.form['name']
            type_ = request.form['type']
            institution = request.form['institution']
            owner = request.form['owner']
            account_number = request.form['account_number']
            line_color = request.form['line_color']
            
            new_account = Account(name=name, type=type_, institution=institution, owner=owner,
                                  account_number=account_number, line_color=line_color)
            db.session.add(new_account)
            db.session.commit()
            flash('Account added successfully')
        return redirect(url_for('accounts'))

    # Retrieve all accounts to display in the table
    accounts = Account.query.all()
    return render_template('accounts.html', accounts=accounts)

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

@app.route('/get_account_values')
def get_account_values():
    # Retrieve all values sorted by date in descending order
    account_values = AccountValue.query.order_by(desc(AccountValue.date)).all()
    
    # Prepare data as JSON
    account_values_data = [{
        "account_name": value.account.name,
        "account_number": value.account.account_number,
        "institution": value.account.institution,
        "owner": value.account.owner,
        "value": f"${value.value:,.2f}",  # Format as dollar amount with two decimal places
        "date": value.date.isoformat()  # Move date to the end
    } for value in account_values]
    
    return jsonify(account_values_data)


if __name__ == '__main__':
    app.run(debug=True)
