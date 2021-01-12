from flask import Flask, render_template, Response, request, redirect, url_for, flash, current_app
from flask_login import UserMixin, LoginManager, login_user, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func, desc
import os
from base64 import b64encode
import io
import matplotlib 
from matplotlib.backends.backend_agg import FigureCanvasAgg
import time
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import date
import enum
from sqlalchemy import asc, Enum
import requests
import lxml.etree
import lxml.html
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
import ast
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from dotenv import load_dotenv # for working locally, to access the .env file
load_dotenv() # load the env vars from local .env


# EB looks for an 'application' callable by default.
application = Flask(__name__)
application.url_map.strict_slashes = False

# Keep the code in TESTING=True mode to avoid running the web scraper excessively
TESTING = True
#TESTING = False
# Use the test db by default, avoid corrupting the actual db
#application.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///dojo_test'

application.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
# Run this to setup the postgres db for the production db
# export DATABASE_URL="postgresql:///dojo_listings"

application.secret_key = os.environ.get("SECRET_KEY")

admin_email = os.environ.get("ADMIN_EMAIL")

application.config['MAIL_SERVER']='smtp.gmail.com'
application.config['MAIL_PORT'] = 465
application.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER")
application.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
application.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
application.config['MAIL_USE_TLS'] = False
application.config['MAIL_USE_SSL'] = True

mail = Mail(application)

TOKEN = os.environ.get("ACCESS_TOKEN")

db = SQLAlchemy(application)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(application)

