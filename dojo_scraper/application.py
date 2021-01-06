from flask import Flask
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import os

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


@application.route('/listing/')
@application.route('/listing/<id>')
def detail(id=None):
    return render_template('detail.html', id=id)

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()

