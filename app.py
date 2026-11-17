from datetime import datetime
import io
from database import DailyLog, MenuItem, PredictionLog, Settings, db, seed_data
from flask import Flask, Response, redirect, render_template, request, url_for
import joblib
import pandas as pd

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///foodwise.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
  db.create_all()
  seed_data()

# Load trained ML model
model_bundle = joblib.load("demand_model.pkl")
ml_model = model_bundle["model"]
feature_cols = model_bundle["features"]
base_confidence = model_bundle["confidence"]


# 1. Dashboard (Home)
@app.route("/")
def dashboard():
  logs = DailyLog.query.order_by(DailyLog.date.desc()).limit(7).all()
  logs.reverse()  # Chronological order for charts

  dates = [log.date for log in logs]
  actual_sales = [log.meals_sold for log in logs]
  # Simulated baseline forecast vs actual
  predicted_sales = [int(log.present_students * 0.90) for log in logs]
  prepared_kg = [log.food_prepared_kg for log in logs]
  wasted_kg = [log.food_wasted_kg for log in logs]

  total_prep = sum(prepared_kg) or 1
  total_waste = sum(wasted_kg)
  waste_pct = round((total_waste / total_prep) * 100, 1)
  waste_reduction_pct = round(max(0, 18.0 - waste_pct), 1)
  est_savings = round(
      (total_prep * 0.18 - total_waste) * 150, 0
  )  # ₹150/kg saved

  latest_pred = PredictionLog.query.order_by(PredictionLog.id.desc()).first()

  return render_template(
      "dashboard.html",
      dates=dates,
      actual_sales=actual_sales,
      predicted_sales=predicted_sales,
      prepared_kg=prepared_kg,
      wasted_kg=wasted_kg,
      waste_pct=waste_pct,
      waste_reduction_pct=waste_reduction_pct,
      est_savings=est_savings,
      latest_pred=latest_pred,
  )


# 2. Demand Prediction Engine
@app.route("/predict", methods=["GET", "POST"])
def predict():
  prediction_result = None
  settings = Settings.query.first()
  menu_items = MenuItem.query.all()
  last_log = DailyLog.query.order_by(DailyLog.date.desc()).first()
  default_prev_sales = last_log.meals_sold if last_log else 380

  if request.method == "POST":
    attendance = int(request.form.get("attendance", 400))
    prev_sales = int(request.form.get("prev_sales", default_prev_sales))
    weather = request.form.get("weather", "Sunny")
    is_event = 1 if request.form.get("is_event") == "1" else 0

    # Build input row matching training features
    input_data = pd.DataFrame([{
        "present_students": attendance,
        "prev_day_sales": prev_sales,
        "is_event": is_event,
        "weather_Sunny": 1 if weather == "Sunny" else 0,
        "weather_Cloudy": 1 if weather == "Cloudy" else 0,
        "weather_Rainy": 1 if weather == "Rainy" else 0,
    }])[feature_cols]

    raw_pred = int(ml_model.predict(input_data)[0])
    buffer_mult = 1 + (settings.safety_buffer_pct / 100.0)
    recommended_meals = int(raw_pred * buffer_mult)
    recommended_kg = round(recommended_meals * 0.40, 1)  # ~400g per meal

    # Save prediction to DB
    new_pred = PredictionLog(
        date=datetime.now().strftime("%Y-%m-%d"),
        predicted_demand=raw_pred,
        recommended_prep=recommended_kg,
        confidence_score=base_confidence,
    )
    db.session.add(new_pred)
    db.session.commit()

    prediction_result = {
        "raw_pred": raw_pred,
        "recommended_meals": recommended_meals,
        "recommended_kg": recommended_kg,
        "confidence": base_confidence,
        "buffer": settings.safety_buffer_pct,
    }

  return render_template(
      "predict.html",
      result=prediction_result,
      menu_items=menu_items,
      default_prev_sales=default_prev_sales,
  )


