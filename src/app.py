import os
from flask import Flask, redirect
from config import DevelopmentConfig, ProductionConfig
import models
from routes.accounts import accounts_bp
from routes.summary import summary_bp
from routes.values import values_bp
from utils.calculations import inject_net_worth

app = Flask(__name__)
config_class = DevelopmentConfig if os.getenv('FLASK_ENV') == 'development' else ProductionConfig
app.config.from_object(config_class)

models.init_db(app)

# Register blueprints
app.register_blueprint(accounts_bp, url_prefix='/accounts')
app.register_blueprint(summary_bp, url_prefix='/summary')
app.register_blueprint(values_bp, url_prefix='/values')

# Context processor for net worth calculation
app.context_processor(inject_net_worth)

@app.route('/')
def index():
    return redirect('/summary')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)