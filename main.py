### Code work of the Real-Time project GrihaSeva ###

### Essential libraries for application

from flask import Flask, jsonify, render_template, request, redirect, url_for, g, session, flash
import mysql.connector
from decimal import Decimal
import os
import logging
import json
from flask_mail import Mail, Message
import secrets
from datetime import datetime, timedelta

### 

### App configuration, initialization and setup

app = Flask(__name__)
app.secret_key = os.urandom(24)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'nirmaldummy@gmail.com'  
app.config['MAIL_PASSWORD'] = 'Your 16 digit unique app code here'   
mail = Mail(app)

###

### Establishing database connection setup
def get_db_connection():
    if 'conn' not in g:
        try:
            g.conn = mysql.connector.connect(
                host="Host ID/IP",
                user="Your Database Username",
                password="Your Database Passoword",
                database="Your Database Name",
                auth_plugin='mysql_native_password'
            )
            g.cursor = g.conn.cursor(dictionary=True)
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None, None
    return g.conn, g.cursor

@app.teardown_appcontext
def close_db_connection(exception):
    conn = g.pop('conn', None)
    cursor = g.pop('cursor', None)
    if cursor:
        cursor.close()
    if conn:
        conn.close()

###

### User related routings
## Forget and Reset password
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        conn, cursor = get_db_connection()
        if not conn or not cursor:
            flash('Database connection error', 'error')
            return redirect(url_for('forgot_password'))

        try:
            cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
            user = cursor.fetchone()
            
            if user:
                token = secrets.token_urlsafe(32)
                expiry = datetime.now() + timedelta(hours=1)
                
                # Insert new token into password_reset_tokens table
                cursor.execute('INSERT INTO password_reset_tokens (user_id, token, expiry) VALUES (%s, %s, %s)',
                               (user['id'], token, expiry))
                conn.commit()
                
                reset_link = url_for('reset_password', token=token, _external=True)
                send_reset_email(email, reset_link)
                
                flash('Password reset link has been sent to your email.', 'success')
                return redirect(url_for('user_login'))
            else:
                flash('Email not found. Please check and try again.', 'error')
        except mysql.connector.Error as err:
            flash(f'An error occurred: {err}', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('forgot_password.html')

def send_reset_email(email, reset_link):
    msg = Message('Password Reset Request',
                  sender='noreply@yourdomain.com',
                  recipients=[email])
    msg.body = f'''To reset your password, visit the following link:
{reset_link}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        flash('Database connection error', 'error')
        return redirect(url_for('user_login'))

    try:
        # Join password_reset_tokens with users table to get user information
        cursor.execute('''
            SELECT u.id, u.email
            FROM password_reset_tokens t
            JOIN users u ON t.user_id = u.id
            WHERE t.token = %s AND t.expiry > NOW()
        ''', (token,))
        result = cursor.fetchone()
        
        if result:
            if request.method == 'POST':
                new_password = request.form.get('new_password')
                confirm_password = request.form.get('confirm_password')
                
                if new_password == confirm_password:
                    # Update user's password
                    cursor.execute('UPDATE users SET password = %s WHERE id = %s', 
                                   (new_password, result['id']))
                    # Delete the used token
                    cursor.execute('DELETE FROM password_reset_tokens WHERE token = %s', (token,))
                    conn.commit()
                    flash('Your password has been updated successfully.', 'success')
                    return redirect(url_for('user_login'))
                else:
                    flash('Passwords do not match. Please try again.', 'error')
            
            return render_template('reset_password.html', token=token)
        else:
            flash('Invalid or expired reset token. Please try again.', 'error')
            return redirect(url_for('forgot_password'))
    except mysql.connector.Error as err:
        flash(f'An error occurred: {err}', 'error')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('user_login'))
##
## User home and profile page after login
@app.route('/user-home')
def user_home():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    return render_template('user_home.html')

@app.route('/user-profile')
def user_profile():
    user = session.get('user')
    return render_template('user_profile.html', user = user)
##
## User login routing
@app.route('/user-login', methods=['GET', 'POST'])
def user_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn, cursor = get_db_connection()
        if not conn or not cursor:
            return "Database connection error", 500

        cursor.execute(
            "SELECT * FROM users WHERE username = %s AND password = %s",
            (username, password)
        )
        user = cursor.fetchone()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('user_home'))
        else:
            error = "Invalid username or password"
    return render_template('user_login.html', error=error)
##
## User registration routing
@app.route('/user-register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email') 
        password = request.form.get('password') 
        
        conn, cursor = get_db_connection()
        if not conn or not cursor:
            return "Database connection error", 500

        try:
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, password)
            )
            conn.commit()
            return redirect(url_for('user_login'))
        except mysql.connector.IntegrityError:
            return render_template('user_registration.html', error="Username or email already exists")
    return render_template('user_registration.html')
##
## User profile routing and updating password funtionality
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']
        
        conn.execute('UPDATE users SET name = ?, phone = ?, address = ? WHERE username = ?', 
                     (name, phone, address, session['username']))
        conn.commit()
        flash('Profile updated successfully!', 'success')

        conn.close()
        return redirect(url_for('profile'))
    return render_template('profile.html', user=user)

@app.route('/update_password', methods=['GET', 'POST'])
def update_password():
    if 'username' not in session:
        flash('You must be logged in to change your password.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            flash('All fields are required.', 'error')
            return redirect(url_for('update_password'))

        if new_password != confirm_password:
            flash('New passwords do not match. Please try again.', 'error')
            return redirect(url_for('update_password'))
        
        conn, cursor = get_db_connection()
        if not conn or not cursor:
            flash('Database connection error', 'error')
            return redirect(url_for('update_password'))

        try:
            cursor.execute('SELECT * FROM users WHERE username = %s', (session['username'],))
            user = cursor.fetchone()
            
            if user and current_password == user['password']:
                cursor.execute('UPDATE users SET password = %s WHERE username = %s', 
                               (new_password, session['username']))
                conn.commit()
                flash('Password updated successfully!', 'success')
            else:
                flash('Current password is incorrect. Please try again.', 'error')
        except mysql.connector.Error as err:
            flash(f'An error occurred: {err}', 'error')
        finally:
            cursor.close()
            conn.close()
    return render_template('user_profile.html', user = user)
##
## Book appointment functionality by user
@app.route('/book-appointment', methods=['GET', 'POST'])
def book_appointment():
    if 'username' not in session:
        flash('Please log in to book an appointment.', 'error')
        return redirect(url_for('user_login'))

    if request.method == 'POST':
        # Handle form submission and book the appointment
        date = request.form['date']
        time = request.form['time']
        service = request.form['service']
        provider = request.form.get('service-provider')
        notes = request.form['notes']
        username = session['username']  # Get the username from the session

        if not provider:
            flash('Please select a service provider.', 'error')
            return redirect(url_for('book_appointment', service=service))

        # Insert the appointment details into the database
        conn, cursor = get_db_connection()
        if not conn or not cursor:
            return "Database connection error", 500

        try:
            cursor.execute(
                "INSERT INTO appointments (date, time, service, provider, notes, username) VALUES (%s, %s, %s, %s, %s, %s)",
                (date, time, service, provider, notes, username)
            )
            conn.commit()
            flash('Appointment booked successfully!', 'success')
            return redirect(url_for('user_home'))
        except mysql.connector.Error as err:
            flash(f'An error occurred: {err}', 'error')
            return redirect(url_for('book_appointment', service=service))
        finally:
            cursor.close()
            conn.close()

    else:
        # Retrieve the list of available services
        services = get_available_services()

        # Retrieve the list of service providers based on the selected service
        selected_service = request.args.get('service')
        service_providers = get_service_providers(selected_service) if selected_service else []
        return render_template('user_book_appointment.html', services=services, service_providers=service_providers, selected_service=selected_service)
    
def get_available_services():
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return []

    try:
        cursor.execute("SELECT DISTINCT service_type FROM service_providers")
        services = [row['service_type'] for row in cursor.fetchall()]
        return services
    except mysql.connector.Error as err:
        flash(f'An error occurred: {err}', 'error')
        return []
    finally:
        cursor.close()
        conn.close()

def get_service_providers(service):
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return []

    try:
        cursor.execute(
            "SELECT name FROM service_providers WHERE service_type = %s",
            (service,)
        )
        service_providers = cursor.fetchall()
        return [provider['name'] for provider in service_providers]
    except mysql.connector.Error as err:
        flash(f'An error occurred: {err}', 'error')
        return []
    finally:
        cursor.close()
        conn.close()
        
@app.route('/get-providers/<service>', methods=['GET'])
def get_providers(service):
    providers = get_service_providers(service)
    return jsonify(providers)

def get_service_providers(service):
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return []

    try:
        cursor.execute(
            "SELECT name FROM service_providers WHERE service_type = %s",
            (service,)
        )
        return [row['name'] for row in cursor.fetchall()]
    except mysql.connector.Error as err:
        flash(f'An error occurred: {err}', 'error')
        return []
    finally:
        cursor.close()
        conn.close()

@app.route('/book-appointment-women-services', methods=['GET', 'POST'])
def book_appointment_women_services():
    if 'username' not in session:
        flash('Please log in to book an appointment.', 'error')
        return redirect(url_for('user_login'))
    
    if request.method == 'POST':
        # Handle form submission and book the appointment
        date = request.form['date']
        time = request.form['time']
        service = request.form['service']
        provider = request.form.get('women-service-provider')
        notes = request.form['notes']
        username = session['username']  # Get the username from the session
        
        if not provider:
            flash('Please select a service provider.', 'error')
            return redirect(url_for('book_appointment_women_services', service=service))
        
        # Insert the appointment details into the database
        conn, cursor = get_db_connection()
        if not conn or not cursor:
            return "Database connection error", 500
        
        try:
            cursor.execute(
                "INSERT INTO women_service_appointments (date, time, service, provider, notes, username) VALUES (%s, %s, %s, %s, %s, %s)",
                (date, time, service, provider, notes, username)
            )
            conn.commit()
            flash('Women services appointment booked successfully!', 'success')
            return redirect(url_for('user_home'))
        except mysql.connector.Error as err:
            flash(f'An error occurred: {err}', 'error')
            return redirect(url_for('book_appointment_women_services', service=service))
        finally:
            cursor.close()
            conn.close()
    
    else:
        # Retrieve the list of available women's services
        services = get_available_women_services()
        
        # Retrieve the list of women service providers based on the selected service
        selected_service = request.args.get('service')
        service_providers = get_women_service_providers(selected_service) if selected_service else []
        
        return render_template('user_book_appointmentw.html', services=services, service_providers=service_providers, selected_service=selected_service)

def get_available_women_services():
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return []
    
    try:
        cursor.execute("SELECT DISTINCT domain FROM women_service_providers")
        services = [row['domain'] for row in cursor.fetchall()]
        return services
    except mysql.connector.Error as err:
        flash(f'An error occurred: {err}', 'error')
        return []
    finally:
        cursor.close()
        conn.close()

def get_women_service_providers(service):
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        return []
    
    try:
        cursor.execute(
            "SELECT name, age FROM women_service_providers WHERE domain = %s",
            (service,)
        )
        return [{'name': row['name'], 'age': row['age']} for row in cursor.fetchall()]
    except mysql.connector.Error as err:
        flash(f'An error occurred: {err}', 'error')
        return []
    finally:
        cursor.close()
        conn.close()

@app.route('/get-women-service-providers/<service>', methods=['GET'])
def get_women_providers(service):
    providers = get_women_service_providers(service)
    return jsonify(providers)
##
## User bookings routing
@app.route('/my-bookings')
def my_bookings():
    return render_template('my_bookings.html')

@app.route('/api/my-bookings')
def api_my_bookings():
    logging.debug("Entering api_my_bookings function")
    conn, cursor = None, None
    try:
        conn, cursor = get_db_connection()
        if not conn or not cursor:
            logging.error("Failed to establish a database connection.")
            return jsonify({"error": "Database connection error"}), 500

        username = session.get('username')
        if not username:
            logging.warning("User is not logged in.")
            return jsonify({"error": "User not logged in"}), 401

        logging.debug(f"Username passed to query: {username}")

        # Query for regular appointments
        regular_query = """
            SELECT service, provider AS name, date, time, 'regular' AS booking_type 
            FROM appointments 
            WHERE username = %s 
        """
        cursor.execute(regular_query, (username,))
        regular_bookings = cursor.fetchall()

        # Query for women's services appointments
        women_query = """
            SELECT service, provider AS name, date, time, 'women_services' AS booking_type 
            FROM women_service_appointments 
            WHERE username = %s 
        """
        cursor.execute(women_query, (username,))
        women_bookings = cursor.fetchall()

        # Combine and sort all bookings
        all_bookings = regular_bookings + women_bookings
        all_bookings.sort(key=lambda x: (x['date'], x['time']), reverse=True)

        if all_bookings:
            bookings = []
            for row in all_bookings:
                bookings.append({
                    "service": row["service"],
                    "name": row["name"],
                    "date": row["date"].strftime('%Y-%m-%d'),
                    "time": str(row["time"]),
                    "booking_type": row["booking_type"]
                })
            logging.debug(f"Bookings fetched: {bookings}")
            return jsonify({"bookings": bookings})
        else:
            logging.info("No bookings found for the user.")
            return jsonify({"message": "No bookings found"}), 200
    except Exception as e:
        logging.exception("An unexpected error occurred.")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logging.debug("Exiting api_my_bookings function")

@app.route('/api/cancel-booking', methods=['POST'])
def cancel_booking():
    logging.debug("Entering cancel_booking function")
    conn, cursor = None, None
    try:
        conn, cursor = get_db_connection()
        if not conn or not cursor:
            logging.error("Failed to establish a database connection.")
            return jsonify({"error": "Database connection error"}), 500

        data = request.get_json()
        date = data.get('date')
        time = data.get('time')
        booking_type = data.get('booking_type')
        username = session.get('username')

        if not username:
            logging.warning("User is not logged in.")
            return jsonify({"error": "User not logged in"}), 401

        logging.debug(f"Cancelling {booking_type} booking for user: {username} on {date} at {time}")

        if booking_type == 'regular':
            table = 'appointments'
        elif booking_type == 'women_services':
            table = 'women_services_appointments'
        else:
            return jsonify({"error": "Invalid booking type"}), 400

        query = f"""
            DELETE FROM {table} 
            WHERE username = %s AND date = %s AND time = %s
        """
        cursor.execute(query, (username, date, time))
        conn.commit()

        if cursor.rowcount > 0:
            logging.info(f"{booking_type.capitalize()} booking cancelled for user: {username}")
            return jsonify({"success": True}), 200
        else:
            logging.warning("No matching booking found to cancel.")
            return jsonify({"success": False, "message": "No matching booking found"}), 404
    except Exception as e:
        logging.exception("An unexpected error occurred.")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logging.debug("Exiting cancel_booking function")
##
###

### General routings for Web Application
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/tos')
def tos():
    return render_template('termsandservices.html')

@app.route('/deciding')
def deciding():
    return render_template('deciding.html')

@app.route('/blogs')
def blogs():
    return render_template('blogs.html')

@app.route('/blog1')
def blog1():
    return render_template('blog1.html')

@app.route('/blog2')
def blog2():
    return render_template('blog2.html')

@app.route('/blog3')
def blog3():
    return render_template('blog3.html')

@app.route('/blog4')
def blog4():
    return render_template('blog4.html')

@app.route('/blog5')
def blog5():
    return render_template('blog5.html')

@app.route('/blog6')
def blog6():
    return render_template('blog6.html')

@app.route('/blog7')
def blog7():
    return render_template('blog7.html')

@app.route('/blog8')
def blog8():
    return render_template('blog8.html')

@app.route('/women')
def women():
    return render_template('women.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('provider_id', None)
    session.pop('username', None)
    return redirect(url_for('home'))
###

### Service provider related routings
## home page after login and login page, registration page routings
@app.route('/provider-home')
def provider_home():
    if 'provider_id' not in session:
        return redirect(url_for('provider_login'))
    return render_template('provider_home.html')

@app.route('/provider-login', methods=['GET', 'POST'])
def provider_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn, cursor = get_db_connection()
        if not conn or not cursor:
            return "Database connection error", 500

        cursor.execute(
            "SELECT * FROM service_providers WHERE username = %s AND password = %s",
            (username, password)
        )
        provider = cursor.fetchone()

        if provider:
            session['provider_id'] = provider['id']
            session['username'] = provider['username']
            return redirect(url_for('provider_home'))
        else:
            error = "Invalid username or password"
    return render_template('provider_login.html', error=error)

@app.route('/provider-register', methods=['GET', 'POST'])
def provider_register():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')  
        service_type = request.form.get('service_type') 
        
        conn, cursor = get_db_connection()
        if not conn or not cursor:
            return "Database connection error", 500

        try:
            cursor.execute(
                "INSERT INTO service_providers (name, username, password, email, service_type) VALUES (%s, %s, %s, %s, %s)",
                (name, username, password, email, service_type)
            )
            conn.commit()
            return redirect(url_for('provider_login'))
        except mysql.connector.IntegrityError:
            return render_template('provider_registration.html', error="Username or email already exists")
    return render_template('provider_registration.html')
##
## Service provider profile page routing & update password functionality
@app.route('/provider-profile', methods=['GET', 'POST'])
def provider_profile():
    if 'username' not in session:
        flash('Please log in to access your profile.', 'error')
        return redirect(url_for('provider_login'))

    conn, cursor = get_db_connection()
    if not conn or not cursor:
        flash('Database connection error. Please try again later.', 'error')
        return render_template('provider_profile.html')
    provider = None
    try:
        # Fetch provider details
        cursor.execute('SELECT * FROM provider_details WHERE provider_username = %s', (session['username'],))
        provider = cursor.fetchone()

        if request.method == 'POST':
            name = request.form.get('name')
            phone = request.form.get('phone')
            address = request.form.get('address')

            if provider:
                # Update existing details
                cursor.execute('UPDATE provider_details SET name = %s, phone = %s, address = %s WHERE provider_username = %s',
                               (name, phone, address, session['username']))
            else:
                # Insert new details
                cursor.execute('INSERT INTO provider_details (provider_username, name, phone, address) VALUES (%s, %s, %s, %s)',
                               (session['username'], name, phone, address))
            
            conn.commit()
            flash('Profile updated successfully!', 'success')
            
            # Fetch updated details
            cursor.execute('SELECT * FROM provider_details WHERE provider_username = %s', (session['username'],))
            provider = cursor.fetchone()

    except mysql.connector.Error as err:
        conn.rollback()
        flash(f'An error occurred: {err}', 'error')
    finally:
        cursor.close()
        conn.close()
    return render_template('provider_profile.html', provider=provider)

@app.route('/provider_update_password', methods=['GET', 'POST'])
def provider_update_password():
    if 'username' not in session:
        flash('You must be logged in to change your password.', 'error')
        return redirect(url_for('provider_login'))

    provider = None
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not all([current_password, new_password, confirm_password]):
            flash('All fields are required.', 'error')
            return redirect(url_for('provider_update_password'))

        if new_password != confirm_password:
            flash('New passwords do not match. Please try again.', 'error')
            return redirect(url_for('provider_update_password'))

        conn, cursor = get_db_connection()
        if not conn or not cursor:
            flash('Database connection error', 'error')
            return redirect(url_for('provider_update_password'))

        try:
            cursor.execute('SELECT * FROM service_providers WHERE username = %s', (session['username'],))
            provider = cursor.fetchone()

            if provider:
                stored_password = provider['password']
                if current_password == stored_password:
                    cursor.execute('UPDATE service_providers SET password = %s WHERE username = %s', 
                                   (new_password, session['username']))
                    conn.commit()
                    flash('Password updated successfully!', 'success')
                else:
                    flash('Current password is incorrect. Please try again.', 'error')
            else:
                flash('Provider not found.', 'error')

        except mysql.connector.Error as err:
            conn.rollback()
            flash(f'An error occurred: {err}', 'error')
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    return render_template('provider_profile.html', provider=provider)
##
## provider booking functionality
@app.route('/provider-bookings')
def provider_bookings():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('provider_bookings.html')

@app.route('/api/provider-bookings')
def api_provider_bookings():
    logging.info("Entering api_provider_bookings function")
    conn, cursor = None, None
    try:
        # Log the entire session data to ensure the username is set
        logging.info(f"Session data: {session.items()}")

        conn, cursor = get_db_connection()
        if not conn or not cursor:
            logging.error("Failed to establish a database connection.")
            return jsonify({"error": "Database connection error"}), 500

        username = session.get('username')
        logging.info(f"Provider username from session: {username}")
        if not username:
            logging.warning("User is not logged in.")
            return jsonify({"error": "User not logged in"}), 401

        # Check if the provider exists in the service_providers table
        check_provider_query = "SELECT * FROM service_providers WHERE username = %s"
        cursor.execute(check_provider_query, (username,))
        provider = cursor.fetchone()

        if not provider:
            logging.warning(f"No provider found with username: {username}")
            return jsonify({"error": "Provider not found"}), 404

        logging.info(f"Provider found: {provider}")

        # Fetch the bookings for the provider
        query = """
            SELECT * FROM appointments 
            WHERE provider = %s 
            ORDER BY date DESC, time DESC
        """
        cursor.execute(query, (provider['name'],))
        rows = cursor.fetchall()

        logging.info(f"Query executed. Number of rows returned: {len(rows)}")

        if rows:
            bookings = []
            for row in rows:
                # Log the raw row data to see exactly what is being fetched
                logging.info(f"Raw row data: {row}")

                # Ensure that the client's username is correctly extracted
                client_username = row.get('username', 'Unknown Client')
                if client_username == 'Unknown Client':
                    logging.warning(f"Client username missing for booking ID: {row['id']}")

                # Build the booking dictionary
                booking = {
                    "id": row['id'],
                    "date": row['date'].strftime('%Y-%m-%d'),
                    "time": str(row['time']),
                    "service": row['service'],
                    "provider": row['provider'],
                    "notes": row.get('notes', ''),
                    "client_username": client_username
                }
                bookings.append(booking)
                logging.info(f"Processed booking: {json.dumps(booking)}")

            logging.info(f"Bookings fetched for provider: {json.dumps(bookings, indent=2)}")
            return jsonify({"bookings": bookings})
        else:
            logging.info(f"No bookings found for the provider: {username}")
            return jsonify({"message": "No bookings found"}), 200
    except Exception as e:
        logging.exception(f"An unexpected error occurred in provider bookings: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logging.info("Exiting api_provider_bookings function")
##
## provider earning functionality
@app.route('/provider-earnings', methods=['GET', 'POST'])
def display_earnings():
    conn, cursor = get_db_connection()
    username = session.get('username')  # Get provider username from session

    if not username:
        print("Provider name is not set in session.")
        return "Error: Provider name is not set in session."

    # Handle POST request to calculate and add earnings
    if request.method == 'POST':
        try:
            hourly_charge = float(request.form['hourlyCharge'])  # Get hourly charge
            hours_worked = float(request.form['hoursWorked'])  # Get hours worked
            session_earnings = Decimal(hourly_charge * hours_worked)  # Calculate session earnings

            # Check if provider already has an entry
            query = "SELECT earnings FROM provider_earnings WHERE provider_name = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()

            if result:
                # Convert existing earnings to Decimal and update
                existing_earnings = Decimal(result['earnings'])
                total_earnings = existing_earnings + session_earnings
                update_query = "UPDATE provider_earnings SET earnings = %s WHERE provider_name = %s"
                cursor.execute(update_query, (total_earnings, username))
            else:
                # Insert new entry for the provider
                total_earnings = session_earnings
                insert_query = "INSERT INTO provider_earnings (provider_name, earnings) VALUES (%s, %s)"
                cursor.execute(insert_query, (username, total_earnings))
            
            conn.commit()

            # Redirect to display updated earnings
            return redirect(url_for('display_earnings'))

        except Exception as e:
            print(f"An error occurred: {e}")
            return "Error processing your request.", 500

    # Handle GET request to display the earnings page
    query = "SELECT earnings FROM provider_earnings WHERE provider_name = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()

    if result and 'earnings' in result:
        total_earnings = Decimal(result['earnings'])
    else:
        total_earnings = Decimal('0.00')  # Default if no record is found

    # Render the earnings page with total earnings
    return render_template('provider_earnings.html', total_earnings=total_earnings)
##
## provider forget and reset password functionality
@app.route('/provider-forgot-password', methods=['GET', 'POST'])
def provider_forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        conn, cursor = get_db_connection()
        if not conn or not cursor:
            flash('Database connection error', 'error')
            return redirect(url_for('provider_forgot_password'))

        try:
            cursor.execute('SELECT id FROM service_providers WHERE email = %s', (email,))
            provider = cursor.fetchone()
            
            if provider:
                token = secrets.token_urlsafe(32)
                expiry = datetime.now() + timedelta(hours=1)
                
                # Insert new token into provider_password_reset_tokens table
                cursor.execute('INSERT INTO provider_password_reset_tokens (provider_id, token, expiry) VALUES (%s, %s, %s)',
                               (provider['id'], token, expiry))
                conn.commit()
                
                reset_link = url_for('provider_reset_password', token=token, _external=True)
                send_provider_reset_email(email, reset_link)
                
                flash('Password reset link has been sent to your email.', 'success')
                return redirect(url_for('provider_login'))
            else:
                flash('Email not found. Please check and try again.', 'error')
        except mysql.connector.Error as err:
            flash(f'An error occurred: {err}', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('provider_forgot_password.html')

def send_provider_reset_email(email, reset_link):
    msg = Message('Service Provider Password Reset Request',
                  sender='nirmaldummy@gmail.com',
                  recipients=[email])
    msg.body = f'''To reset your service provider password, visit the following link:
{reset_link}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

@app.route('/provider-reset-password/<token>', methods=['GET', 'POST'])
def provider_reset_password(token):
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        flash('Database connection error', 'error')
        return redirect(url_for('provider_login'))

    try:
        # Join provider_password_reset_tokens with service_providers table to get provider information
        cursor.execute('''
            SELECT sp.id, sp.email
            FROM provider_password_reset_tokens t
            JOIN service_providers sp ON t.provider_id = sp.id
            WHERE t.token = %s AND t.expiry > NOW()
        ''', (token,))
        result = cursor.fetchone()
        
        if result:
            if request.method == 'POST':
                new_password = request.form.get('new_password')
                confirm_password = request.form.get('confirm_password')
                
                if new_password == confirm_password:
                    # Update provider's password
                    cursor.execute('UPDATE service_providers SET password = %s WHERE id = %s', 
                                   (new_password, result['id']))
                    # Delete the used token
                    cursor.execute('DELETE FROM provider_password_reset_tokens WHERE token = %s', (token,))
                    conn.commit()
                    flash('Your password has been updated successfully.', 'success')
                    return redirect(url_for('provider_login'))
                else:
                    flash('Passwords do not match. Please try again.', 'error')
            
            return render_template('provider_reset_password.html', token=token)
        else:
            flash('Invalid or expired reset token. Please try again.', 'error')
            return redirect(url_for('provider_forgot_password'))
    except mysql.connector.Error as err:
        flash(f'An error occurred: {err}', 'error')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('provider_login'))
