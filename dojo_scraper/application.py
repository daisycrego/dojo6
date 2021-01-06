from flask import Flask, render_template, Response, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import os
from base64 import b64encode
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import date
from sqlalchemy import asc

# EB looks for an 'application' callable by default.
application = Flask(__name__)

application.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
# export DATABASE_URL="postgresql:///dojo_listings"
#application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(application)

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(80), unique=True, nullable=False)
    url_zillow=db.Column(db.String(120), unique=True, nullable=True)
    url_redfin=db.Column(db.String(120), unique=True, nullable=True)
    url_cb=db.Column(db.String(120), unique=True, nullable=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'), nullable=True)
    agent = db.relationship('Agent', backref=db.backref('listings', lazy=True))

    def __repr__(self):
        return '<Listing %r>' % self.address


class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return '<Agent %r>' % self.name


class ListingViews(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    views_zillow = db.Column(db.Integer, nullable=True)
    views_redfin = db.Column(db.Integer, nullable=True)
    views_cb = db.Column(db.Integer, nullable=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=True)
    listing = db.relationship('Listing', backref=db.backref('listingviews', lazy=True))

    def __repr__(self):
        return '<ListingViews for %r>' % self.listing_id


@application.route('/')
def index():
    listings = Listing.query.all()
    return render_template('list.html', listings=listings)

@application.route('/help/')
def help():
    return render_template('help.html')

@application.route("/matplot-as-image-<int:id>.png")
def plot_png(id=None):
    """ renders the plot on the fly.
    """
    print(f"plotting listing views on the fly for `${id}`")
    views = ListingViews.query.filter_by(listing_id=id).order_by(asc(ListingViews.date)).all()
    print("VIEWS")
    print(views)
    x = []
    y_zillow = []
    y_redfin = []
    y_cb = []
    for view in views: 
        x.append(view.date.strftime("%m/%d/%Y"))
        print(view.date.isoformat())
        print(type(view.date))
        y_zillow.append(view.views_zillow)
        y_redfin.append(view.views_redfin)
        y_cb.append(view.views_cb)
    #print(zillow)
    #print(redfin)
    #print(cb)
    dataObject = {
        "x": x,
        "y_z": y_zillow, 
        "y_r": y_redfin,
        "y_c": y_cb
    }
    print(dataObject)
    df=pd.DataFrame(dataObject)

    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    #axis.plot(x_points, [random.randint(1, 30) for x in x_points])
    axis.plot( 'x', 'y_z', data=df, marker='o', markerfacecolor='blue', markersize=12, color='skyblue', linewidth=4, label="zillow")
    axis.plot( 'x', 'y_r', data=df, marker='o', markerfacecolor='red', markersize=12, color='red', linewidth=4, label="redfin")
    axis.plot( 'x', 'y_c', data=df, marker='o', markerfacecolor='olive', markersize=12, color='olive', linewidth=4, linestyle='dashed', label="cb")
    axis.legend()


    output = io.BytesIO()
    FigureCanvasAgg(fig).print_png(output)
    return Response(output.getvalue(), mimetype="image/png")

@application.route('/listing/')
@application.route('/listing/<id>')
def detail(id=None):
    listing = getListing(id)
    return render_template('detail.html', id=id, listing=listing, plot=True)

def getListing(id=None):
    if not id: 
        print("Listing ID missing")
        return None
    return Listing.query.filter_by(id=id).first()

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()

