from sqlalchemy.sql import func
import enum
from flask_login import UserMixin
from application import db

# MODELS 
class Status(enum.Enum):
    active = 1
    archived = 2
    deleted = 3

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(500), unique=False, nullable=False)
    url_zillow=db.Column(db.String(500), unique=False, nullable=True)
    url_redfin=db.Column(db.String(500), unique=False, nullable=True)
    url_cb=db.Column(db.String(500), unique=False, nullable=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'), nullable=True)
    agent = db.relationship('Agent', backref=db.backref('listing', lazy=True))
    price = db.Column(db.Integer, nullable=True)
    mls = db.Column(db.String(100), nullable=True)
    status = db.Column(db.Enum(Status), default=Status.active, nullable=False) 

    def __repr__(self):
        return '<Listing %r>' % self.address

class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    status = status = db.Column(db.Enum(Status), default=Status.active) 

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

class CollectionType(enum.Enum):
    one_time = 1
    weekly = 2

class DataCollection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    listing_ids = db.Column(db.ARRAY(db.Integer), nullable=True)
    collection_type = db.Column(db.Enum(CollectionType)) # one_time or weekly
    status = db.Column(db.Boolean, unique=False, default=False, nullable=True)
    errors = db.Column(db.ARRAY(db.String(1000)), nullable=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    token = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, unique=False, default=False)

class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100))
    email = db.Column(db.String(100))
    created_time = db.Column(db.DateTime(timezone=True), server_default=func.now())