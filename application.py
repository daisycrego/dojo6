from flask import Flask, render_template, Response, request, redirect, url_for, flash, current_app
from flask_login import UserMixin, LoginManager, login_user, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func, desc
import os
from base64 import b64encode
import io
import matplotlib 
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime
from datetime import date, timedelta, time
import enum
from sqlalchemy import asc
import requests
import ast
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import random, string
from smtplib import SMTPDataError
from web_scraper import *
from dotenv import load_dotenv # for working locally, to access the .env file
load_dotenv() # load the env vars from local .env


# EB looks for an 'application' callable by default.
application = Flask(__name__)
application.url_map.strict_slashes = False

# Keep the code in TESTING=True mode to avoid running the web scraper excessively
TESTING = False
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

from models import *

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(application)

application.debug = False

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ROUTES

## Invite New User
@application.route("/invite-user/", methods=["POST"])
@login_required
def invite_user():
    if not current_user.is_admin:
        flash("You don't have the privileges to perform this task.")
        return redirect(url_for("settings"))
    email = request.form.get("email")
    if not email:
        flash("Please provide an email for the invitation.")
        return redirect(url_for("settings"))

    user_exists = User.query.filter_by(email=email).first()
    if user_exists:
        flash("A user with this email already exists.")
        return redirect(url_for("settings"))

    title = "JBG Listings - Create My Account"
    new_token = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))
    
    # delete any existing tokens for this email
    existing_tokens = Token.query.filter_by(email=email).all()
    for token in existing_tokens:
        db.session.delete(token)
        db.session.commit()
    
    # create a new token and email it
    token = Token(email=email, token=new_token)
    db.session.add(token)
    db.session.commit()
    body = f"Welcome to the JBG Listings Portal!\n\nPlease follow this link to create your account: {request.base_url}../register?token={new_token}&email={email}"
    sent = send_email([email], title, body)

    if sent: 
        flash(f"An invitation was emailed to {email}")
    else:
        flash(f"An invitation was NOT emailed to {email} due to email server issues. Please contact your system administrator.")
    return redirect(url_for("settings"))

## Settings
@application.route("/settings/")
def settings():
    return render_template("settings.html", is_admin=current_user.is_admin)

@application.route("/settings/edit", methods=["GET", "POST"])
@login_required
def settings_edit(prev_data=None):
    if request.args.get("prev_data"):
        prev_data = ast.literal_eval(request.args.get("prev_data").rstrip('/'))    
    if request.method == "POST":
        valid = True
        name = request.form.get("name")
        email = request.form.get("email")
        if not name and not email:
            flash("No changes detected.")
            valid = False
        elif name == current_user.name and email == current_user.email:
            flash("No changes detected.")
            valid = False

        # check if email is taken
        user_exists = User.query.filter_by(email=email).filter(email!=current_user.email).first()
        if user_exists: 
            flash("Email already taken.")
            valid = False

        if valid: 
            if name and name != current_user.name:
                current_user.name = name
            if email and email != current_user.email:
                current_user.email = email
            db.session.add(current_user)
            db.session.commit()
            flash("Profile updated.")
            return redirect(url_for("settings"))
        else: 
            if prev_data:
                return render_template('settings.html', data=prev_data, is_admin=current_user.is_admin)
            else:
                return render_template('settings.html', data=dict(request.form), is_admin=current_user.is_admin)
    else:
        if prev_data:
            return render_template("settings.html", is_admin=current_user.is_admin, data=prev_data, editing=True)
        return render_template("settings.html", is_admin=current_user.is_admin, editing=True)

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
        #if request.args.get("data"):
        #    data = ast.literal_eval(request.args.get("data").rstrip('/'))    
        return render_template("login.html")

### Logout 
@application.route('/logout/')
@login_required
def logout():
    logout_user()
    return(redirect(url_for("login")))