application.debug = False

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# MODELS 
class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(500), unique=True, nullable=False)
    url_zillow=db.Column(db.String(500), unique=False, nullable=True)
    url_redfin=db.Column(db.String(500), unique=False, nullable=True)
    url_cb=db.Column(db.String(500), unique=False, nullable=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'), nullable=True)
    agent = db.relationship('Agent', backref=db.backref('listing', lazy=True))
    price = db.Column(db.Integer, nullable=True)
    mls = db.Column(db.String(100), nullable=True)

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

class CollectionType(enum.Enum):
    one_time = 1
    weekly = 2

class DataCollection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    listing_ids = db.Column(db.ARRAY(db.Integer), nullable=True)
    collection_type = db.Column(db.Enum(CollectionType)) # one_time or weekly

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    token = db.Column(db.String(100))

# WEB SCRAPER
class WebScraper:
    zillow_headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "cookie": "JSESSIONID=E988E25011499DF287B3336BE0E5F5F0; zguid=23|%2422236d48-1875-434d-b8f2-d1421d073afd; zgsession=1|2b52934e-1667-431f-9ec9-82007785df2a; _ga=GA1.2.1982612433.1604442799; _gid=GA1.2.620325738.1604442799; zjs_user_id=null; zjs_anonymous_id=%2222236d48-1875-434d-b8f2-d1421d073afd%22; _pxvid=92a1511a-1e24-11eb-8532-0242ac120018; _gcl_au=1.1.1767744341.1604442801; KruxPixel=true; DoubleClickSession=true; __gads=ID=41906d69e2453aa2-22d228f5397a006b:T=1604442801:S=ALNI_MYdXvUPJMu2Teg1lshpPkb5Ji_RVA; _fbp=fb.1.1604442801842.727886612; _pin_unauth=dWlkPU5EQmpaVGxoWkRrdE5qWTJPUzAwTVRJd0xUaGlNekF0TXpNeFlUZzVaREF3T0RReg; search=6|1607034817342%7Crect%3D40.78606556037442%252C-73.85258674621582%252C40.71688335199443%252C-74.20723915100098%26rid%3D25146%26disp%3Dmap%26mdm%3Dauto%26p%3D1%26z%3D1%26pt%3Dpmf%252Cpf%26fs%3D1%26fr%3D0%26mmm%3D1%26rs%3D0%26ah%3D0%26singlestory%3D0%26housing-connector%3D0%26abo%3D0%26garage%3D0%26pool%3D0%26ac%3D0%26waterfront%3D0%26finished%3D0%26unfinished%3D0%26cityview%3D0%26mountainview%3D0%26parkview%3D0%26waterview%3D0%26hoadata%3D1%26zillow-owned%3D0%263dhome%3D0%09%09%09%09%09%09%09%09; _px3=3429246752721cd227605773f1b990296844cc3b7adf99d73db1641b9fbd7524:HyhtsCiMCjoXm9YCLqUyYvVN6efdCzIdoSd+zu5Fou3woWXM3ouLAMEgw+vvoadA2GEfCRLJMBAtsdG3obEb2Q==:1000:WFzQZqPXu1SGFlXAM2Sa3b1ddSBnf/TdcWupq2Muc7NzUQfxNTQK9Mzpbt86RfiaHArwpcS4V3i9V+VEVoB7v58pm0C9FL2IkALrsTHHlQWQ25JMYDjgm8kPx8qWlas1+OSEOjGKwf+nuBKX7kjdN2KzMdxkpVySMkvEtZLoJ3k=; _uetsid=940faaa01e2411eb878aa964e2fb93d7; _uetvid=940ffda01e2411eb9bb3456f6030a021; AWSALB=lOVOVmEArl7Hkta9wCWOwWj3OzDo8E0zavfRORSHJRtpjlgqblhOKL0o7n0wNhn3CR7zrJpDRDgFMiPRuLsb/zny6hY2Ttw4KoOm5fRdnA2WU729Z1jXP6lLvtc5; AWSALBCORS=lOVOVmEArl7Hkta9wCWOwWj3OzDo8E0zavfRORSHJRtpjlgqblhOKL0o7n0wNhn3CR7zrJpDRDgFMiPRuLsb/zny6hY2Ttw4KoOm5fRdnA2WU729Z1jXP6lLvtc5; KruxAddition=true",
        "pragma": "no-cache",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36"
    }
    redfin_headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "cookie": "RF_CORVAIR_LAST_VERSION=338.2.1; RF_BROWSER_ID=68NeycsSR0u5ZYJe3HNFeg; RF_VISITED=false; RF_BID_UPDATED=1; RF_MARKET=newjersey; RF_BUSINESS_MARKET=41; AKA_A2=A; _gcl_au=1.1.594105178.1604444441; AMP_TOKEN=%24NOT_FOUND; _ga=GA1.2.241545075.1604444442; _gid=GA1.2.517680459.1604444442; _uetsid=65e404c01e2811eb9ad809962c95ca2f; _uetvid=65e44e601e2811eb93ecc7484b75a7c7; RF_BROWSER_CAPABILITIES=%7B%22screen-size%22%3A4%2C%22ie-browser%22%3Afalse%2C%22events-touch%22%3Afalse%2C%22ios-app-store%22%3Afalse%2C%22google-play-store%22%3Afalse%2C%22ios-web-view%22%3Afalse%2C%22android-web-view%22%3Afalse%7D; RF_LAST_SEARCHED_CITY=Hoboken; userPreferences=parcels%3Dtrue%26schools%3Dfalse%26mapStyle%3Ds%26statistics%3Dtrue%26agcTooltip%3Dfalse%26agentReset%3Dfalse%26ldpRegister%3Dfalse%26afCard%3D2%26schoolType%3D0%26lastSeenLdp%3DnoSharedSearchCookie; RF_LDP_VIEWS_FOR_PROMPT=%7B%22viewsData%22%3A%7B%2211-03-2020%22%3A%7B%22122200495%22%3A1%7D%7D%2C%22expiration%22%3A%222022-11-03T23%3A00%3A43.223Z%22%2C%22totalPromptedLdps%22%3A0%7D; FEED_COUNT=0%3Af; G_ENABLED_IDPS=google; RF_LISTING_VIEWS=122200495",
        "pragma": "no-cache",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36"
    }
    cb_headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "content-length": "0",
        "content-type": "text/plain",
        "cookie": "IDE=AHWqTUkqjk9aEsiwwq7Of_DhztqOLy8hRBhPMSenMOcZsNelDowpIl4Mng4ScA1C; DSID=AAO-7r7zzuHNo0Cqvl0Fu2PGvpAEl4mR_KdOuVZpergV7fKeY8emo1Tw4bZ-92VdKbS2-aT3jRqAQtTL_1TTcRMO9XDTZt3Lo7GiPdv5W4ku3JU9-fjNcE0",
        "origin": "https://www.coldwellbankerhomes.com",
        "pragma": "no-cache",
        "referer": "https://www.coldwellbankerhomes.com/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36",
        "x-client-data": "CKO1yQEIkLbJAQimtskBCMG2yQEIqZ3KAQi3uMoBCKvHygEI9sfKAQjpyMoBCNzVygEI/ZfLAQiRmcsBCMiZywEIl5rLARiLwcoB"
    }

    def scrape_listing(self, id=None):
        if not id:
            print("scrape_listing(): id required")
            return
        listing = Listing.query.filter_by(id=id).first()
        final_results = {
            "zillow": None,
            "redfin": None,
            "cb": None,
        }

        # zillow
        url_zillow = listing.url_zillow
        url_redfin = listing.url_redfin
        url_cb = listing.url_cb
        if listing.url_zillow and "zillow.com" in listing.url_zillow:
            url_zillow = listing.url_zillow
            r = requests.get(url=url_zillow, headers=self.zillow_headers)
            root = lxml.html.fromstring(r.content)
            results = root.xpath('//button[text()="Views"]/parent::div/parent::div/div')
            try: 
                zillow_views = int(results[1].text.replace(',',''))
            except (IndexError,ValueError) as e:
                zillow_views = None
            final_results["zillow"] = zillow_views
        
        # redfin 
        if listing.url_redfin and "redfin.com" in listing.url_redfin:
            url_redfin = listing.url_redfin
            r = requests.get(url=url_redfin, headers=self.redfin_headers)
            root = lxml.html.fromstring(r.content)
            try:
                redfin_views = int(root.xpath('//span[@data-rf-test-name="activity-count-label"]')[0].text.replace(',',''))
            except (IndexError,ValueError) as e:
                redfin_views = None
            final_results["redfin"] = redfin_views

        # cb 
        if listing.url_cb and "coldwellbankerhomes.com" in listing.url_cb:
            url_cb = listing.url_cb
            cb_request = requests.get(url=url_cb, headers=self.cb_headers)
            root = lxml.html.fromstring(cb_request.content)
            options = Options()
            options.headless = True
            driver = webdriver.Firefox(options=options)
            driver.set_page_load_timeout(30)
            #driver.implicitly_wait(30)
            driver.get(url_cb) 

            attempts = 0
            while attempts < 100: 
                try: 
                    #elem = driver.find_element_by_css_selector('body > section.content.single-photo-carousel > div:nth-child(2) > div.layout-main.property-details > div:nth-child(5) > div.toggle-body > div.details-block.details-block-full-property-details > div.col-1 > ul > li[-1]')
                    elem_parent = driver.find_element_by_xpath("//*[contains(text(),'Viewed:')]/parent::*")
                    print(url_cb)
                    print(elem_parent.get_attribute('innerText'))
                    views = elem_parent.get_attribute('innerText').split(" ")[1]
                    cb_views = int(views.replace(',',''))
                    final_results["cb"] = cb_views
                    break
                except NoSuchElementException:
                    attempts += 1
                    if attempts > 100: 
                        error_filename = f"{i}_url_err.log"
                        error_file = open(error_filename, 'w+')
                        error_file.write(driver.page_source)
                    else:
                        continue
                    
            driver.quit()

        existing_views = ListingViews.query.filter_by(listing_id=id).filter(ListingViews.date >= date.today()).first()
        if not existing_views:
            print("No ListingViews already found for this listing...")
            views = ListingViews(listing_id=id, listing=listing, views_zillow=final_results["zillow"], views_redfin=final_results["redfin"], views_cb=final_results["cb"] )
            db.session.add(views)
            db.session.commit()
        else:
            print("ListingViews already scraped today for this listing...")
            flash("Data already scraped today")
            existing_views.views_zillow = final_results["zillow"]
            existing_views.views_redfin = final_results["redfin"]
            existing_views.views_cb = final_results["cb"]
            db.session.add(existing_views)
            db.session.commit()

        print(f"Listing {id}, {listing.address}: Done scraping from all 3 urls ({url_zillow}, {url_redfin}, {url_cb}) results committed to the db.")