###

### Women service provider related routings and functionalities
@app.route('/women-provider-register', methods=['GET', 'POST'])
def women_provider_register():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        email = request.form.get('email')
        domain = request.form.get('domain')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        age = request.form.get('age')
        gov_id = request.form.get('gov_id')
        
        conn, cursor = get_db_connection()
        if not conn or not cursor:
            return "Database connection error", 500
        
        try:
            # Insert new provider into the women_service_providers table
            cursor.execute(
                "INSERT INTO women_service_providers (name, username, email, domain, phone, password, age, gov_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (name, username, email, domain, phone, password, age, gov_id)
            )
            conn.commit()
            return redirect(url_for('women_login'))
        except mysql.connector.Error as err:
            return render_template('women_provider_registration.html', error = "Username or email already exists.")
    
    return render_template('women_provider_registration.html')

@app.route('/women-home')
def women_home():
    # Check if the user is logged in and has the correct role
    if 'username' not in session or session.get('user_role') != 'women_provider':
        return redirect(url_for('women_login'))  # Redirect to login if not logged in or incorrect user role
    
    # Pass the username to the template
    return render_template('women_home.html', username=session['username'])

@app.route('/women-login', methods=['GET', 'POST'])
def women_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Get DB connection
        conn, cursor = get_db_connection()
        if not conn or not cursor:
            return "Database connection error", 500

        # Use dictionary cursor
        cursor = conn.cursor(dictionary=True)
        
        # Query to check user credentials
        cursor.execute(
            "SELECT * FROM women_service_providers WHERE username = %s AND password = %s",
            (username, password)
        )
        provider = cursor.fetchone()

        # If provider exists, set session variables
        if provider:
            session['provider_id'] = provider['id']
            session['username'] = provider['username']
            session['user_role'] = 'women_provider'  # Set user role for women service provider
            return redirect(url_for('women_home'))
        else:
            error = "Invalid username or password"

    return render_template('women_login.html', error=error)