### Register
### Register
@application.route("/register/")
@application.route('/register/<data>&<token>')
@application.route('/register/', methods=["POST"])
def register(data=None):
    
    if request.method == "POST":
        valid = True
        errors = []
        ## validate access token
        token = request.form.get("token")
        if not token:
            flash("Invitation required to create an account. Please contact your system administrator.")
            return redirect(url_for('login'))

        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        one_hour_ago = datetime.datetime.now() - timedelta(hours=1)
        active_token = Token.query.filter_by(token=token).filter_by(email=email).filter(Token.created_time > one_hour_ago).first()
        if not active_token:
            flash("Invalid access token, please contact your system administrator")
            return redirect(url_for('register', data=dict(request.form)))

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
        new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'), is_admin=False)

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))
    # GET
    else:
        token = request.args.get("token")
        if not token: 
            flash("Please check your email for a registration link. Contact your system administrator if you don't receive an email. Make sure to check your spam folder.")
        one_hour_ago = datetime.datetime.now() - timedelta(hours=1)
        active_token = Token.query.filter_by(token=token).filter(Token.created_time > one_hour_ago).first()
        if not active_token:
            flash("Your registration link is expired. Please contact your system administrator for a new invitation.")
            return redirect(url_for("login"))
        
        if request.args.get("data"):
            data = ast.literal_eval(request.args.get("data").rstrip('/'))
        return render_template('register.html', admin_email=admin_email, data=data, token=token)

def send_email(recipients, title, body):
    with application.app_context():
        # within this block, current_app points to app.
        msg = Message(title, recipients=recipients)
        msg.body = body
        # accessing the flask-mail app extension using the app_context (current_app)
        try:
            current_app.extensions['mail'].send(msg)
            return True
        except SMTPDataError: 
            print("Daily limits exceeded for primary Gmail SMTP server, switching to backup SMTP server.")
            current_app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("BACKUP_EMAIL")
            current_app.config["MAIL_USERNAME"] = os.environ.get("BACKUP_EMAIL")
            current_app.extensions['mail'] = Mail(current_app)
            try: 
                current_app.extensions['mail'].send(msg)
                return True
            except SMTPDataError:
                if current_app.config["MAIL_USERNAME"] == os.environ.get("BACKUP_EMAIL"):
                    print("MAIL_USERNAME has been set to the backup, but email limits also exceeded on the backup")
                    return False
                else:
                    print("Limits still exceeded, but MAIL_USERNAME has not been set to backup.")
        return False 

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
            one_hour_ago = datetime.datetime.now() - timedelta(hours=1)
            active_token = Token.query.filter_by(token=token).filter_by(email=email).filter(Token.created_time > one_hour_ago).first()
            if not user or not active_token:
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
                # delete any existing tokens for this email
                existing_tokens = Token.query.filter_by(email=email).all()
                for token in existing_tokens:
                    db.session.delete(token)
                    db.session.commit()
                new_token = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))
                token = Token(email=user.email, token=new_token)
                db.session.add(token)
                db.session.commit()
                
                # Send the token to user's email
                title = "Password Reset"
                body = f"Please follow this link to reset your password: {request.base_url}?token={new_token}&email={email}"
                sent = send_email([email], title, body)
            if sent:
                flash(f"An email has been sent to {email} with instructions to reset your password. Make sure to check your spam folder!")
            else:
                flash("Unable to send to email with reset instructions. Please contact your system administrator.")
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
            if not email:
                flash("Invalid reset link, please check your email for instructions on resetting your password.")
            
            # Check token and email before showing password reset form
            user = User.query.filter_by(email=email).first()
            
            if not user or not token:
                flash("Invalid reset link, please check your email for instructions on resetting your password.")
            else:
                one_hour_ago = datetime.datetime.now() - timedelta(hours=1)
                active_token = Token.query.filter_by(token=token).filter_by(email=email).filter(Token.created_time > one_hour_ago).first()
                if not active_token:
                    flash("Reset link is expired. Please provide your email and request a new reset password link.")
                    return(redirect(url_for("reset_password"))) 
            return render_template("reset_password.html", resetting=True, token=token, email=email)

## LISTINGS ROUTES 
## Listings - List View
@application.route('/')
@application.route('/<show_inactive>')
@login_required
def index(show_inactive=None):
    if not show_inactive:
        show_inactive = request.args.get("show_inactive")
    show_inactive = True if show_inactive == "True" else False
    listings = Listing.query.filter(Listing.status!=Status.deleted).all()
    return render_template('list.html', listings=listings, show_inactive=show_inactive)

