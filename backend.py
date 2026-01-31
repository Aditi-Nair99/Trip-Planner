import os
import json
import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import sqlite3

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app, supports_credentials=True)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Database configuration - Try MySQL first, fallback to SQLite
USE_MYSQL = os.getenv('USE_MYSQL', 'false').lower() == 'true'
DB_TYPE = "MySQL" if USE_MYSQL else "SQLite"

print(f"Using database type: {DB_TYPE}")

# For demonstration, we'll use SQLite as fallback
SQLITE_DB_PATH = 'voyager.db'

def get_db_connection():
    """Get database connection based on configuration"""
    if USE_MYSQL:
        try:
            import mysql.connector
            from mysql.connector import Error
            
            db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'user': os.getenv('DB_USER', 'root'),
                'password': os.getenv('DB_PASSWORD', ''),
                'database': os.getenv('DB_NAME', 'voyager_db'),
                'port': os.getenv('DB_PORT', '3306')
            }
            
            # Try connecting to MySQL
            connection = mysql.connector.connect(**db_config)
            print("Connected to MySQL database")
            return connection
        except ImportError:
            print("mysql-connector-python not installed. Falling back to SQLite.")
            return get_sqlite_connection()
        except Error as e:
            print(f"MySQL connection error: {e}")
            print("Falling back to SQLite database.")
            return get_sqlite_connection()
    else:
        return get_sqlite_connection()

def get_sqlite_connection():
    """Get SQLite database connection"""
    try:
        connection = sqlite3.connect(SQLITE_DB_PATH)
        connection.row_factory = sqlite3.Row
        print(f"Connected to SQLite database: {SQLITE_DB_PATH}")
        return connection
    except Exception as e:
        print(f"SQLite connection error: {e}")
        return None

# Create tables if they don't exist
def init_db():
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        
        # Create users table
        if DB_TYPE == "MySQL":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create trips table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trips (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    destination VARCHAR(100) NOT NULL,
                    travel_days INT NOT NULL,
                    budget VARCHAR(50) NOT NULL,
                    travelers INT NOT NULL,
                    interests TEXT NOT NULL,
                    additional_notes TEXT,
                    itinerary_json JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
        else:
            # SQLite version
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create trips table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    destination TEXT NOT NULL,
                    travel_days INTEGER NOT NULL,
                    budget TEXT NOT NULL,
                    travelers INTEGER NOT NULL,
                    interests TEXT NOT NULL,
                    additional_notes TEXT,
                    itinerary_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
        
        connection.commit()
        
        # Insert demo users if none exists
        cursor.execute("SELECT COUNT(*) as count FROM users")
        result = cursor.fetchone()
        user_count = result[0] if result else 0
        
        if user_count == 0:
            # Insert Aditi Nair
            aditi_password = bcrypt.hashpw(b"aditi12345", bcrypt.gensalt())
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("Aditi Nair", "aditirajeshnair5@gmail.com", aditi_password)
            )
            
            # Insert Test User
            test_password = bcrypt.hashpw(b"test123", bcrypt.gensalt())
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("Test User", "test@example.com", test_password)
            )
            
            connection.commit()
            print("Demo users created:")
            print("1. Aditi Nair - aditirajeshnair5@gmail.com / aditi12345")
            print("2. Test User - test@example.com / test123")
        
        cursor.close()
        connection.close()
        print(f"Database initialized successfully using {DB_TYPE}")
    else:
        print("Failed to initialize database")

