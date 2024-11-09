from flask import Blueprint, render_template
from models import Account, AccountValue
from datetime import datetime

summary_bp = Blueprint('summary_bp', __name__)

@summary_bp.route('/')
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
        "currency": account.currency
    } for account in accounts]

    # Retrieve and align account values
    account_values = AccountValue.query.order_by(AccountValue.date).all()
    unique_dates = sorted({value.date for value in account_values})

    # Prepare a dictionary to store the date-aligned values for each account
    account_data = {account.id: {} for account in accounts}
    for account in accounts:
        last_value = 0
        for date in unique_dates:
            # Carry forward last known value
            recorded_value = next((v.value for v in account_values if v.account_id == account.id and v.date == date), None)
            if recorded_value is not None:
                last_value = recorded_value
            account_data[account.id][date] = last_value

    # Convert date-aligned account data to a format suitable for JSON
    account_values_data = []
    for account_id, values in account_data.items():
        for date, value in values.items():
            account_values_data.append({
                "account_id": account_id,
                "date": date.isoformat(),
                "value": value
            })

    return render_template('summary.html', accounts=accounts_data, account_values=account_values_data)
