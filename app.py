from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import joblib
import mysql.connector
from passlib.hash import bcrypt

app = Flask(__name__)

# Load the recipe dataset into a DataFrame
#recipe_data = pd.read_csv('data/recipes.csv')

# MySQL Database Configuration
db_config = {
    'host': 'localhost',
    'user': 'admin',
    'password': '12345',
    'database': 'recipe_recommender_db',
}

# Load the machine learning recommendation model
#recommendation_model = joblib.load('models/recommendation_model.pkl')

# Home page
@app.route('/')
def index():
    # Implement logic to show recommended recipes based on user profile and interactions
    # Pass the recommended recipes to the 'index.html' template
    recommended_recipes = []
    return render_template('index.html', recommended_recipes=recommended_recipes)

# User registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get user input from the registration form
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Perform basic validation
        if not username or not email or not password:
            error_message = "Please fill out all the fields."
            return render_template('register.html', error_message=error_message)

        # Hash the password using passlib
        hashed_password = bcrypt.hash(password)

        # Connect to the MySQL database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        try:
            # Check if the user already exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE email=%s", (email,))
            user_count = cursor.fetchone()[0]

            if user_count > 0:
                error_message = "Email already registered. Please log in."
                return render_template('register.html', error_message=error_message)

            # If the user does not exist, insert the new user into the database
            sql = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
            cursor.execute(sql, (username, email, hashed_password))
            connection.commit()

        except Exception as e:
            print("Error:", e)
            connection.rollback()
            error_message = "An error occurred during registration. Please try again later."
            return render_template('register.html', error_message=error_message)

        finally:
            # Close the database connection
            cursor.close()
            connection.close()

        # Redirect the user to the home page or login page after successful registration
        return redirect(url_for('index'))

    return render_template('register.html')

# User login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get user input from the login form
        email = request.form.get('email')
        password = request.form.get('password')

        # Connect to the MySQL database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        try:
            # Check if the user exists in the database
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user_data = cursor.fetchone()

            if not user_data:
                error_message = "Invalid email or password."
                return render_template('login.html', error_message=error_message)

            # Verify the hashed password using passlib
            if not bcrypt.verify(password, user_data[3]):  # Assuming password hash is in index 3
                error_message = "Invalid email or password."
                return render_template('login.html', error_message=error_message)

            # Redirect back to index, no session management yet
            return redirect(url_for('index'))

        except Exception as e:
            print("Error:", e)
            error_message = "An error occurred during login. Please try again later."
            return render_template('login.html', error_message=error_message)

        finally:
            # Close the database connection
            cursor.close()
            connection.close()

    return render_template('login.html')

# User profile page
@app.route('/profile')
def user_profile():
    # Implement logic to display and edit user profile information
    user_profile_data = {}
    return render_template('user_profile.html', user_profile_data=user_profile_data)

# Recipe details page
@app.route('/recipe/<int:recipe_id>')
def recipe(recipe_id):
    # Implement logic to fetch recipe details based on the 'recipe_id'
    recipe_details = {}
    return render_template('recipe.html', recipe_details=recipe_details)

if __name__ == '__main__':
    app.run(debug=True)
