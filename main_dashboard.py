from flask import render_template, render_template_string
from flask_login import login_required

import app


@app.route('/vhc')
@login_required
def main_dashboard():
    return render_template('main_dashboard.html')