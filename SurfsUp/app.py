# Import the dependencies.
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

#################################################
# Database Setup
#################################################

# Create engine to connect to SQLite database
engine = create_engine("sqlite:///resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

# Homepage route
@app.route('/')
def home():
    """Welcome to the Climate API! Use the following routes: /api/v1.0/precipitation, /api/v1.0/stations, /api/v1.0/tobs, /api/v1.0/<start>, /api/v1.0/<start>/<end>"""
    return (

    "Welcome to the Climate API!<br/>"
    "Available Routes:<br/>"
    "/api/v1.0/precipitation - Precipitation data for the last 12 months<br/>"
    "/api/v1.0/stations - List of all weather stations<br/>"
    "/api/v1.0/tobs - Temperature observations for the most active station<br/>"
    "/api/v1.0/&lt;start&gt; - Min, Avg, and Max temperatures from a start date<br/>"
    "/api/v1.0/&lt;start&gt;/&lt;end&gt; - Min, Avg, and Max temperatures for a date range"
    )

# Precipitation route - returns last 12 months of data
@app.route('/api/v1.0/precipitation')
def precipitation():
    """Return the last 12 months of precipitation data."""
    with Session(engine) as session:
        # Calculate the date 12 months ago from the last date in the database
        most_recent_date = session.query(func.max(Measurement.date)).scalar()
        most_recent_date = datetime.strptime(most_recent_date, '%Y-%m-%d')
        twelve_months_ago = most_recent_date - timedelta(days=365)

        # Convert twelve_months_ago back to a string in 'YYYY-MM-DD' format
        twelve_months_ago_str = twelve_months_ago.strftime('%Y-%m-%d')

        # Query precipitation data
        results = session.query(Measurement.date, Measurement.prcp).\
            filter(Measurement.date >= twelve_months_ago_str).all()

        # Convert results to a dictionary
        prcp_dict = {date: prcp for date, prcp in results}

        return jsonify(prcp_dict)

# Stations route - returns a list of all stations
@app.route('/api/v1.0/stations')
def stations():
    """Return a list of all weather stations."""
    with Session(engine) as session:
        results = session.query(Station.station).all()

        if not results:
            return jsonify({"error": "No stations found."}), 404

        stations = [result[0] for result in results]
        return jsonify(stations)

@app.route('/api/v1.0/tobs')
def tobs():
    """Return temperature observations for the most active station from the last year."""
    with Session(engine) as session:
        # Find the most active station
        most_active_station = session.query(Measurement.station).\
            group_by(Measurement.station).\
            order_by(func.count(Measurement.station).desc()).first()

        if not most_active_station:
            return jsonify({"error": "No data found for stations."}), 404

        station_id = most_active_station[0]

        # Get the most recent date from the database
        most_recent_date_text = session.query(func.max(Measurement.date)).scalar()
        most_recent_date = datetime.strptime(most_recent_date_text, '%Y-%m-%d')
        twelve_months_ago = most_recent_date - timedelta(days=365)

        # Query temperature observations
        results = session.query(Measurement.date, Measurement.tobs).\
            filter(Measurement.station == station_id).\
            filter(Measurement.date >= twelve_months_ago.strftime('%Y-%m-%d')).all()

        tobs_list = [{"date": date, "tobs": tobs} for date, tobs in results]
        return jsonify(tobs_list)

@app.route('/api/v1.0/<start>')
def start_date(start):
    """Return min, avg, and max temperatures for a given start date."""
    with Session(engine) as session:
        try:
            # Convert start date to datetime object
            start_date = datetime.strptime(start, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

        results = session.query(
            func.min(Measurement.tobs),
            func.avg(Measurement.tobs),
            func.max(Measurement.tobs)
        ).filter(Measurement.date >= start_date.strftime('%Y-%m-%d')).all()

        if not results[0][0]:
            return jsonify({"error": "No data found for the given start date."}), 404

        return jsonify({
            "Start Date": start,
            "Min Temperature": results[0][0],
            "Avg Temperature": results[0][1],
            "Max Temperature": results[0][2]
        })

@app.route('/api/v1.0/<start>/<end>')
def start_end_date(start, end):
    """Return min, avg, and max temperatures for a date range."""
    with Session(engine) as session:
        try:
            # Convert start and end dates to datetime objects
            start_date = datetime.strptime(start, '%Y-%m-%d')
            end_date = datetime.strptime(end, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

        results = session.query(
            func.min(Measurement.tobs),
            func.avg(Measurement.tobs),
            func.max(Measurement.tobs)
        ).filter(Measurement.date >= start_date.strftime('%Y-%m-%d')).filter(Measurement.date <= end_date.strftime('%Y-%m-%d')).all()

        if not results[0][0]:
            return jsonify({"error": "No data found for the given date range."}), 404

        return jsonify({
            "Start Date": start,
            "End Date": end,
            "Min Temperature": results[0][0],
            "Avg Temperature": results[0][1],
            "Max Temperature": results[0][2]
        })

if __name__ == '__main__':
    app.run(debug=True)