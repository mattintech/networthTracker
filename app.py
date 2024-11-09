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

class AccountValue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float, nullable=False)
    __table_args__ = (db.UniqueConstraint('account_id', 'date', name='unique_account_month'),)

with app.app_context():
    db.create_all()

# Context processor to calculate total net worth and change
@app.context_processor
def inject_net_worth():
    account_values = AccountValue.query.order_by(AccountValue.date).all()
    unique_dates = sorted({value.date for value in account_values})
    accounts = Account.query.all()
    
    # Carry-forward logic for each account's values
    account_data = {account.id: {} for account in accounts}
    for account in accounts:
        last_value = 0
        for date in unique_dates:
            recorded_value = next((v.value for v in account_values if v.account_id == account.id and v.date == date), None)
            if recorded_value is not None:
                last_value = recorded_value
            account_data[account.id][date] = last_value

    # Calculate total net worth as the sum of each account's latest known value
    total_net_worth = sum(account_data[account.id][unique_dates[-1]] for account in accounts if unique_dates) if unique_dates else 0

    # Calculate net worth change between the last two dates
    net_worth_change = 0
    if len(unique_dates) > 1:
        last_month = unique_dates[-1]
        previous_month = unique_dates[-2]
        last_month_net_worth = sum(account_data[account.id][last_month] for account in accounts)
        previous_month_net_worth = sum(account_data[account.id][previous_month] for account in accounts)
        net_worth_change = last_month_net_worth - previous_month_net_worth

    return {
        'total_net_worth': total_net_worth,
        'net_worth_change': net_worth_change
    }

@app.route('/')
def index():
    return redirect(url_for('summary'))

@app.route('/summary')
def summary():
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
    for account in accounts:
        last_value = 0
        for date in unique_dates:
            recorded_value = next((v.value for v in account_values if v.account_id == account.id and v.date == date), None)
            if recorded_value is not None:
                last_value = recorded_value
            account_data[account.id][date] = last_value

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
    return render_template('accounts.html', accounts=accounts)

@app.route('/values', methods=['GET', 'POST'])
def values():
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

    return render_template('values.html', accounts=accounts)

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