# ROUTES

@application.route("/hello/")
@application.route("/hello/<name>")
def hello(name=None):
    if name == None:
        name = "world"
    return "Hello, {}".format(name)

## AUTH ROUTES
### Login
@application.route("/login/")
@application.route("/login/<data>")
@application.route('/login', methods=["POST"])
def login(data=None):
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        remember = True if request.form.get("remember") else False

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash("Invalid email and/or password.")
            return redirect(url_for("login", data=dict(request.form)))

        login_user(user, remember=remember)
        return redirect(url_for("index"))
    # GET
    else:
        if request.args.get("data"):
            data = ast.literal_eval(request.args.get("data").rstrip('/'))    
        return render_template("login.html", data=data)

### Logout 
@application.route('/logout/')
@login_required
def logout():
    logout_user()
    return(redirect(url_for("login")))

### Register
### Register
@application.route("/register/")
@application.route('/register/<data>')
@application.route('/register/', methods=["POST"])
def register(data=None):
    if request.method == "POST":
        valid = True
        errors = []
        ## validate access token
        token = request.form.get("token")
        if not token:
            flash("Access token required. Contact your system administrator for a new token.")
            return redirect(url_for('register', data=dict(request.form)))

        elif token != TOKEN:
            flash("Invalid access token, please contact your system administrator")
            return redirect(url_for('register', data=dict(request.form)))

        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        if not password:
            valid = False
            flash("Password missing")
            return redirect(url_for("register", data=dict(request.form)))
        elif not password_confirm:
            valid = False
            #errors.append("Retype password")
            flash("Retype password")
            return redirect(url_for("register", data=dict(request.form)))
        elif password != password_confirm:
            valid = False
            #errors.append("Passwords must match")
            flash("Passwords must match")
            return redirect(url_for("register", data=dict(request.form)))
        elif len(password) < 8:
            flash("Password must be at least 8 characters long.")
            return redirect(url_for("register", data=dict(request.form)))

        user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

        if user: # if a user is found, we want to redirect back to signup page so user can try again
            flash('Email address already in use')
            return redirect(url_for('register', data=dict(request.form)))

        # create a new user with the form data. Hash the password so the plaintext version isn't saved.
        new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))
    # GET
    else:
        if request.args.get("data"):
            data = ast.literal_eval(request.args.get("data").rstrip('/'))
        return render_template('register.html', admin_email=admin_email, data=data)

