from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Account, db

accounts_bp = Blueprint('accounts_bp', __name__)

@accounts_bp.route('/', methods=['GET', 'POST'])
def accounts():
    if request.method == 'POST':
        account_id = request.form.get('account_id')
        currency = request.form['currency']
        if account_id:
            account = Account.query.get(account_id)
            if account:
                account.name = request.form['name']
                account.type = request.form['type']
                account.institution = request.form['institution']
                account.owner = request.form['owner']
                account.account_number = request.form['account_number']
                account.line_color = request.form['line_color']
                account.currency = currency
                db.session.commit()
                flash('Account updated successfully')
        else:
            new_account = Account(
                name=request.form['name'],
                type=request.form['type'],
                institution=request.form['institution'],
                owner=request.form['owner'],
                account_number=request.form['account_number'],
                line_color=request.form['line_color'],
                currency=currency
            )
            db.session.add(new_account)
            db.session.commit()
            flash('Account added successfully')
        return redirect(url_for('accounts_bp.accounts'))

    accounts = Account.query.all()
    return render_template('accounts.html', accounts=accounts)