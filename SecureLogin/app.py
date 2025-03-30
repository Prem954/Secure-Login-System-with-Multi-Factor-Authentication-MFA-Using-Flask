from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
import pyotp
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'thaparitik45@gmail.com'
app.config['MAIL_PASSWORD'] = 'fonq nams rtje bgtb'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.getcwd()), 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database, encryption, and login manager
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    otp_secret = db.Column(db.String(16), nullable=False, default=lambda: pyotp.random_base32())

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            session['email'] = email  # Store email for MFA verification
            return redirect(url_for('mfa'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

# MFA Route
@app.route('/mfa', methods=['GET', 'POST'])
def mfa():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(email=session['email']).first()
    
    if request.method == 'POST':
        otp = request.form['otp']
        totp = pyotp.TOTP(user.otp_secret)
        if totp.verify(otp):
            login_user(user)
            session.pop('email', None)  # Clear session after successful login
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid OTP. Try again.', 'danger')
    
    # Send OTP via email
    totp = pyotp.TOTP(user.otp_secret)
    otp_code = totp.now()
    msg = Message("Your MFA Code", sender="your_email@gmail.com", recipients=[user.email])
    msg.body = f"Your OTP code is: {otp_code}"
    mail.send(msg)
    
    return render_template('mfa.html')

# Dashboard Route
@app.route('/dashboard')
@login_required
def dashboard():
    return f'Welcome, {current_user.email}! You have logged in successfully.'

# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
def home():
    return redirect(url_for('login'))  # Redirect to login page


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created inside the app context
    app.run(debug=True)