@application.route("/reset-password/", methods=["GET", "POST"])
@application.route("/reset-password?<email>&<token>", methods=["GET", "POST"])
@login_required
def reset_password():
    if request.method == "POST":
        token = request.form.get("token")
        email = request.form.get("email")
        if token and email:
            # handle POST - check passwords, handle password reset
            
            # check the token and the user (based on the email)
            user = User.query.filter_by(email=email).first()
            if not user or token != user.token:
                flash("Invalid access token and/or email, please check your email for instructions on resetting your password. Make sure to check your spam folder!")
                return(redirect(url_for("login")))
            
            password = request.form.get("password")
            confirm_password = request.form.get("password-confirm")
            
            if not password:
                flash("Password missing")
                return render_template("reset_password.html", resetting=True, token=token, email=email)
            elif not confirm_password:
                flash("Retype password")
                return render_template("reset_password.html", resetting=True, token=token, email=email)
            elif password != confirm_password:
                flash("Passwords must match")
                return render_template("reset_password.html", resetting=True, token=token, email=email)
            elif len(password) < 8:
                flash("Password must be at least 8 characters long.")
                return render_template("reset_password.html", resetting=True, token=token, email=email)

            user.password = generate_password_hash(password, method='sha256')

            # save the changes in the db 
            db.session.add(user)
            db.session.commit()
            flash("Password successfully reset.")
            return redirect(url_for("login"))
        elif email:
            # handle POST - new password reset access token, url, and email
            user = User.query.filter_by(email=email).first()
            if user:
                # Create a token for the reset password link, save it in the db
                random_bytes = os.urandom(64)
                new_token = b64encode(random_bytes).decode('utf-8')
                user.token = new_token
                db.session.add(user)
                db.session.commit()
                
                # Send the token to user's email
                msg = Message('Hello', recipients = [email])
                msg.body = f"Please follow this link to reset your password: {request.base_url}?token={new_token}&email={email}"
                mail.send(msg)
            
            flash(f"An email has been sent to {email} with instructions to reset your password. Make sure to check your spam folder!")
            return redirect(url_for("reset_password"))
            
                    
        else:
            flash("Please provide an email to get instructions for resetting your password.")
            return redirect(url_for("reset_password"))
    # GET
    else:
        token = request.args.get("token")
        email = request.args.get("email")
        if not token and not email:
            return render_template("reset_password.html", resetting=False)
        else:
            # Check token and email before showing password reset form
            user = User.query.filter_by(email=email).first()
            if not user or not token or token != user.token:
                if token and token != user.token:
                    flash("Your password reset link is invalid or expired. Please provide your email for a new link.")
                else:
                    flash("Invalid access token and/or email, please check your email for instructions on resetting your password.")
                return(redirect(url_for("reset_password"))) 
            return render_template("reset_password.html", resetting=True, token=token, email=email)