# JWT token required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            # Decode token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
            
            # Verify user exists in database
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                if DB_TYPE == "MySQL":
                    cursor.execute("SELECT id, name, email FROM users WHERE id = %s", (current_user_id,))
                else:
                    cursor.execute("SELECT id, name, email FROM users WHERE id = ?", (current_user_id,))
                
                user = cursor.fetchone()
                cursor.close()
                connection.close()
                
                if not user:
                    return jsonify({'message': 'User not found!'}), 401
                
                # Convert to dictionary
                current_user = {
                    'id': user[0],
                    'name': user[1],
                    'email': user[2]
                }
            else:
                return jsonify({'message': 'Database connection error!'}), 500
                
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Mock AI trip generation (replace with actual AI API integration)
def generate_ai_itinerary(trip_data):
    """
    Generate a travel itinerary using AI.
    In a real application, this would call an AI API like OpenAI or Gemini.
    """
    destination = trip_data['destination']
    travel_days = trip_data['travel_days']
    budget = trip_data['budget']
    travelers = trip_data['travelers']
    interests = trip_data['interests']
    additional_notes = trip_data.get('additional_notes', '')
    
    # Create a mock itinerary (replace with actual AI API call)
    days = []
    
    for day in range(1, travel_days + 1):
        if day == 1:
            day_title = f"Arrival in {destination}"
            day_summary = f"Arrive in {destination}, check into your accommodation, and start exploring."
            activities = [
                {"time": "Afternoon", "type": "arrival", "description": "Arrive at airport and transfer to hotel", "location": "Airport to Hotel"},
                {"time": "Evening", "type": "sightseeing", "description": "Take a walk around the neighborhood to get familiar with the area", "location": "City Center"},
                {"time": "Dinner", "type": "dining", "description": "Enjoy welcome dinner at a local restaurant", "location": "Local Restaurant"}
            ]
        elif day == travel_days:
            day_title = f"Departure from {destination}"
            day_summary = f"Last day in {destination}, some final exploration before departure."
            activities = [
                {"time": "Morning", "type": "breakfast", "description": "Final breakfast at hotel", "location": "Hotel"},
                {"time": "Late Morning", "type": "sightseeing", "description": "Visit any last-minute attractions or do some souvenir shopping", "location": "Shopping District"},
                {"time": "Afternoon", "type": "departure", "description": "Transfer to airport for departure", "location": "Hotel to Airport"}
            ]
        else:
            day_title = f"Exploring {destination}"
            day_summary = f"Full day of exploration based on your interests: {interests}."
            activities = [
                {"time": "Morning", "type": "breakfast", "description": "Breakfast at hotel or local cafe", "location": "Hotel/Cafe"},
                {"time": "Late Morning", "type": "sightseeing", "description": "Visit main attractions and landmarks", "location": "Various Attractions"},
                {"time": "Lunch", "type": "dining", "description": "Lunch at a recommended local restaurant", "location": "Local Restaurant"},
                {"time": "Afternoon", "type": "activity", "description": f"Activity based on your interests: {interests}", "location": "Various Locations"},
                {"time": "Evening", "type": "dining", "description": "Dinner experience", "location": "Restaurant"}
            ]
        
        days.append({
            "day": day,
            "title": day_title,
            "summary": day_summary,
            "activities": activities
        })
    
    # Calculate estimated cost based on budget
    budget_ranges = {
        "budget": {"per_day": 80, "accommodation": "Hostels/Budget Hotels", "food": "Street food/Local restaurants"},
        "moderate": {"per_day": 150, "accommodation": "3-4 Star Hotels", "food": "Mix of local and mid-range restaurants"},
        "luxury": {"per_day": 300, "accommodation": "5 Star Hotels/Luxury Resorts", "food": "Fine dining and premium experiences"}
    }
    
    budget_info = budget_ranges.get(budget, budget_ranges["moderate"])
    estimated_cost = budget_info["per_day"] * travel_days * travelers
    
    itinerary = {
        "summary": f"A {travel_days}-day {budget} trip to {destination} for {travelers} people interested in {interests}.",
        "days": days,
        "estimated_cost": estimated_cost,
        "accommodation_type": budget_info["accommodation"],
        "dining_style": budget_info["food"],
        "travel_tips": [
            "Book accommodations in advance for better rates",
            "Try local transportation for authentic experience",
            "Carry local currency for small purchases",
            "Respect local customs and traditions"
        ]
    }
    
    return itinerary