@application.route('/listings/deleted')
@login_required
def deleted_listings():
    listings = Listing.query.filter_by(status=Status.deleted).all()
    return render_template('deleted_listings.html', listings=listings)

@application.route("/toggle_inactive/<type>/", methods=["POST"])
@login_required
def toggle_inactive(type=None):
    if not type:
        type = request.args.get("type")
        print(f"toggle_inactive(): type: {type}")
    show_inactive = request.form.get("show_inactive")
    print(f"toggle_inactive(): Toggling inactive to {show_inactive}")
    if type == "listing": 
        return redirect(url_for('index', show_inactive=show_inactive))
    elif type == "agent": 
        return redirect(url_for('agents', show_inactive=show_inactive))
    else: 
        print(f"Type {type} not valid.")
        return redirect(url_for('index'))

## Listing - Detail View
@application.route('/listing/')
@application.route('/listing/<id>')
@login_required
def detail_listing(id=None, errors=None):
    errors = request.args.getlist("errors")
    statuses = dict()
    for category in Status:
        statuses.update({category.value: category.name})
    print(statuses)
    listing = Listing.query.filter_by(id=id).first()
    try:
        price = "${:,.2f}".format(listing.price)
    except (ValueError, TypeError, IndexError):
        flash("Price not formatted correctly")
        price = str(listing.price)
    if errors:
        flash(f"{errors[0]}. For more details, please see the Logs.")
    return render_template('detail_listing.html', id=id, listing=listing, price=price, plot=True, statuses=statuses)

## Listing - Create  
@application.route('/listing/create/', methods=["GET", "POST"])
@login_required
def create(prev_data=None):
    if request.args.get("prev_data"):
        prev_data = ast.literal_eval(request.args.get("prev_data").rstrip('/'))    
    valid = True
    if request.method == "POST":
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
            flash("Address is required")
        try:
            if price:
                parsed_price = int(price.replace("$","").replace(",",""))
                if parsed_price < 0:
                    valid = False
                    flash("Listing price cannot be negative")
        except ValueError: 
            valid = False
            flash(f"Price of {price} is invalid.")
        
        address_exists = len(Listing.query.filter_by(address=address).all()) > 0
        if address_exists:
            valid = False
            flash(f"Listing already exists with this address.")

        if url_zillow and "zillow.com" not in url_zillow:
            valid = False
            flash(f"Zillow URL should contain 'zillow.com'")
        if url_redfin and "redfin.com" not in url_redfin:
            valid = False
            flash(f"Redfin URL should contain 'redfin.com'")
        if url_cb and "coldwellbankerhomes.com" not in url_cb:
            valid = False
            flash(f"Coldwell Banker URL should contain 'coldwellbankerhomes.com'")

        if valid:
            listing = Listing(address=address, price=parsed_price, agent=agent, agent_id=agent_id, mls=mls, url_zillow=url_zillow, url_redfin=url_redfin, url_cb=url_cb)
            db.session.add(listing)
            db.session.commit()
            return redirect(url_for('detail_listing', id=listing.id))
        else:
            agents = Agent.query.all()
            default_agent = Agent.query.filter_by(name="Jill Biggs").first()
            return redirect(url_for("create", prev_data=dict(request.form)))
    # GET 
    else:
        # if there are errors, reload the page content, 
        # otherwise create a new empty form     
        agents = Agent.query.all()
        default_agent = Agent.query.filter_by(name="Jill Biggs").first()

        if prev_data:
            return render_template('create_listing.html', agents=agents, default_agent=default_agent, data=prev_data)
        return render_template('create_listing.html', agents=agents, default_agent = default_agent)