## LISTINGS ROUTES 
## Listings - List View
@application.route('/')
@application.route('/<message>')
@login_required
def index(message=None):
    listings = Listing.query.all()
    return render_template('list.html', listings=listings, message=message)

## Listing - Detail View
@application.route('/listing/')
@application.route('/listing/<id>')
@login_required
def detail_listing(id=None):
    messages = []
    listing = Listing.query.filter_by(id=id).first()
    try:
        price = "${:,.2f}".format(listing.price)
    except (ValueError, TypeError, IndexError):
        messages.append("Price not formatted correctly")
        price = str(listing.price)
    return render_template('detail_listing.html', id=id, listing=listing, price=price, plot=True, messages=messages)

## Listing - Create  
@application.route('/listing/create/', methods=["GET", "POST"])
@login_required
def create(errors=None, prev_data=None):
    errors = request.args.getlist("errors")
    if request.args.get("prev_data"):
        prev_data = ast.literal_eval(request.args.get("prev_data").rstrip('/'))    
    valid = True
    if request.method == "POST":
        errors = []
        address = request.form["address"]
        price = request.form["price"]
        mls = request.form["mls"]
        url_zillow = request.form["url_zillow"]
        url_redfin = request.form["url_redfin"]
        url_cb = request.form["url_cb"]
        agent_id = request.form["agent"]
        agent = Agent.query.filter_by(id=agent_id).first()
        
        parsed_price = 0
        if not address:
            valid = False
            errors.append("Address is required")
        try:
            if price:
                parsed_price = int(price.replace("$","").replace(",",""))
                if parsed_price < 0:
                    valid = False
                    errors.append("Listing price cannot be negative")
        except ValueError: 
            valid = False
            errors.append(f"Price of {price} is invalid.")
        
        address_exists = len(Listing.query.filter_by(address=address).all()) > 0
        if address_exists:
            valid = False
            errors.append(f"Listing already exists with this address.")

        if url_zillow and "zillow.com" not in url_zillow:
            valid = False
            errors.append(f"Zillow URL should contain 'zillow.com'")
        if url_redfin and "redfin.com" not in url_redfin:
            valid = False
            errors.append(f"Redfin URL should contain 'redfin.com'")
        if url_cb and "coldwellbankerhomes.com" not in url_cb:
            valid = False
            errors.append(f"Coldwell Banker URL should contain 'coldwellbankerhomes.com'")

        if valid:
            listing = Listing(address=address, price=parsed_price, agent=agent, agent_id=agent_id, mls=mls, url_zillow=url_zillow, url_redfin=url_redfin, url_cb=url_cb)
            db.session.add(listing)
            db.session.commit()
            return redirect(url_for('detail_listing', id=listing.id))
        else:
            agents = Agent.query.all()
            default_agent = Agent.query.filter_by(name="Jill Biggs").first()
            return redirect(url_for("create", errors=errors, prev_data=dict(request.form)))
    # GET 
    else:
        # if there are errors, reload the page content, 
        # otherwise create a new empty form     
        agents = Agent.query.all()
        default_agent = Agent.query.filter_by(name="Jill Biggs").first()
        if errors:
            return render_template('create_listing.html', agents=agents, default_agent=default_agent, errors=errors, data=prev_data)
        return render_template('create_listing.html', agents=agents, default_agent = default_agent)

