from models import Account, AccountValue
from datetime import datetime

def inject_net_worth():
    account_values = AccountValue.query.order_by(AccountValue.date).all()
    unique_dates = sorted({value.date for value in account_values})
    accounts = Account.query.all()
    
    account_data = {account.id: {} for account in accounts}
    for account in accounts:
        last_value = 0
        for date in unique_dates:
            recorded_value = next((v.value for v in account_values if v.account_id == account.id and v.date == date), None)
            if recorded_value is not None:
                last_value = recorded_value
            account_data[account.id][date] = last_value

    total_net_worth = sum(account_data[account.id][unique_dates[-1]] for account in accounts if unique_dates) if unique_dates else 0

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