## Listing - Edit 
@application.route('/listing/<id>/edit', methods=["GET", "POST"])
@login_required
def edit_listing(id=None, prev_data=None):
    statuses = dict()
    for category in Status:
        statuses.update({category.value: category.name})
    print(statuses)
    if request.args.get("prev_data"):
        prev_data = ast.literal_eval(request.args.get("prev_data").rstrip('/'))    
    valid = True
    if request.method == "POST":
        address = request.form.get("address")
        price = request.form.get("price")
        mls = request.form.get("mls")
        url_zillow = request.form.get("url_zillow")
        url_redfin = request.form.get("url_redfin")
        url_cb = request.form.get("url_cb")
        agent_id = request.form.get("agent")
        agent = Agent.query.filter_by(id=agent_id).first()
        status = request.form.get("status")
        print(f"status: {status} is just a number")
        if not status:
            valid = False
            flash("Status is required")
            return redirect(url_for('detail_listing', id=id))
        
        status = Status(int(status)) # this should now be an enum
        print(f"enum option: {type(status)}")

        if not address:
            valid = False
            flash("Address is required")

        try:
            if price:
                parsed_price = int(price.replace("$","").replace(",",""))
                if parsed_price < 0:
                    valid = False
                    flash("Listing price cannot be negative")
        except ValueError: 
            valid = False
            flash(f"Price of {price} is invalid.")
        
        listing = Listing.query.filter_by(id=id).first()
        prev_address = listing.address
        
        address_exists = len(Listing.query.filter_by(address=address).filter(address!=prev_address).all()) > 0
        if address_exists:
            valid = False
            flash(f"Listing already exists with this address.")

        if url_zillow and "zillow.com" not in url_zillow:
            valid = False
            flash(f"Zillow URL should contain 'zillow.com'")
        if url_redfin and "redfin.com" not in url_redfin:
            valid = False
            flash(f"Redfin URL should contain 'redfin.com'")
        if url_cb and "coldwellbankerhomes.com" not in url_cb:
            valid = False
            flash(f"Coldwell Banker URL should contain 'redfin.com'")

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
            listing.status = status
            db.session.add(listing)
            db.session.commit()
        else:
            agents = Agent.query.all()
            default_agent = Agent.query.filter_by(name="Jill Biggs").first()            
            if prev_data:
                return render_template('detail_listing.html', listing=listing, agents=agents, default_agent=default_agent, data=prev_data, editing=True, statuses=statuses)
            else:
                return render_template('detail_listing.html', listing=listing, agents=agents, default_agent=default_agent, data=dict(request.form), editing=True, statuses=statuses)
            #else:
            #    return redirect(url_for("edit_listing", id=id, prev_data=dict(request.form)))
        return redirect(url_for('detail_listing', id=id))
    else: 
        if not id:
            print("Missing ID")
            return
        agents = Agent.query.all()
        listing = Listing.query.filter_by(id=id).first()
        if prev_data:
            return render_template('detail_listing.html', listing=listing, agents=agents, data=prev_data, editing=True, statuses=statuses)
        return render_template('detail_listing.html', listing=listing, agents=agents, editing=True, statuses=statuses)

## AGENT ROUTES
## Agents - List  
@application.route('/agents/')
@application.route('/agents/<show_inactive>')
@login_required
def agents(show_inactive=None):
    if not show_inactive:
        show_inactive = request.args.get("show_inactive")
    show_inactive = True if show_inactive == "True" else False
    agents = Agent.query.filter(Agent.status!=Status.deleted).all()
    return render_template('list_agents.html', agents=agents, show_inactive=show_inactive)

@application.route('/agents/deleted')
@login_required
def deleted_agents():
    agents = Agent.query.filter_by(status=Status.deleted).all()
    return render_template('deleted_agents.html', agents=agents)

## Agent - Detail 
@application.route('/agent/')
@application.route('/agent/<id>')
@login_required
def detail_agent(id=None):
    agent = Agent.query.filter_by(id=id).first()
    return render_template('detail_agent.html', agent=agent)

## Agent - Create
@application.route('/agent/create/', methods=["GET", "POST"])
@login_required
def create_agent(prev_data=None):
    if request.args.get("prev_data"):
        prev_data = ast.literal_eval(request.args.get("prev_data").rstrip('/')) 
    valid = True
    if request.method == "POST":
        name = request.form["name"]
        
        if not name:
            valid = False
            flash("Name is required")
        
        agent_exists = len(Agent.query.filter_by(name=name).all()) > 0
        if agent_exists:
            valid = False
            flash(f"Agent already exists with this name.")

        if valid:
            agent = Agent(name=name)
            db.session.add(agent)
            db.session.commit()
            return redirect(url_for('detail_agent', id=agent.id))
        else:
            agents = Agent.query.all()
            default_agent = Agent.query.filter_by(name="Jill Biggs").first()
            return redirect(url_for("create_agent", prev_data=dict(request.form)))
    # GET 
    else:
        # if there are errors, reload the page content, 
        # otherwise create a new empty form   
        if prev_data:
            return render_template('create_agent.html', data=prev_data)
        return render_template('create_agent.html')

