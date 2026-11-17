FoodWise AI - Smart Food Waste Predictor

FoodWise AI is a machine learning web application built for institutional canteens and dining halls to forecast daily meal demand, optimize kitchen preparation quantities, and reduce food waste.

Why FoodWise AI

Manual meal estimation often leads to overproduction and costly food waste, or underproduction and meal shortages. FoodWise AI replaces guesswork with data-driven forecasts based on student attendance, prior sales, weather, and campus events.

Key Advantages

- Data-Driven Preparation: Aligns cooking quantities with machine learning demand predictions to reduce overproduction.
- Cost Savings: Tracks food waste in kilograms and converts losses into clear financial metrics.
- Dynamic Adjustments: Adapts forecasts to daily attendance shifts, weather conditions, and campus events.
- Operational Safeguards: Applies configurable safety buffers to prevent shortages and flags high-waste menu items.
- Easy Scaling: Runs locally with SQLite and supports seamless migration to MySQL for larger deployments.
- Audit-Ready Exports: Generates one-click CSV reports for daily, weekly, and monthly reviews.

Core Modules

- Operations Dashboard: Displays predicted demand, 7-day waste percentages, cost savings, and forecast charts.
- Demand Prediction Engine: Calculates recommended meals and preparation weights (kg) using a Random Forest model.
- Food Waste Analytics: Tracks prepared versus wasted food and highlights high-risk dishes.
- Menu Management: Organizes daily menus by meal category, expected demand, and waste risk.
- Attendance Tracking: Updates expected meal consumption based on present student headcounts.
- Sales and Waste Logs: Stores historical attendance, sales, preparation weights, waste percentages, and revenue.
- Reports and Exports: Downloads CSV audits for waste trends, demand, and cost savings.
- System Settings: Configures canteen capacity, safety buffers, and waste alert thresholds.

Technology Stack

- Backend: Python, Flask, Flask-SQLAlchemy
- Frontend: HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js
- Database: SQLite and MySQL-compatible via SQLAlchemy ORM
- Machine Learning: Scikit-learn (RandomForestRegressor), Pandas, NumPy, Joblib

Planned Enhancements

- Role-based user authentication (Flask-Login) for managers and kitchen staff.
- Direct UI form for logging daily actuals with one-click model retraining.
- Automated weather API integration for live daily forecasts.