@app.route('/women-provider-profile', methods=['GET', 'POST'])
def women_provider_profile():
    if 'username' not in session:
        flash('Please log in to access your profile.', 'error')
        return redirect(url_for('women_provider_login'))

    conn, cursor = get_db_connection()
    if not conn or not cursor:
        flash('Database connection error. Please try again later.', 'error')
        return render_template('women_provider_profile.html')
    
    provider = None
    try:
        cursor.execute('SELECT * FROM women_service_providers WHERE username = %s', (session['username'],))
        provider = cursor.fetchone()

        if request.method == 'POST':
            name = request.form.get('name')
            phone = request.form.get('phone')
            address = request.form.get('address')

            if provider:
                cursor.execute('UPDATE women_service_providers SET name = %s, phone = %s, address = %s WHERE username = %s',
                               (name, phone, address, session['username']))
            else:
                cursor.execute('INSERT INTO women_service_providers (username, name, phone, address) VALUES (%s, %s, %s, %s)',
                               (session['username'], name, phone, address))
            conn.commit()
            flash('Profile updated successfully!', 'success')
            
            cursor.execute('SELECT * FROM women_service_providers WHERE username = %s', (session['username'],))
            provider = cursor.fetchone()

    except mysql.connector.Error as err:
        conn.rollback()
        flash(f'An error occurred: {err}', 'error')
    finally:
        cursor.close()
        conn.close()

    return render_template('women_provider_profile.html', provider=provider)

