from datetime import datetime, timedelta
import random
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class MenuItem(db.Model):
  __tablename__ = "menu_items"
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  meal_type = db.Column(db.String(50), nullable=False)
  base_demand = db.Column(db.Integer, default=100)
  waste_risk = db.Column(db.String(20), default="Low")


class DailyLog(db.Model):
  __tablename__ = "daily_logs"
  id = db.Column(db.Integer, primary_key=True)
  date = db.Column(db.String(20), unique=True, nullable=False)
  enrolled_students = db.Column(db.Integer, default=500)
  present_students = db.Column(db.Integer, nullable=False)
  meals_sold = db.Column(db.Integer, nullable=False)
  food_prepared_kg = db.Column(db.Float, nullable=False)
  food_wasted_kg = db.Column(db.Float, nullable=False)
  revenue = db.Column(db.Float, nullable=False)
  weather = db.Column(db.String(20), default="Sunny")
  is_event = db.Column(db.Boolean, default=False)


class PredictionLog(db.Model):
  __tablename__ = "prediction_logs"
  id = db.Column(db.Integer, primary_key=True)
  date = db.Column(db.String(20), nullable=False)
  predicted_demand = db.Column(db.Integer, nullable=False)
  recommended_prep = db.Column(db.Float, nullable=False)
  confidence_score = db.Column(db.Float, nullable=False)


class Settings(db.Model):
  __tablename__ = "settings"
  id = db.Column(db.Integer, primary_key=True)
  canteen_name = db.Column(db.String(100), default="Main Campus Canteen")
  capacity = db.Column(db.Integer, default=500)
  safety_buffer_pct = db.Column(db.Float, default=5.0)
  waste_threshold_pct = db.Column(db.Float, default=12.0)


def seed_data():
  if not Settings.query.first():
    db.session.add(
        Settings(
            canteen_name="Main Campus Canteen",
            capacity=500,
            safety_buffer_pct=5.0,
            waste_threshold_pct=12.0,
        )
    )

  if not MenuItem.query.first():
    sample_menu = [
        MenuItem(
            name="Steamed Rice",
            meal_type="Lunch",
            base_demand=380,
            waste_risk="High",
        ),
        MenuItem(
            name="Paneer Butter Masala",
            meal_type="Lunch",
            base_demand=340,
            waste_risk="Low",
        ),
        MenuItem(
            name="Masala Dosa",
            meal_type="Breakfast",
            base_demand=290,
            waste_risk="Medium",
        ),
        MenuItem(
            name="Dal Tadka",
            meal_type="Dinner",
            base_demand=310,
            waste_risk="Low",
        ),
        MenuItem(
            name="Samosa & Chai",
            meal_type="Snacks",
            base_demand=250,
            waste_risk="Medium",
        ),
    ]
    db.session.add_all(sample_menu)

  if not DailyLog.query.first():
    weathers = ["Sunny", "Cloudy", "Rainy"]
    for i in range(30, 0, -1):
      day_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
      present = random.randint(340, 485)
      weather = random.choice(weathers)
      is_event = True if i % 7 == 0 else False

      demand_factor = 0.82 if weather == "Rainy" else 0.90
      if is_event:
        demand_factor += 0.12
      sold = int(present * demand_factor)

      prepared_kg = round(sold * 0.42, 1)
      consumed_kg = round(sold * 0.37, 1)
      wasted_kg = round(max(1.2, prepared_kg - consumed_kg), 1)
      revenue = round(sold * 65.0, 2)

      db.session.add(
          DailyLog(
              date=day_str,
              enrolled_students=500,
              present_students=present,
              meals_sold=sold,
              food_prepared_kg=prepared_kg,
              food_wasted_kg=wasted_kg,
              revenue=revenue,
              weather=weather,
              is_event=is_event,
          )
      )

  if not PredictionLog.query.first():
    today_str = datetime.now().strftime("%Y-%m-%d")
    db.session.add(
        PredictionLog(
            date=today_str,
            predicted_demand=410,
            recommended_prep=172.2,
            confidence_score=91.5,
        )
    )

  db.session.commit()
  print("Sample data seeded successfully!")