@application.route('/agent/<id>/archive')
@login_required
def agent_archive(id=None):
    if not id:
        flash("Missing id. Unable to archive this agent.")
        return redirect(request.referrer)
    else:
        agent = Agent.query.filter_by(id=id).first()
        if agent:
            agent.status = Status.archived
            db.session.add(agent)
            db.session.commit()
            flash("Agent archived.")
        else:
            flash("No agent found with this id. Unable to archive this agent.")
    return redirect(request.referrer)

@application.route('/listing/<id>/archive')
@login_required
def listing_archive(id=None):
    if not id:
        flash("Missing id. Unable to archive this listing.")
    else:
        listing = Listing.query.filter_by(id=id).first()
        if listing:
            listing.status = Status.archived
            db.session.add(listing)
            db.session.commit()
            flash("Listing archived.")
        else:
            flash("No listing found with this id. Unable to archive this listing.")
    return redirect(request.referrer)

## Agent - Edit
@application.route('/agent/<id>/edit', methods=["GET", "POST"])
@login_required
def agent_edit(id=None, prev_data=None):
    if request.args.get("prev_data"):
        prev_data = ast.literal_eval(request.args.get("prev_data").rstrip('/'))    
    valid = True
    if request.method == "POST":
        name = request.form["name"]

        if not name:
            valid = False
            flash("Name is required")
        
        agent = Agent.query.filter_by(id=id).first()
        prev_name = agent.name

        name_exists = len(Agent.query.filter_by(name=name).filter(name!=prev_name).all()) > 0
        if name_exists:
            valid = False
            flash(f"Agent already exists with this name.")

        if valid:
            agent.name = name
            db.session.add(agent)
            db.session.commit()
        else:
            if prev_data:
                return render_template('detail_agent.html', id=id, agent=agent, data=prev_data)
            return redirect(url_for("agent_edit", id=id, agent=agent, prev_data=dict(request.form)))
        return redirect(url_for("detail_agent", id=id))
    else: 
        if not id:
            print("Missing ID")
            return
        agent = Agent.query.filter_by(id=id).first()
        if prev_data:
            return render_template('detail_agent.html', id=id, agent=agent, data=prev_data, editing=True)
        return render_template('detail_agent.html', id=id, agent=agent, editing=True)

@application.route('/agent/<id>/delete')
@login_required
def delete_agent(id=None):
    if not id:
        flash("Cannot delete. No id provided.")
        return redirect(request.referrer)
    agent = Agent.query.filter_by(id=id).first()
    if agent:
            agent.status = Status.deleted
            db.session.add(agent)
            db.session.commit()
            flash("Agent deleted successfully.")
    else:
        flash(f"Agent not found with id: {id}. Unable to delete this agent.")
    return redirect(request.referrer)

@application.route('/agent/<id>/recover')
@login_required
def recover_agent(id=None):
    if not id:
        flash("Cannot recover. No id provided.")
        return redirect(request.referrer)
    agent = Agent.query.filter_by(id=id).first()
    if agent:
            agent.status = Status.active
            db.session.add(agent)
            db.session.commit()
            flash("Agent recovered successfully.")
    else:
        flash(f"Agent not found with id: {id}. Unable to recover this agent.")
    return redirect(request.referrer)

@application.route('/listing/<id>/delete')
@login_required
def delete_listing(id=None):
    if not id:
        flash("Cannot delete. No id provided.")
        return redirect(request.referrer)
    listing = Listing.query.filter_by(id=id).first()
    if listing:
            listing.status = Status.deleted
            db.session.add(listing)
            db.session.commit()
            flash("Listing deleted successfully.")
    else:
        flash(f"Listing not found with id: {id}. Unable to delete this listing.")
    return redirect(request.referrer)