## Listing - Edit 
@application.route('/listing/<id>/edit', methods=["GET", "POST"])
@login_required
def edit_listing(id=None, errors=None, prev_data=None):
    errors = request.args.getlist("errors")
    if request.args.get("prev_data"):
        prev_data = ast.literal_eval(request.args.get("prev_data").rstrip('/'))    
    valid = True
    if request.method == "POST":
        errors = []
        address = request.form["address"]
        price = request.form["price"]
        mls = request.form["mls"]
        url_zillow = request.form["url_zillow"]
        url_redfin = request.form["url_redfin"]
        url_cb = request.form["url_cb"]
        agent_id = request.form["agent"]
        agent = Agent.query.filter_by(id=agent_id).first()

        if not address:
            valid = False
            errors.append("Address is required")
        
        try:
            if price:
                parsed_price = int(price.replace("$","").replace(",",""))
                if parsed_price < 0:
                    valid = False
                    errors.append("Listing price cannot be negative")
        except ValueError: 
            valid = False
            errors.append(f"Price of {price} is invalid.")
        
        listing = Listing.query.filter_by(id=id).first()
        prev_address = listing.address
        
        address_exists = len(Listing.query.filter_by(address=address).filter(address!=prev_address).all()) > 0
        if address_exists:
            valid = False
            errors.append(f"Listing already exists with this address.")

        if url_zillow and "zillow.com" not in url_zillow:
            valid = False
            errors.append(f"Zillow URL should contain 'zillow.com'")
        if url_redfin and "redfin.com" not in url_redfin:
            valid = False
            errors.append(f"Redfin URL should contain 'redfin.com'")
        if url_cb and "coldwellbankerhomes.com" not in url_cb:
            valid = False
            errors.append(f"Coldwell Banker URL should contain 'redfin.com'")

        listing = Listing.query.filter_by(id=id).first()
        agents = Agent.query.all()

        if valid:
            listing = Listing.query.filter_by(id=id).first()
            listing.address = address
            listing.price = price
            listing.mls = mls
            listing.url_zillow = url_zillow
            listing.url_redfin = url_redfin
            listing.url_cb = url_cb
            listing.agent = agent
            listing.agent_id = agent_id
            db.session.add(listing)
            db.session.commit()
        else:
            agents = Agent.query.all()
            default_agent = Agent.query.filter_by(name="Jill Biggs").first()
            if errors:
                return render_template('create_listing.html', agents=agents, default_agent=default_agent, errors=errors, data=prev_data)
            return redirect(url_for("edit_listing", id=id, errors=errors, prev_data=dict(request.form)))
        return redirect(url_for('detail_listing', id=id))
    else: 
        if not id:
            print("Missing ID")
            return
        agents = Agent.query.all()
        listing = Listing.query.filter_by(id=id).first()
        if errors:
            return render_template('detail_listing.html', id=id, listing=listing, agents=agents, errors=errors, data=prev_data)
        return render_template('detail_listing.html', id=id, listing=listing, agents=agents, editing=True)

## Listing - Delete 
@application.route('/listing/<id>/delete')
@login_required
def delete_listing(id=None):
    listing = Listing.query.filter_by(id=id).first()
    address = listing.address
    db.session.delete(listing)
    db.session.commit()
    message = f"Listing ({address}) deleted successfully."
    return redirect(url_for("index", message=message))

## AGENT ROUTES
## Agents - List  
@application.route('/agents/')
@application.route('/agents/<message>')
@login_required
def agents(message=None):
    agents = Agent.query.all()
    return render_template('list_agents.html', agents=agents, message=message)

## Agent - Detail 
@application.route('/agent/')
@application.route('/agent/<id>')
@login_required
def detail_agent(id=None):
    agent = Agent.query.filter_by(id=id).first()
    return render_template('detail_agent.html', id=id, agent=agent)