@app.route('/women-provider-update-password', methods=['GET', 'POST'])
def women_provider_update_password():
    if 'username' not in session:
        flash('You must be logged in to change your password.', 'error')
        return redirect(url_for('women_provider_login'))

    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not all([current_password, new_password, confirm_password]):
            flash('All fields are required.', 'error')
            return redirect(url_for('women_provider_update_password'))

        if new_password != confirm_password:
            flash('New passwords do not match. Please try again.', 'error')
            return redirect(url_for('women_provider_update_password'))

        conn, cursor = get_db_connection()
        if not conn or not cursor:
            flash('Database connection error', 'error')
            return redirect(url_for('women_provider_update_password'))

        try:
            cursor.execute('SELECT * FROM women_service_providers WHERE username = %s', (session['username'],))
            provider = cursor.fetchone()

            if provider:
                stored_password = provider['password']
                if current_password == stored_password:
                    cursor.execute('UPDATE women_service_providers SET password = %s WHERE username = %s', 
                                   (new_password, session['username']))
                    conn.commit()
                    flash('Password updated successfully!', 'success')
                else:
                    flash('Current password is incorrect. Please try again.', 'error')
            else:
                flash('Provider not found.', 'error')

        except mysql.connector.Error as err:
            conn.rollback()
            flash(f'An error occurred: {err}', 'error')
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    return render_template('women_provider_profile.html', provider = provider)