# Routes
@app.route('/')
def index():
    return jsonify({
        "message": "Voyager AI Trip Planner API", 
        "status": "running",
        "database": DB_TYPE,
        "version": "2.0"
    })

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        
        # Validate input
        if not name or not email or not password:
            return jsonify({'message': 'All fields are required!'}), 400
        
        if len(password) < 8:
            return jsonify({'message': 'Password must be at least 8 characters long!'}), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Save to database
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Check if email already exists
            if DB_TYPE == "MySQL":
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            else:
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            
            if cursor.fetchone():
                cursor.close()
                connection.close()
                return jsonify({'message': 'Email already registered!'}), 409
            
            # Insert new user
            if DB_TYPE == "MySQL":
                cursor.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
                    (name, email, password_hash)
                )
            else:
                cursor.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, password_hash)
                )
            
            connection.commit()
            user_id = cursor.lastrowid
            cursor.close()
            connection.close()
            
            return jsonify({
                'message': 'User registered successfully!',
                'user_id': user_id,
                'database': DB_TYPE
            }), 201
        else:
            return jsonify({'message': 'Database connection error!'}), 500
            
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'message': f'Registration failed! Error: {str(e)}'}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        # Validate input
        if not email or not password:
            return jsonify({'message': 'Email and password are required!'}), 400
        
        # Get user from database
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            if DB_TYPE == "MySQL":
                cursor.execute("SELECT id, name, email, password_hash FROM users WHERE email = %s", (email,))
            else:
                cursor.execute("SELECT id, name, email, password_hash FROM users WHERE email = ?", (email,))
            
            user = cursor.fetchone()
            cursor.close()
            connection.close()
            
            if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
                # Generate JWT token
                token = jwt.encode({
                    'user_id': user[0],
                    'exp': datetime.utcnow() + app.config['JWT_ACCESS_TOKEN_EXPIRES']
                }, app.config['SECRET_KEY'], algorithm='HS256')
                
                return jsonify({
                    'message': 'Login successful!',
                    'token': token,
                    'user': {
                        'id': user[0],
                        'name': user[1],
                        'email': user[2]
                    },
                    'database': DB_TYPE
                }), 200
            else:
                return jsonify({'message': 'Invalid email or password!'}), 401
        else:
            return jsonify({'message': 'Database connection error!'}), 500
            
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'message': f'Login failed! Error: {str(e)}'}), 500

@app.route('/generate-trip', methods=['POST'])
@token_required
def generate_trip(current_user):
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['destination', 'travel_days', 'budget', 'travelers', 'interests']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'{field} is required!'}), 400
        
        # Generate itinerary using AI
        itinerary = generate_ai_itinerary(data)
        
        # Prepare trip data for response
        trip_data = {
            'user_id': current_user['id'],
            'destination': data['destination'],
            'travel_days': data['travel_days'],
            'budget': data['budget'],
            'travelers': data['travelers'],
            'interests': data['interests'],
            'additional_notes': data.get('additional_notes', ''),
            'itinerary': itinerary,
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'message': 'Trip generated successfully!',
            'trip': trip_data,
            'database': DB_TYPE
        }), 200
        
    except Exception as e:
        print(f"Trip generation error: {e}")
        return jsonify({'message': f'Failed to generate trip! Error: {str(e)}'}), 500

@app.route('/save-trip', methods=['POST'])
@token_required
def save_trip(current_user):
    try:
        data = request.get_json()
        trip_data = data.get('trip')
        
        if not trip_data:
            return jsonify({'message': 'Trip data is required!'}), 400
        
        # Save trip to database
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            if DB_TYPE == "MySQL":
                cursor.execute("""
                    INSERT INTO trips (user_id, destination, travel_days, budget, travelers, interests, additional_notes, itinerary_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    current_user['id'],
                    trip_data['destination'],
                    trip_data['travel_days'],
                    trip_data['budget'],
                    trip_data['travelers'],
                    trip_data['interests'],
                    trip_data.get('additional_notes', ''),
                    json.dumps(trip_data.get('itinerary', {}))
                ))
            else:
                cursor.execute("""
                    INSERT INTO trips (user_id, destination, travel_days, budget, travelers, interests, additional_notes, itinerary_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    current_user['id'],
                    trip_data['destination'],
                    trip_data['travel_days'],
                    trip_data['budget'],
                    trip_data['travelers'],
                    trip_data['interests'],
                    trip_data.get('additional_notes', ''),
                    json.dumps(trip_data.get('itinerary', {}))
                ))
            
            connection.commit()
            trip_id = cursor.lastrowid
            cursor.close()
            connection.close()
            
            return jsonify({
                'message': 'Trip saved successfully!',
                'trip_id': trip_id,
                'database': DB_TYPE
            }), 201
        else:
            return jsonify({'message': 'Database connection error!'}), 500
            
    except Exception as e:
        print(f"Save trip error: {e}")
        return jsonify({'message': f'Failed to save trip! Error: {str(e)}'}), 500