## Agent - Create
@application.route('/agent/create/', methods=["GET", "POST"])
@login_required
def create_agent(errors=None, prev_data=None):
    errors = request.args.getlist("errors")
    if request.args.get("prev_data"):
        prev_data = ast.literal_eval(request.args.get("prev_data").rstrip('/')) 
    valid = True
    if request.method == "POST":
        errors = []
        name = request.form["name"]
        
        if not name:
            valid = False
            errors.append("Name is required")
        
        agent_exists = len(Agent.query.filter_by(name=name).all()) > 0
        if agent_exists:
            valid = False
            errors.append(f"Agent already exists with this name.")

        if valid:
            agent = Agent(name=name)
            db.session.add(agent)
            db.session.commit()
            return redirect(url_for('detail_agent', id=agent.id))
        else:
            agents = Agent.query.all()
            default_agent = Agent.query.filter_by(name="Jill Biggs").first()
            return redirect(url_for("create_agent", errors=errors, prev_data=dict(request.form)))
    # GET 
    else:
        # if there are errors, reload the page content, 
        # otherwise create a new empty form   
        if errors:
            return render_template('create_agent.html', errors=errors, data=prev_data)
        return render_template('create_agent.html')

## Agent - Edit
@application.route('/agent/<id>/edit', methods=["GET", "POST"])
@login_required
def agent_edit(id=None, errors=None, prev_data=None):
    errors = request.args.getlist("errors")
    if request.args.get("prev_data"):
        prev_data = ast.literal_eval(request.args.get("prev_data").rstrip('/'))    
    valid = True
    if request.method == "POST":
        errors = []
        name = request.form["name"]

        if not name:
            valid = False
            errors.append("Name is required")
        
        agent = Agent.query.filter_by(id=id).first()
        prev_name = agent.name

        name_exists = len(Agent.query.filter_by(name=name).filter(name!=prev_name).all()) > 0
        if name_exists:
            valid = False
            errors.append(f"Agent already exists with this name.")

        if valid:
            agent.name = name
            db.session.add(agent)
            db.session.commit()
        else:
            if errors:
                return render_template('detail_agent.html', id=id, agent=agent, errors=errors, data=prev_data)
            return redirect(url_for("agent_edit", id=id, agent=agent, errors=errors, prev_data=dict(request.form)))
        return redirect(url_for("detail_agent", id=id))
    else: 
        if not id:
            print("Missing ID")
            return
        agent = Agent.query.filter_by(id=id).first()
        if errors:
            return render_template('detail_agent.html', id=id, agent=agent, errors=errors, data=prev_data, editing=True)
        return render_template('detail_agent.html', id=id, agent=agent, editing=True)

## Agent - Delete
@application.route('/agent/<id>/delete')
@login_required 
def delete_agent(id=None):
    agent = Agent.query.filter_by(id=id).first()
    name = agent.name
    db.session.delete(agent)
    db.session.commit()
    message = f"Agent ({name}) deleted successfully."
    return redirect(url_for("agents", message=message))

## Logs - List View
@application.route('/logs/')
@login_required
def list_logs():
    logs = DataCollection.query.order_by(desc(DataCollection.date)).all()
    return render_template("list_logs.html", logs=logs)

## Logs - Detail View
@application.route('/log/')
@application.route('/log/<id>')
@login_required
def detail_log(id=None):
    log = DataCollection.query.filter_by(id=id).first()
    listings = [Listing.query.filter_by(id=listing_id).first() for listing_id in log.listing_ids]
    return render_template('detail_log.html', id=id, log=log, listings=listings)

## Generates plot of listing views (views per day) for a given Listing ID.
@application.route("/matplot-as-image-<int:id>.png")
@login_required
def plot_png(id=None):
    """ renders the plot on the fly.
    """
    views = ListingViews.query.filter_by(listing_id=id).order_by(asc(ListingViews.date)).all()
    # @ TODO - Limit to 1 ListingViews object per day, choose the largest value. This will allow for cases where a second run was done on top of the first. 
    x = []
    y_zillow = []
    y_redfin = []
    y_cb = []
    for view in views: 
        x.append(view.date.strftime("%m/%d/%Y"))
        y_zillow.append(view.views_zillow)
        y_redfin.append(view.views_redfin)
        y_cb.append(view.views_cb)

    dataObject = {
        "x": x,
        "y_z": y_zillow, 
        "y_r": y_redfin,
        "y_c": y_cb
    }

    df=pd.DataFrame(dataObject)

    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.plot( 'x', 'y_z', data=df, marker='o', markerfacecolor='blue', markersize=12, color='skyblue', linewidth=4, label="zillow")
    axis.plot( 'x', 'y_r', data=df, marker='o', markerfacecolor='red', markersize=12, color='red', linewidth=4, label="redfin")
    axis.plot( 'x', 'y_c', data=df, marker='o', markerfacecolor='olive', markersize=12, color='olive', linewidth=4, label="cb")
    axis.legend()
    
    for x,y in zip([] + x + x + x, [] + y_zillow + y_redfin + y_cb):
        # add labels to the points
        if isinstance(x, str) and isinstance(y, int):
            try:
                axis.annotate(
                        y, 
                        (x,y),
                        textcoords="offset points", # how to position the text
                        bbox=dict(boxstyle="round", fc="white", ec="black"),
                        xytext=(0,10), # distance from text to points (x,y)
                        ha='center') # horizontal alignment can be left, right or center.          
            except TypeError:
                continue

    output = io.BytesIO()
    FigureCanvasAgg(fig).print_png(output)
    
    return Response(output.getvalue(), mimetype="image/png")