@app.route('/women-provider-bookings')
def women_provider_bookings():
    if 'username' not in session:
        return redirect(url_for('women_provider_login'))
    return render_template('women_provider_bookings.html')

@app.route('/api/women-provider-bookings')
def api_women_provider_bookings():
    logging.info("Entering api_women_provider_bookings function")
    conn, cursor = None, None
    try:
        # Log the entire session data to ensure the username is set
        logging.info(f"Session data: {session.items()}")

        conn, cursor = get_db_connection()
        if not conn or not cursor:
            logging.error("Failed to establish a database connection.")
            return jsonify({"error": "Database connection error"}), 500

        username = session.get('username')
        logging.info(f"Provider username from session: {username}")
        if not username:
            logging.warning("User is not logged in.")
            return jsonify({"error": "User not logged in"}), 401

        # Check if the provider exists in the service_providers table
        check_provider_query = "SELECT * FROM women_service_providers WHERE username = %s"
        cursor.execute(check_provider_query, (username,))
        provider = cursor.fetchone()

        if not provider:
            logging.warning(f"No provider found with username: {username}")
            return jsonify({"error": "Provider not found"}), 404

        logging.info(f"Provider found: {provider}")

        # Fetch the bookings for the provider
        query = """
            SELECT * FROM women_service_appointments 
            WHERE provider = %s 
            ORDER BY date DESC, time DESC
        """
        cursor.execute(query, (provider['name'],))
        rows = cursor.fetchall()

        logging.info(f"Query executed. Number of rows returned: {len(rows)}")

        if rows:
            bookings = []
            for row in rows:
                # Log the raw row data to see exactly what is being fetched
                logging.info(f"Raw row data: {row}")

                # Ensure that the client's username is correctly extracted
                client_username = row.get('username', 'Unknown Client')
                if client_username == 'Unknown Client':
                    logging.warning(f"Client username missing for booking ID: {row['id']}")

                # Build the booking dictionary
                booking = {
                    "id": row['id'],
                    "date": row['date'].strftime('%Y-%m-%d'),
                    "time": str(row['time']),
                    "service": row['service'],
                    "provider": row['provider'],
                    "notes": row.get('notes', ''),
                    "client_username": client_username
                }
                bookings.append(booking)
                logging.info(f"Processed booking: {json.dumps(booking)}")

            logging.info(f"Bookings fetched for provider: {json.dumps(bookings, indent=2)}")
            return jsonify({"bookings": bookings})
        else:
            logging.info(f"No bookings found for the provider: {username}")
            return jsonify({"message": "No bookings found"}), 200
    except Exception as e:
        logging.exception(f"An unexpected error occurred in women provider bookings: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logging.info("Exiting api_women_provider_bookings function")

@app.route('/women-provider-earnings', methods=['GET', 'POST'])
def women_provider_earnings():
    conn, cursor = get_db_connection()
    username = session.get('username')  # Get provider username from session

    if not username:
        print("Provider name is not set in session.")
        return "Error: Provider name is not set in session."

    # Handle POST request to calculate and add earnings
    if request.method == 'POST':
        try:
            hourly_charge = float(request.form['hourlyCharge'])  # Get hourly charge
            hours_worked = float(request.form['hoursWorked'])  # Get hours worked
            session_earnings = Decimal(hourly_charge * hours_worked)  # Calculate session earnings

            # Check if provider already has an entry
            query = "SELECT earnings FROM women_provider_earnings WHERE provider_name = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()

            if result:
                # Convert existing earnings to Decimal and update
                existing_earnings = Decimal(result['earnings'])
                total_earnings = existing_earnings + session_earnings
                update_query = "UPDATE women_provider_earnings SET earnings = %s WHERE provider_name = %s"
                cursor.execute(update_query, (total_earnings, username))
            else:
                # Insert new entry for the provider
                total_earnings = session_earnings
                insert_query = "INSERT INTO women_provider_earnings (provider_name, earnings) VALUES (%s, %s)"
                cursor.execute(insert_query, (username, total_earnings))
            
            conn.commit()

            # Redirect to display updated earnings
            return redirect(url_for('women_provider_earnings'))

        except Exception as e:
            print(f"An error occurred: {e}")
            return "Error processing your request.", 500

    # Handle GET request to display the earnings page
    query = "SELECT earnings FROM women_provider_earnings WHERE provider_name = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()

    if result and 'earnings' in result:
        total_earnings = Decimal(result['earnings'])
    else:
        total_earnings = Decimal('0.00')  # Default if no record is found

    # Render the earnings page with total earnings
    return render_template('women_provider_earnings.html', total_earnings=total_earnings)

@app.route('/women-forgot-password', methods=['GET', 'POST'])
def women_forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        conn, cursor = get_db_connection()
        if not conn or not cursor:
            flash('Database connection error', 'error')
            return redirect(url_for('women_forgot_password'))
        
        try:
            cursor.execute('SELECT id FROM women_service_providers WHERE email = %s', (email,))
            provider = cursor.fetchone()
            
            if provider:
                token = secrets.token_urlsafe(32)
                expiry = datetime.now() + timedelta(hours=1)
                
                cursor.execute('INSERT INTO women_password_reset_tokens (provider_id, token, expiry) VALUES (%s, %s, %s)',
                               (provider['id'], token, expiry))
                conn.commit()
                
                reset_link = url_for('women_reset_password', token=token, _external=True)
                send_reset_email(email, reset_link)
                
                flash('Password reset link has been sent to your email.', 'success')
                return redirect(url_for('women_login'))
            else:
                flash('Email not found. Please check and try again.', 'error')
        except mysql.connector.Error as err:
            flash(f'An error occurred: {err}', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('women_forgot_password.html')

def send_reset_email(email, reset_link):
    msg = Message('Password Reset Request',
                  sender='nirmaldummy@gmail.com',
                  recipients=[email])
    msg.body = f'''To reset your password, visit the following link: {reset_link}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

@app.route('/women-reset-password/<token>', methods=['GET', 'POST'])
def women_reset_password(token):
    conn, cursor = get_db_connection()
    if not conn or not cursor:
        flash('Database connection error', 'error')
        return redirect(url_for('women_login'))
    
    try:
        # Join women_password_reset_tokens with women_service_providers table to get provider information
        cursor.execute('''
            SELECT wsp.id, wsp.email
            FROM women_password_reset_tokens t
            JOIN women_service_providers wsp ON t.provider_id = wsp.id
            WHERE t.token = %s AND t.expiry > NOW()
        ''', (token,))
        result = cursor.fetchone()
        
        if result:
            if request.method == 'POST':
                new_password = request.form.get('new_password')
                confirm_password = request.form.get('confirm_password')
                
                if new_password == confirm_password:
                    # Update provider's password
                    cursor.execute('UPDATE women_service_providers SET password = %s WHERE id = %s',
                                   (new_password, result['id']))
                    # Delete the used token
                    cursor.execute('DELETE FROM women_password_reset_tokens WHERE token = %s', (token,))
                    conn.commit()
                    flash('Your password has been updated successfully.', 'success')
                    return redirect(url_for('women_login'))
                else:
                    flash('Passwords do not match. Please try again.', 'error')
            
            return render_template('women_reset_password.html', token=token)
        else:
            flash('Invalid or expired reset token. Please try again.', 'error')
            return redirect(url_for('women_forgot_password'))
    except mysql.connector.Error as err:
        flash(f'An error occurred: {err}', 'error')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('women_login'))
###

### App running command
if __name__ == '__main__':
    app.run(debug=True)
###

###
                     ### End ###
#######################################################
