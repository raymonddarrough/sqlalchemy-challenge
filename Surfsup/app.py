# Import the dependencies.
import datetime as dt
import numpy as np
import pandas as pd
import os

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
# engine = create_engine("sqlite:///Resources/hawaii.sqlite")
# Replace this line
# engine = create_engine("sqlite:///../Resources/hawaii.sqlite")

# With an absolute path
db_path = os.path.abspath("../Resources/hawaii.sqlite")
engine = create_engine(f"sqlite:///{db_path}")


# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine,reflect=True)

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

@app.route("/")
def welcome():
    return (
        f"Welcome to the Hawaii Climate Analysis API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end><br/>"
        f"To test the /api/v1.0/<start> route, you can use a URL like this: http://localhost:5000/api/v1.0/2016-08-23. This will return the TMIN, TAVG, and TMAX for all the dates greater than or equal to the start date of 2016-08-23.<br/>"
        f"To test the /api/v1.0/<start>/<end> route, you can use a URL like this: http://localhost:5000/api/v1.0/2016-08-23/2017-08-23. This will return the TMIN, TAVG, and TMAX for the dates between the start date of 2016-08-23 and the end date of 2017-08-23, inclusive."
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Calculate the date one year from the last date in data set.
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    most_recent_date_dt = dt.datetime.strptime(most_recent_date, '%Y-%m-%d')
    one_year_ago = most_recent_date_dt - dt.timedelta(days=365)

    # Perform a query to retrieve the data and precipitation scores
    results = session.query(Measurement.date, Measurement.prcp).\
              filter(Measurement.date >= one_year_ago).\
              order_by(Measurement.date).all()

    # Convert the query results to a dictionary
    precipitation_data = {}
    for date, prcp in results:
        precipitation_data[date] = prcp

    # Return the JSON representation of the dictionary
    return jsonify(precipitation_data)

@app.route("/api/v1.0/stations")
def stations():
    # Query the Station table for all stations
    results = session.query(Station.station).all()

    # Convert the results to a list of station names
    station_list = list(np.ravel(results))

    # Return the list as a JSON object
    return jsonify(station_list)

@app.route("/api/v1.0/tobs")
def tobs(): 
   # Find the most active station
    most_active_station = session.query(Measurement.station, func.count(Measurement.tobs))\
                                .group_by(Measurement.station)\
                                .order_by(func.count(Measurement.tobs).desc())\
                                .first()[0]

    # Calculate the date one year from the last date in data set
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    most_recent_date_dt = dt.datetime.strptime(most_recent_date, '%Y-%m-%d')
    one_year_ago = most_recent_date_dt - dt.timedelta(days=365)

    # Perform a query to retrieve the temperature observations for the most active station for the previous year
    temp_observations = session.query(Measurement.date, Measurement.tobs)\
                            .filter(Measurement.station == most_active_station)\
                            .filter(Measurement.date >= one_year_ago)\
                            .all()

    # Convert the query results to a list of dictionaries
    temp_list = []
    for date, tobs in temp_observations:
        temp_dict = {}
        temp_dict["date"] = date
        temp_dict["tobs"] = tobs
        temp_list.append(temp_dict)

    # Return a JSON list of the temperature observations
    return jsonify(temp_list)

@app.route('/api/v1.0/<start>')
def get_temps_start(start):
    # Return TMIN, TAVG, and TMAX for all dates greater than or equal to the start date.
    # Query the database for TMIN, TAVG, and TMAX
    results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs))\
        .filter(Measurement.date >= start).all()

    # Convert the query results to a list
    temps = list(np.ravel(results))

    # Return the results as a JSON object
    return jsonify(temps)


@app.route('/api/v1.0/<start>/<end>')
def get_temps_start_end(start, end):
    # Return TMIN, TAVG, and TMAX for dates between the start and end dates.
    # Query the database for TMIN, TAVG, and TMAX
    results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs))\
        .filter(Measurement.date >= start)\
        .filter(Measurement.date <= end).all()

    # Convert the query results to a list
    temps = list(np.ravel(results))

    # Return the results as a JSON object
    return jsonify(temps)


if __name__ == '__main__':
    app.run(debug=True)