@app.route('/get-trips', methods=['GET'])
@token_required
def get_trips(current_user):
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            if DB_TYPE == "MySQL":
                cursor.execute("""
                    SELECT id, destination, travel_days, budget, travelers, interests, 
                           additional_notes, created_at
                    FROM trips 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC
                """, (current_user['id'],))
            else:
                cursor.execute("""
                    SELECT id, destination, travel_days, budget, travelers, interests, 
                           additional_notes, created_at
                    FROM trips 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC
                """, (current_user['id'],))
            
            trips = []
            rows = cursor.fetchall()
            for row in rows:
                trips.append({
                    'id': row[0],
                    'destination': row[1],
                    'travel_days': row[2],
                    'budget': row[3],
                    'travelers': row[4],
                    'interests': row[5],
                    'additional_notes': row[6],
                    'created_at': row[7]
                })
            
            cursor.close()
            connection.close()
            
            return jsonify({
                'message': 'Trips retrieved successfully!',
                'trips': trips,
                'database': DB_TYPE
            }), 200
        else:
            return jsonify({'message': 'Database connection error!'}), 500
            
    except Exception as e:
        print(f"Get trips error: {e}")
        return jsonify({'message': f'Failed to retrieve trips! Error: {str(e)}'}), 500

@app.route('/get-trip/<int:trip_id>', methods=['GET'])
@token_required
def get_trip(current_user, trip_id):
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            if DB_TYPE == "MySQL":
                cursor.execute("""
                    SELECT id, destination, travel_days, budget, travelers, interests, 
                           additional_notes, itinerary_json, created_at
                    FROM trips 
                    WHERE id = %s AND user_id = %s
                """, (trip_id, current_user['id']))
            else:
                cursor.execute("""
                    SELECT id, destination, travel_days, budget, travelers, interests, 
                           additional_notes, itinerary_json, created_at
                    FROM trips 
                    WHERE id = ? AND user_id = ?
                """, (trip_id, current_user['id']))
            
            row = cursor.fetchone()
            cursor.close()
            connection.close()
            
            if row:
                # Parse itinerary JSON
                itinerary = {}
                if row[7]:
                    try:
                        itinerary = json.loads(row[7])
                    except:
                        itinerary = {}
                
                trip = {
                    'id': row[0],
                    'destination': row[1],
                    'travel_days': row[2],
                    'budget': row[3],
                    'travelers': row[4],
                    'interests': row[5],
                    'additional_notes': row[6],
                    'itinerary': itinerary,
                    'created_at': row[8]
                }
                
                return jsonify({
                    'message': 'Trip retrieved successfully!',
                    'trip': trip,
                    'database': DB_TYPE
                }), 200
            else:
                return jsonify({'message': 'Trip not found or access denied!'}), 404
        else:
            return jsonify({'message': 'Database connection error!'}), 500
            
    except Exception as e:
        print(f"Get trip error: {e}")
        return jsonify({'message': f'Failed to retrieve trip! Error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    connection = get_db_connection()
    db_status = "connected" if connection else "disconnected"
    if connection:
        connection.close()
    
    return jsonify({
        "status": "healthy", 
        "database": db_status,
        "database_type": DB_TYPE,
        "timestamp": datetime.now().isoformat()
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Endpoint not found!'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'message': 'Internal server error!'}), 500

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run Flask app
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"🚀 Starting Voyager AI Trip Planner API on port {port}")
    print(f"📊 Database type: {DB_TYPE}")
    print(f"🐛 Debug mode: {debug}")
    print(f"👤 Demo users available:")
    print(f"   1. Aditi Nair - aditirajeshnair5@gmail.com / aditi12345")
    print(f"   2. Test User - test@example.com / test123")
    print(f"🔗 API Base URL: http://localhost:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)