@application.route('/listing/<id>/recover')
@login_required
def recover_listing(id=None):
    if not id:
        flash("Cannot recover. No id provided.")
        return redirect(request.referrer)
    listing = Listing.query.filter_by(id=id).first()
    if listing:
            listing.status = Status.active
            db.session.add(listing)
            db.session.commit()
            flash("Listing recovered successfully.")
    else:
        flash(f"Listing not found with id: {id}. Unable to recover this listing.")
    return redirect(request.referrer)

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
    errors = []
    if not listings:
        errors.append("No listings to scrape.")
        return errors
    
    listings_to_scrape = []
    for listing in listings:
        
        fifteen_min_ago = datetime.datetime.now() - timedelta(minutes=15)
        existing_views = ListingViews.query.filter_by(listing_id=listing.id).filter(ListingViews.date > fifteen_min_ago).first()
        if not existing_views:
            listings_to_scrape.append(listing)
        else:
            errors.append(f"{listing.address} scraped less than 15 minutes ago. Please try again later or talk to your system adminstrator.")
    if errors:
        return errors

    scraper = WebScraper()
    for listing in listings_to_scrape: 
        scraper.scrape_listing(listing.id, testing=TESTING)

    return errors
        
## Scrapes listing views for today for a given Listing ID. Updates the db directly once the results are retrieved.
@application.route('/scrape/<id>/')
@login_required
def scraper(id=None):
    listing = Listing.query.filter_by(id=id).first()
    errors = scrape_listings([listing])    
    status = True
    if errors:
        status = False
    
    # Add web scraper run to the DataCollection log
    log_data_collection(CollectionType.one_time, [listing], status=status, errors=errors)
    
    return redirect(url_for('detail_listing', id=id, errors=errors))

## Scrapes listing views for today for all Listings. Updates the db as the results are found. 
@application.route('/scrape/all/')
@login_required
def scrapeAll(id=None):
    listings = Listing.query.all()
    errors = scrape_listings(listings)

    status = True
    if errors:
        status = False
    
    # Log scraping event
    log_data_collection(CollectionType.one_time, listings, status=status, errors=errors)
    
    # Redirect to the home page (Listings - List View)
    if len(errors):
        flash(errors[0])
    return redirect(url_for('list_logs'))

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

    scraped = False
    errors = scrape_listings(listings)
    if not len(errors):
        scraped = True

    if scraped:
        # Log scraping event
        log_data_collection(CollectionType.weekly, listings, status=True, errors=errors)

        # Email admin to notify about scraping run.
        admin_email = os.environ.get("ADMIN_EMAIL")
        if admin_email:
            body = f"Property views were scraped for this week.\nJob Status: {'Passed' if scraped else 'Failed'}\n"
            send_email([admin_email], "JBG Listings - Weekly Listings Report", body)
    else:
        log_data_collection(CollectionType.weekly, listings, status=False, errors=errors)

def log_data_collection(collection_type=None, listings=[], status=True, errors=[]):
    if not collection_type:
        return
    listing_ids = [listing.id for listing in listings]
    data_collection = DataCollection(listing_ids=listing_ids, collection_type=collection_type, status=status, errors=errors)
    db.session.add(data_collection)
    db.session.commit()


# Set up weekly cron job for scraping the listings
# Only when running in the child reloader process.
# Prevent the scheduler from running in the master 
# process. 
#https://stackoverflow.com/questions/9449101/how-to-stop-flask-from-initialising-twice-in-debug-mode
if not (application.debug or os.environ.get("FLASK_ENV") == "development") or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.configure(timezone='est')

    # Every Friday at 5:30 pm 
    scheduler.add_job(scrape_listings_weekly, 'cron', day_of_week="mon-fri", hour=17, minute=30)

    # Every minute - TEST
    #scheduler.add_job(scrape_listings_weekly,'cron',second="*")
        
    # Check which jobs are scheduled
    # scheduler.print_jobs()

    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

#Run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output.
    # REMOVE BEFORE DEPLOYING.
    #application.debug = False

    application.run(use_reloader=False)

    print(f"TESTING = {TESTING}")

    