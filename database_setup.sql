-- Voyager AI Trip Planner Database Setup
-- This script creates the necessary database and tables for the Voyager application

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS voyager_db;
USE voyager_db;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trips table
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
);

-- Create indexes for better performance
CREATE INDEX idx_user_id ON trips(user_id);
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_trip_created ON trips(created_at);

-- Insert demo users (use bcrypt to hash passwords in actual application)
-- Passwords are pre-hashed for demo purposes:
-- aditi12345 -> $2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW
-- test123 -> $2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW

INSERT IGNORE INTO users (name, email, password_hash) VALUES 
('Aditi Nair', 'aditirajeshnair5@gmail.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW'),
('Test User', 'test@example.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW');

-- Insert sample trips for demo purposes
INSERT IGNORE INTO trips (user_id, destination, travel_days, budget, travelers, interests, itinerary_json) VALUES
(1, 'Paris, France', 5, 'moderate', 2, 'Sightseeing, Food, Culture', '{
    "summary": "A 5-day moderate trip to Paris for 2 people interested in Sightseeing, Food, Culture.",
    "days": [
        {
            "day": 1,
            "title": "Arrival in Paris",
            "summary": "Arrive in Paris, check into your hotel, and start exploring the City of Lights.",
            "theme": "Arrival & Orientation",
            "activities": [
                {"time": "2:00 PM", "type": "arrival", "description": "Arrive at Charles de Gaulle Airport", "location": "CDG Airport"},
                {"time": "4:00 PM", "type": "sightseeing", "description": "Check into hotel and freshen up", "location": "Hotel"},
                {"time": "7:30 PM", "type": "dining", "description": "Welcome dinner at traditional French bistro", "location": "Le Marais"}
            ]
        },
        {
            "day": 2,
            "title": "Parisian Landmarks",
            "summary": "Explore the iconic landmarks of Paris.",
            "theme": "Landmark Tour",
            "activities": [
                {"time": "9:00 AM", "type": "breakfast", "description": "French breakfast at local cafe", "location": "Local Cafe"},
                {"time": "10:30 AM", "type": "sightseeing", "description": "Visit Eiffel Tower", "location": "Champ de Mars"},
                {"time": "1:00 PM", "type": "lunch", "description": "Lunch near Notre Dame", "location": "Latin Quarter"},
                {"time": "3:00 PM", "type": "sightseeing", "description": "Explore Louvre Museum", "location": "Louvre Museum"},
                {"time": "7:00 PM", "type": "dining", "description": "Dinner cruise on Seine River", "location": "Seine River"}
            ]
        }
    ],
    "estimated_cost": 1500,
    "accommodation_type": "3-4 Star Hotels",
    "dining_style": "Mix of local and mid-range restaurants",
    "travel_tips": ["Buy museum tickets online", "Use Paris Metro for transportation", "Try local patisseries"]
}'),
(2, 'Tokyo, Japan', 7, 'luxury', 4, 'Food, Culture, Technology', '{
    "summary": "A 7-day luxury trip to Tokyo for 4 people interested in Food, Culture, Technology.",
    "days": [
        {
            "day": 1,
            "title": "Welcome to Tokyo",
            "summary": "Arrive in Tokyo and experience the blend of tradition and technology.",
            "theme": "Arrival",
            "activities": [
                {"time": "3:00 PM", "type": "arrival", "description": "Arrive at Narita International Airport", "location": "Narita Airport"},
                {"time": "5:00 PM", "type": "transport", "description": "Transfer to luxury hotel", "location": "Airport to Hotel"},
                {"time": "8:00 PM", "type": "dining", "description": "Authentic sushi dinner", "location": "Ginza District"}
            ]
        }
    ],
    "estimated_cost": 4200,
    "accommodation_type": "5 Star Hotels/Luxury Resorts",
    "dining_style": "Fine dining and premium experiences",
    "travel_tips": ["Get a Suica card for transportation", "Try ramen at local shops", "Visit temples early to avoid crowds"]
}');

-- Display created tables
SHOW TABLES;

-- Display users
SELECT id, name, email, created_at FROM users;

-- Display trip count
SELECT COUNT(*) as total_trips FROM trips;

-- View sample trip data
SELECT 
    t.id,
    t.destination,
    t.travel_days,
    t.budget,
    t.travelers,
    u.name as user_name
FROM trips t
JOIN users u ON t.user_id = u.id
LIMIT 5;