# 3. Food Waste Analytics
@app.route("/analytics")
def analytics():
  logs = DailyLog.query.order_by(DailyLog.date.desc()).limit(7).all()
  logs.reverse()
  settings = Settings.query.first()
  high_risk_items = MenuItem.query.filter(
      MenuItem.waste_risk.in_(["High", "Medium"])
  ).all()

  total_prep = round(sum(l.food_prepared_kg for l in logs), 1)
  total_waste = round(sum(l.food_wasted_kg for l in logs), 1)
  total_consumed = round(total_prep - total_waste, 1)
  overall_waste_pct = round((total_waste / (total_prep or 1)) * 100, 1)
  monetary_loss = round(total_waste * 150, 2)  # ₹150 per kg wasted

  return render_template(
      "analytics.html",
      logs=logs,
      total_prep=total_prep,
      total_consumed=total_consumed,
      total_waste=total_waste,
      overall_waste_pct=overall_waste_pct,
      monetary_loss=monetary_loss,
      high_risk_items=high_risk_items,
      threshold=settings.waste_threshold_pct,
  )


# 4. Menu Management
@app.route("/menu", methods=["GET", "POST"])
def menu():
  if request.method == "POST":
    name = request.form.get("name")
    meal_type = request.form.get("meal_type")
    base_demand = int(request.form.get("base_demand", 100))
    waste_risk = request.form.get("waste_risk", "Low")
    if name:
      db.session.add(
          MenuItem(
              name=name,
              meal_type=meal_type,
              base_demand=base_demand,
              waste_risk=waste_risk,
          )
      )
      db.session.commit()
    return redirect(url_for("menu"))

  items = MenuItem.query.all()
  return render_template("menu.html", items=items)


# 5. Attendance Tracking
@app.route("/attendance", methods=["GET", "POST"])
def attendance():
  settings = Settings.query.first()
  enrolled = settings.capacity
  present = int(request.form.get("present_students", int(enrolled * 0.85)))
  attendance_pct = round((present / (enrolled or 1)) * 100, 1)
  est_meals = int(present * 0.90)

  # Note: Matches your filename 'attendence.html'
  return render_template(
      "attendence.html",
      enrolled=enrolled,
      present=present,
      attendance_pct=attendance_pct,
      est_meals=est_meals,
  )


# 6. Sales Data
@app.route("/sales")
def sales():
  logs = DailyLog.query.order_by(DailyLog.date.desc()).all()
  return render_template("sales.html", logs=logs)


# 7. Reports & CSV Export
@app.route("/reports")
def reports():
  logs = DailyLog.query.order_by(DailyLog.date.desc()).limit(10).all()
  return render_template("reports.html", logs=logs)


@app.route("/reports/export/<report_type>")
def export_report(report_type):
  logs = DailyLog.query.order_by(DailyLog.date.desc()).all()
  data = [{
      "Date": l.date,
      "Attendance": l.present_students,
      "Meals Sold": l.meals_sold,
      "Prepared (kg)": l.food_prepared_kg,
      "Wasted (kg)": l.food_wasted_kg,
      "Waste %": round((l.food_wasted_kg / l.food_prepared_kg) * 100, 1),
      "Revenue (INR)": l.revenue,
  } for l in logs]
  df = pd.DataFrame(data)
  output = io.StringIO()
  df.to_csv(output, index=False)
  return Response(
      output.getvalue(),
      mimetype="text/csv",
      headers={
          "Content-Disposition": (
              f"attachment;filename=foodwise_{report_type}_report.csv"
          )
      },
  )


# 8. Settings
@app.route("/settings", methods=["GET", "POST"])
def settings():
  config = Settings.query.first()
  if request.method == "POST":
    config.canteen_name = request.form.get("canteen_name", config.canteen_name)
    config.capacity = int(request.form.get("capacity", config.capacity))
    config.safety_buffer_pct = float(
        request.form.get("safety_buffer_pct", config.safety_buffer_pct)
    )
    config.waste_threshold_pct = float(
        request.form.get("waste_threshold_pct", config.waste_threshold_pct)
    )
    db.session.commit()
    return redirect(url_for("settings"))

  return render_template("settings.html", config=config)


if __name__ == "__main__":
  app.run(debug=True)