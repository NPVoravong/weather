import datetime as dt
import numpy as np
import pandas as pd

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

engine = create_engine("sqlite:///./Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
m = Base.classes.measurement
s = Base.classes.station

# Create session (link) from Python to the DB
session = Session(engine)

app = Flask(__name__)

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start_date/end_date"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():

    #DT calculation for the last year
    last_date = session.query(m.date).order_by(m.date.desc()).first()[0]
    query_date = dt.datetime.strptime(last_date, '%Y-%m-%d') - dt.timedelta(days=366)

    # Query past year of precipitation data
    data = session.query(m.date, m.prcp).filter (m.date > query_date).all()

    p = {date: precip for date, precip in data}

    return jsonify(precipitation = p)

@app.route("/api/v1.0/stations")
def stations():
 
    # Query all stations
    stations = session.query(s.station, s.name).filter(s.station == m.station).group_by(s.name).all()

    return jsonify(stations = stations)

@app.route("/api/v1.0/tobs")
def tobs():

    #Find the station with the most temperature observations
    query_station = session.query(m.station).filter(s.station == m.station)\
    .group_by(m.station).order_by(func.count(m.tobs).desc()).first()

    #Query the last 12 months of temperature observation data for this station
    past_date = session.query(m.date).order_by(m.date.desc()).first()[0]
    date_query = dt.datetime.strptime(past_date, '%Y-%m-%d') - dt.timedelta(days=366)
    temperature_data = session.query(m.tobs).filter(m.date > date_query).filter(m.station == query_station[0]).all()

    temperature = list(np.ravel(temperature_data))

    return jsonify(temp = temperature)


@app.route("/api/v1.0/<start_date>")
@app.route("/api/v1.0/<start_date>/<end_date>")
def date_range(start_date = None, end_date = None):

    if not end_date:
        start = session.query(func.min(m.tobs), func.max(m.tobs), func.avg(m.tobs)).filter (m.date >= start_date).all()
        temperature = list(np.ravel(start))
        return jsonify(temperature)
    
    start_end = session.query(func.min(m.tobs), func.max(m.tobs), func.avg(m.tobs))\
        .filter(m.date >= start_date).filter(m.date <= end_date).all()
    temperature = list(np.ravel(start_end))
    return jsonify(temperature = temperature)

session.close()

if __name__ == '__main__':
    app.run(debug=True)

