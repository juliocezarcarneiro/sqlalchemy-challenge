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
engine = create_engine("sqlite:///hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

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
    return (
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Climate API</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    color: #333;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    text-align: left;
                }
                .container {
                    background-color: #fff;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }
                h1 {
                    color: #007BFF;
                }
                a {
                    color: #007BFF;
                    text-decoration: none;
                }
                a:hover {
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to the Climate API!</h1>
                <p>Explore the available routes below:</p>
                <ul style="list-style-type: none; padding: 0;">
                    <li><a href="/api/v1.0/precipitation">/api/v1.0/precipitation</a> - Precipitation data for the last 12 months</li>
                    <li><a href="/api/v1.0/stations">/api/v1.0/stations</a> - List of all weather stations</li>
                    <li><a href="/api/v1.0/tobs">/api/v1.0/tobs</a> - Temperature observations for the most active station</li>
                    <li><a href="/api/v1.0/&lt;start&gt;">/api/v1.0/&lt;start&gt;</a> - Min, Avg, and Max temperatures from a start date</li>
                    <li><a href="/api/v1.0/&lt;start&gt;/&lt;end&gt;">/api/v1.0/&lt;start&gt;/&lt;end&gt;</a> - Min, Avg, and Max temperatures for a date range</li>
    
               <div class="instructions">
            <h3>How to Use the Date Routes:</h3>
            <p>
                To use the date-based routes, replace <code>&lt;start&gt;</code> and/or <code>&lt;end&gt;</code> in the URL with a valid date in the format <strong>YYYY-MM-DD</strong>.
            </p>
                </ul>
            </div>
        </body>
        </html>
        """
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
        # Find the most active station (station with the most measurements)
        most_active_station = session.query(Measurement.station, func.count(Measurement.station))\
            .group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).first()

        # Get the most active station ID
        station_id = most_active_station[0]
        
        # Get the most recent date from the database
        most_recent_date = session.query(func.max(Measurement.date)).scalar()
        most_recent_date = datetime.strptime(most_recent_date, '%Y-%m-%d')
        
        # Calculate the date 1 year ago from the most recent date
        one_year_ago = most_recent_date - timedelta(days=365)
        one_year_ago_str = one_year_ago.strftime('%Y-%m-%d')

        # Query temperature observations for the most active station for the previous year
        results = session.query(Measurement.date, Measurement.tobs).\
            filter(Measurement.station == station_id).\
            filter(Measurement.date >= one_year_ago_str).all()

        # Convert results into a list of dictionaries with date and temperature observations
        tobs_list = [{"date": date, "temperature": tobs} for date, tobs in results]

        # Return the list as a JSON response
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

        # Query for TMIN, TAVG, and TMAX for dates >= start_date
        results = session.query(
            func.min(Measurement.tobs).label('TMIN'),
            func.avg(Measurement.tobs).label('TAVG'),
            func.max(Measurement.tobs).label('TMAX')
        ).filter(Measurement.date >= start_date.strftime('%Y-%m-%d')).all()

        # Check if results are empty
        if not results[0].TMIN:
            return jsonify({"error": "No data found for the given start date."}), 404

        # Format the results as a JSON response
        return jsonify({
            "Start Date": start,
            "TMIN": results[0].TMIN,
            "TAVG": results[0].TAVG,
            "TMAX": results[0].TMAX
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