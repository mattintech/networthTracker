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
    values = db.relationship('AccountValue', backref='account', lazy=True)

# Define the AccountValue model
class AccountValue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float, nullable=False)
    __table_args__ = (db.UniqueConstraint('account_id', 'date', name='unique_account_month'),)

# Initialize the database
with app.app_context():
    db.create_all()

def calculate_net_worth_change():
    account_values = AccountValue.query.order_by(AccountValue.date).all()
    unique_dates = sorted({value.date for value in account_values})
    accounts = Account.query.all()
    
    account_data = {account.id: {} for account in accounts}
    
    # Populate account_data with carry-forward logic
    for account in accounts:
        last_value = 0  # Start with 0 if there's no prior value
        for date in unique_dates:
            recorded_value = next((v.value for v in account_values if v.account_id == account.id and v.date == date), None)
            if recorded_value is not None:
                last_value = recorded_value  # Update last known value if there's a recorded value
            account_data[account.id][date] = last_value  # Carry forward the last known value

    # Calculate net worth for each date
    monthly_net_worth = {date: sum(account_data[account.id][date] for account in accounts) for date in unique_dates}

    # Determine the change in net worth between the last two months
    net_worth_change = 0
    sorted_dates = sorted(monthly_net_worth.keys())
    if len(sorted_dates) > 1:
        last_month = sorted_dates[-1]
        previous_month = sorted_dates[-2]
        net_worth_change = monthly_net_worth[last_month] - monthly_net_worth[previous_month]

    return net_worth_change

@app.route('/')
def index():
    return redirect(url_for('summary'))

@app.route('/summary')
def summary():
    net_worth_change = calculate_net_worth_change()
    accounts = Account.query.all()
    
    # Prepare accounts data as dictionaries for JSON serialization
    accounts_data = [{
        "id": account.id,
        "name": account.name,
        "type": account.type,
        "institution": account.institution,
        "owner": account.owner,
        "line_color": account.line_color,
    } for account in accounts]
    
    account_values = AccountValue.query.order_by(AccountValue.date).all()
    unique_dates = sorted({value.date for value in account_values})
    
    account_data = {account.id: {} for account in accounts}
    
    # Carry-forward logic for each account's values across dates
    for account in accounts:
        last_value = 0  # Default to 0 if no previous value
        for date in unique_dates:
            recorded_value = next((v.value for v in account_values if v.account_id == account.id and v.date == date), None)
            if recorded_value is not None:
                last_value = recorded_value  # Update last known value
            account_data[account.id][date] = last_value  # Carry forward the last known value

    # Prepare account values for the template
    account_values_data = []
    for account_id, values in account_data.items():
        for date, value in values.items():
            account_values_data.append({
                "account_id": account_id,
                "date": date.isoformat(),
                "value": value
            })

    return render_template('summary.html', 
                           net_worth_change=net_worth_change, 
                           accounts=accounts_data, 
                           account_values=account_values_data)


@app.route('/accounts', methods=['GET', 'POST'])
def accounts():
    net_worth_change = calculate_net_worth_change()
    
    if request.method == 'POST':
        account_id = request.form.get('account_id')
        if account_id:
            account = Account.query.get(account_id)
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
            new_account = Account(
                name=request.form['name'],
                type=request.form['type'],
                institution=request.form['institution'],
                owner=request.form['owner'],
                account_number=request.form['account_number'],
                line_color=request.form['line_color']
            )
            db.session.add(new_account)
            db.session.commit()
            flash('Account added successfully')
        return redirect(url_for('accounts'))

    accounts = Account.query.all()
    return render_template('accounts.html', accounts=accounts, net_worth_change=net_worth_change)

@app.route('/values', methods=['GET', 'POST'])
def values():
    net_worth_change = calculate_net_worth_change()
    accounts = Account.query.all()
    
    if request.method == 'POST':
        account_value_id = request.form.get('account_value_id')
        account_id = request.form.get('account_id_hidden') or request.form.get('account_id')
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        value = float(request.form['value'])
        
        if account_value_id:
            account_value = AccountValue.query.get(account_value_id)
            if account_value:
                account_value.date = date
                account_value.value = value
                db.session.commit()
                flash('Value updated successfully')
        else:
            existing_value = AccountValue.query.filter_by(account_id=account_id, date=date).first()
            if existing_value:
                flash('Value for this account and month already exists.')
            else:
                new_value = AccountValue(account_id=account_id, date=date, value=value)
                db.session.add(new_value)
                db.session.commit()
                flash('Value added successfully')
        return redirect(url_for('values'))

    return render_template('values.html', accounts=accounts, net_worth_change=net_worth_change)

@app.route('/get_account_values')
def get_account_values():
    account_values = AccountValue.query.order_by(desc(AccountValue.date)).all()
    account_values_data = [{
        "id": value.id,
        "account_id": value.account.id,
        "account_name": value.account.name,
        "account_number": value.account.account_number,
        "institution": value.account.institution,
        "owner": value.account.owner,
        "value": f"${value.value:,.2f}",
        "date": value.date.isoformat()
    } for value in account_values]
    
    return jsonify(account_values_data)

if __name__ == '__main__':
    app.run(debug=True)
