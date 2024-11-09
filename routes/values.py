from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import desc
from models import Account, AccountValue, db
from datetime import datetime

values_bp = Blueprint('values_bp', __name__)

@values_bp.route('/', methods=['GET', 'POST'])
def values():
    accounts = Account.query.all()

    if request.method == 'POST':
        # Debugging output to check if we enter the POST request
        print("Received POST request on /values")

        # Retrieve form data for creating or updating an account value
        account_value_id = request.form.get('account_value_id')
        account_id = request.form.get('account_id_hidden') or request.form.get('account_id')
        date_str = request.form.get('date')
        value_str = request.form.get('value')
        
        # Debugging output for received form data
        print(f"Form Data - account_value_id: {account_value_id}, account_id: {account_id}, date: {date_str}, value: {value_str}")

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            value = float(value_str)
        except ValueError as e:
            print(f"Error parsing date or value: {e}")
            flash('Invalid date or value format. Please check your input.')
            return redirect(url_for('values_bp.values'))

        if account_value_id:
            # Update an existing account value
            account_value = AccountValue.query.get(account_value_id)
            if account_value:
                print(f"Updating account value with ID: {account_value_id}")
                account_value.date = date
                account_value.value = value
                db.session.commit()
                flash('Value updated successfully')
            else:
                print(f"No account value found with ID: {account_value_id}")
                flash('Error: Could not find the specified account value to update.')
        else:
            # Add a new value only if it doesn't exist for the same account and date
            existing_value = AccountValue.query.filter_by(account_id=account_id, date=date).first()
            if existing_value:
                print("A value for this account and month already exists.")
                flash('Value for this account and month already exists.')
            else:
                # Add a new value
                print(f"Adding new value for account_id: {account_id}, date: {date}, value: {value}")
                new_value = AccountValue(account_id=account_id, date=date, value=value)
                db.session.add(new_value)
                db.session.commit()
                flash('Value added successfully')

        return redirect(url_for('values_bp.values'))

    # Render template with accounts for selection
    return render_template('values.html', accounts=accounts)

@values_bp.route('/get_account_values')
def get_account_values():
    # Retrieve all values sorted by date in descending order
    account_values = AccountValue.query.order_by(desc(AccountValue.date)).all()
    account_values_data = [{
        "id": value.id,
        "account_id": value.account.id,
        "account_name": f"{value.account.owner} - {value.account.name} ({value.account.account_number[-4:]})",
        "account_number": value.account.account_number,
        "institution": value.account.institution,
        "owner": value.account.owner,
        "value": f"${value.value:,.2f}",
        "date": value.date.isoformat()
    } for value in account_values]

    return jsonify(account_values_data)