## Helper - Scrapes all the listings passed in the input array using the WebScraper class
def scrape_listings(listings=None):
    if not listings:
        print("scrape_listings(): No listings to scrape.")
    scraper = WebScraper()
    for listing in listings: 
        scraper.scrape_listing(listing.id)

## Scrapes listing views for today for a given Listing ID. Updates the db directly once the results are retrieved.
@application.route('/scrape/<id>/')
@login_required
def scraper(id=None):
    listing = Listing.query.filter_by(id=id).first()
    if TESTING:
        print("Not actually scraping... in TESTING mode")
    else:
        scrape_listings([listing])
    
    # Add web scraper run to the DataCollection log
    log_data_collection(CollectionType.one_time, [listing])
    
    return redirect(url_for('detail_listing', id=id))

## Scrapes listing views for today for all Listings. Updates the db as the results are found. 
@application.route('/scrape/all/')
@login_required
def scrapeAll(id=None):
    listings = Listing.query.all()
    if TESTING:
        print("Not actually scraping... in TESTING mode")
    else:
        scrape_listings(listings)
    
    # Log scraping event
    log_data_collection(CollectionType.one_time, listings)
    
    # Redirect to the home page (Listings - List View)
    return redirect(url_for('index', id=id))

@application.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404

@application.errorhandler(403)
def forbidden_page(e):
    # note that we set the 403 status explicitly
    return render_template('403.html'), 403

@application.errorhandler(500)
def internal_server_error(e):
    # note that we set the 500 status explicitly
    return render_template('500.html'), 500

def scrape_listings_weekly():
    # Retrieve all of the current listings
    listings = Listing.query.all()

    if TESTING:
        print("Not actually scraping... in TESTING mode")
    else:
        scrape_listings(listings)

    # Log scraping event
    log_data_collection(CollectionType.weekly, listings)

    # Email admin if they exist
    admin_email = os.environ.get("ADMIN_EMAIL")
    if admin_email:
        # within this block, current_app points to app.
        #print(current_app.name)
        #print("current_app")
        #print(current_app)
        #print(current_app.request)
        body = f"Property views were scraped for this week."
        send_email([admin_email], "JBG Listings - Weekly Listings Report", body)

def send_email(recipients, title, body):
    with application.app_context():
        msg = Message(title, recipients=recipients)
        msg.body = body
        current_app.extensions['mail'].send(msg)
        #current_app.mail.send(msg)

def log_data_collection(collection_type=None, listings=[]):
    if not collection_type:
        return
    listing_ids = [listing.id for listing in listings]
    data_collection = DataCollection(listing_ids=listing_ids, collection_type=collection_type)
    db.session.add(data_collection)
    db.session.commit()

# Set up weekly cron job for scraping the listings
# Only when running in the child reloader process.
# Prevent the scheduler from running in the master 
# process. 
#if not application.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    
scheduler = BackgroundScheduler(daemon=True)
scheduler.configure(timezone='est')

# Every Friday at 5:30 pm 
scheduler.add_job(scrape_listings_weekly, 'cron', day_of_week="fri", hour=17, minute=30)

# Every minute - TEST
scheduler.add_job(scrape_listings_weekly,'cron',minute="*")
    
# Check which jobs are scheduled
# scheduler.print_jobs()

scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

# Run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output.
    # REMOVE BEFORE DEPLOYING.
    #application.debug = False

    application.run(use_reloader=False)
