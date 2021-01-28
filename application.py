import os
import io
from base64 import b64encode
import datetime
from datetime import date, timedelta, time
import enum
import ast
import atexit
import random, string
import requests
from flask import Flask, render_template, Response, request, redirect, url_for, flash, current_app
from flask_login import UserMixin, LoginManager, login_user, \
login_required, current_user, logout_user
from sqlalchemy import asc, func, desc, and_
from flask_sqlalchemy import SQLAlchemy
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from smtplib import SMTPDataError
from dotenv import load_dotenv # for working locally, to access the .env file
import lxml.etree
import lxml.html
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary


load_dotenv() # load the env vars from local .env

application = Flask(__name__)
application.url_map.strict_slashes = False

# When TESTING=True, the WebScraper will generate RANDOM values between 0-10 \
# instead of actually scraping the URLs.
#TESTING = True
#TESTING = False
TESTING = False if os.environ.get("TESTING") and os.environ.get("TESTING") == "False" else True

# Determines whether scraper is active or not
LOCAL = True if os.environ.get("LOCAL") and os.environ.get("LOCAL") == "True" else False


# Set up database based on environment's postgres URL
application.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

# Set secret key for use with Flask-Login for password hashing
application.secret_key = os.environ.get("SECRET_KEY")

# Set up flask mail server and backup config
application.config['MAIL_SERVER']= os.environ.get("PRIMARY_EMAIL_SERVER")
application.config['MAIL_PORT'] = os.environ.get("PRIMARY_EMAIL_PORT")
application.config["MAIL_DEFAULT_SENDER"] = os.environ.get("PRIMARY_EMAIL_LOGIN")
application.config["MAIL_USERNAME"] = os.environ.get("PRIMARY_EMAIL_LOGIN")
application.config["MAIL_PASSWORD"] = os.environ.get("PRIMARY_EMAIL_PASSWORD")
application.config['MAIL_USE_TLS'] = False
application.config['MAIL_USE_SSL'] = True
mail = Mail(application)

db = SQLAlchemy(application)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(application)

application.debug = False

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36",
        "referer": "https://www.redfin.com/"
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

    def scrape_listing(self, id=None, testing=False):
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

        if testing:
            final_results["zillow"] = random.randint(0,10)
            final_results["redfin"] = random.randint(0,10)
            final_results["cb"] = random.randint(0,10)
        else:
            # redfin 
            if listing.url_redfin and "redfin.com" in listing.url_redfin:
                print(f"url_redfin: {url_redfin}")
                url_redfin = listing.url_redfin
                r = requests.get(url=url_redfin, headers=self.redfin_headers)
                root = lxml.html.fromstring(r.content)
                #print(r.content)

                with open(f'redfin_output_{listing.id}.html', 'w') as f:
                     f.write(str(r.content))
                try:
                    #print("raw val before conversion to int:", end=" ")
                    #print(root.xpath('/html/body/div[1]/div[8]/div[2]/div[17]/section/div/div/div[2]/div/div/table/tbody/tr/td[1]/div/div[2]/div/span[1]'))
                    #print(root.xpath('//span[@data-rf-test-name="activity-count-label"]')[0].text.replace(',',''))
                    redfin_views = int(root.xpath('//*[@id="activity-collapsible"]/div[2]/div/div/table/tbody/tr/td[1]/div/div[2]/div/span[1]')[0].text.replace(',',''))
                    #redfin_views = int(root.xpath('//span[@data-rf-test-name="activity-count-label"]')[0].text.replace(',',''))
                    #print(f"redfin_views after conversion to: {redfin_views}")
                except (IndexError,ValueError) as e:
                    print("Initial xpath select for redfin failed, trying backup css selector")
                    print(root.cssselect('#activity-collapsible > div.sectionContentContainer.expanded > div > div > table > tbody > tr > td:nth-child(1) > div > div.labels > div > span.count'))
                    try: 
                        redfin_views = int(root.cssselect('#activity-collapsible > div.sectionContentContainer.expanded > div > div > table > tbody > tr > td:nth-child(1) > div > div.labels > div > span.count')[0].text.replace(',',''))
                        #activity-collapsible > div.sectionContentContainer.expanded > div > div > table > tbody > tr > td:nth-child(1) > div > div.labels > div > span.count
                    except (IndexError,ValueError) as e:
                        redfin_views = None
                
                final_results["redfin"] = redfin_views
            # cb 
            if listing.url_cb and "coldwellbankerhomes.com" in listing.url_cb:
                url_cb = listing.url_cb 
                cb_request = requests.get(url=url_cb, headers=self.cb_headers)
                root = lxml.html.fromstring(cb_request.content)
                with open(f'cb_output_{listing.id}.html', 'w') as f:
                     f.write(str(cb_request.content))
                try:
                    options = Options()
                    options.headless = True
                    executable_path = os.environ.get("GECKODRIVER_PATH")
                    if os.environ.get("FIREFOX_BINARY_PATH"):
                        options.binary = os.environ.get("FIREFOX_BINARY_PATH")
                    #options.binary = "/app/vendor/firefox/firefox"
                    options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')
                    driver = webdriver.Firefox(options=options, executable_path=executable_path)

                    driver.set_page_load_timeout(30)
                    #driver.implicitly_wait(30)
                     
                    attempts = 0
                    while attempts < 100: 
                        try: 
                            driver.get(url_cb)
                            
                            #elem = driver.find_element_by_css_selector('body > section.content.single-photo-carousel > div:nth-child(2) > div.layout-main.property-details > div:nth-child(5) > div.toggle-body > div.details-block.details-block-full-property-details > div.col-1 > ul > li[-1]')
                            elem_parent = driver.find_element_by_xpath("//*[contains(text(),'Viewed:')]/parent::*")
                            views = elem_parent.get_attribute('innerText').split(" ")[1]
                            cb_views = int(views.replace(',',''))
                            final_results["cb"] = cb_views
                            break
                        except NoSuchElementException:
                            attempts += 1
                    
                    if not final_results["cb"]:
                        print(f"url_cb: {url_cb}")
                        print(driver.page_source)

                    driver.quit()
                except (WebDriverException, FileNotFoundError) as e:
                    flash(f"Error while scraping CB values: {e}\n Aborting the scraping run.")
                    final_results["cb"] = None
                    
                    return redirect(request.referrer)
            
            if listing.url_zillow and "zillow.com" in listing.url_zillow:
                url_zillow = listing.url_zillow
                r = requests.get(url=url_zillow, headers=self.zillow_headers)
                root = lxml.html.fromstring(r.content)
                with open(f'zillow_output_{listing.id}.html', 'w') as f:
                     f.write(str(cb_request.content))
                results = root.xpath('//button[text()="Views"]/parent::div/parent::div/div')
                try: 
                    zillow_views = int(results[1].text.replace(',',''))
                except (IndexError,ValueError) as e:
                    zillow_views = None
                if not zillow_views: 
                    print(f"url_zillow: {url_zillow}")
                    print(r.content)
                final_results["zillow"] = zillow_views
                    
        print(f"final_results: {final_results}")
                    
        midnight = datetime.datetime.combine(datetime.datetime.today(), time.min)
        existing_views = ListingViews.query.filter_by(listing_id=id).filter(ListingViews.date >= midnight).first()
        if not existing_views:
            print("No ListingViews already found for this listing... creating a new ListingViews object")
            views = ListingViews(listing_id=id, listing=listing, views_zillow=final_results["zillow"], views_redfin=final_results["redfin"], views_cb=final_results["cb"] )
            db.session.add(views)
            db.session.commit()
        else:
            print("ListingViews already scraped today for this listing... updating the ListingViews object if the new value is larger")
            changed = False
            if not existing_views.views_zillow or (not existing_views.views_zillow is None and not final_results["zillow"] is None and final_results["zillow"] > existing_views.views_zillow):
                existing_views.views_zillow = final_results["zillow"]
                changed = True 
            if not existing_views.views_redfin or (not existing_views.views_redfin is None and not final_results["redfin"] is None and final_results["redfin"] > existing_views.views_redfin):
                existing_views.views_redfin = final_results["redfin"]
                changed = True 
            if not existing_views.views_cb or (not existing_views.views_cb is None and not final_results["cb"] is None and final_results["cb"] > existing_views.views_cb):
                existing_views.views_cb = final_results["cb"]
                changed = True 
            if changed:
                existing_views.date = datetime.datetime.now()
            db.session.add(existing_views)
            db.session.commit()

        print(f"Listing {id}, {listing.address}: Done scraping from all 3 urls ({url_zillow}, {url_redfin}, {url_cb}) results committed to the db.")


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

class SortOptions(enum.Enum):
    asc = 1
    desc = 2
    default = 2

class SortCategory(enum.Enum):
    address = 1
    price = 2
    views_zillow = 3
    views_redfin = 4
    views_cb = 5
    default = 2

# Each user has a FilterState, which is their latest settings for the Listings - List View table filters (sort asc/desc, sort by category)
class FilterState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', backref=db.backref('filterstate', lazy=True))
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    statuses = db.Column(db.ARRAY(db.Integer), nullable=True)
    agents = db.Column(db.ARRAY(db.Integer), nullable=True)
    
    sort_category = db.Column(db.Enum(SortCategory), default=SortCategory.price, nullable=True)
    sort_order = db.Column(db.Enum(SortOptions), default=SortOptions.desc, nullable=True)
    query_string = db.Column(db.String(1000), default=None, nullable=True)


# ROUTES

## LISTINGS ROUTES 
## Listings - List View
@application.route('/', methods=["GET", "POST"])
@login_required
def index():    
    if request.method == "POST":
        # Retrieve search terms
        query = request.form.get("search")
        
        # Find FilterState for this user - (state of all the filters on the Home Page (Listings View))
        filter_state = FilterState.query.filter_by(user=current_user).first()
        
        # Create FilterState for this user if one doesn't exist
        if not filter_state: 
            # Initial filter state is: all agents, active listings only)
            agents = [agent.id for agent in Agent.query.all()]
            statuses = [Status.active.value]
            filter_state = FilterState(user_id=current_user.id, user=current_user, agents=agents, statuses=statuses)
        
        # If this POST was from a search, there will be a query
        if query:
            filter_state.query_string = query if query else filter_state.query_string
        
        # Save the current FilterState and redirect to the GET route
        db.session.add(filter_state)
        db.session.commit()
        return redirect(url_for('index'))
    else:
        # Find FilterState for this user
        filter_state = FilterState.query.filter_by(user=current_user).first()

        # Create FilterState for this user if one doesn't exist
        if not filter_state: 
            # Initial filter state is: all agents, active listings only)
            agents = [agent.id for agent in Agent.query.all()]
            statuses = [Status.active.value]
            filter_state = FilterState(user_id=current_user.id, user=current_user, agents=agents, statuses=statuses)

        # Perform query if FilterState has a query_string
        query = filter_state.query_string
        if query:
            listings = Listing.query.filter(func.lower(Listing.address).contains(query.lower())).union(Listing.query.filter(Listing.mls == query))
            if not len(listings.all()):
                flash(f"No listings found with an address or MLS # containing '{query}'", 'warning')
        else: 
            listings = Listing.query; 

        if filter_state.sort_category:
            if filter_state.sort_category == SortCategory.address: 
                listings = listings.order_by(asc(Listing.address) if filter_state.sort_order == SortOptions.asc else desc(Listing.address))
            elif filter_state.sort_category == SortCategory.price: 
                listings = listings.order_by(asc(Listing.price) if filter_state.sort_order == SortOptions.asc else desc(Listing.price))
            elif filter_state.sort_category == SortCategory.views_zillow:
                if query: 
                    listings = db.session.query(Listing).join(ListingViews
                    ).filter(Listing.id.in_([listing.id for listing in listings.all()])
                    ).order_by(desc(ListingViews.views_zillow) if filter_state.sort_order == SortOptions.desc else (asc(ListingViews.views_zillow) if filter_state.sort_order == SortOptions.asc else desc(Listing.price))
                    )
                else: 
                    listings = db.session.query(Listing).join(ListingViews
                    ).order_by(desc(ListingViews.views_zillow) if filter_state.sort_order == SortOptions.desc else (asc(ListingViews.views_zillow) if filter_state.sort_order == SortOptions.asc else desc(Listing.price))
                    )
            elif filter_state.sort_category == SortCategory.views_redfin: 
                if query: 
                    listings = db.session.query(Listing).join(ListingViews
                    ).filter(Listing.id.in_([listing.id for listing in listings.all()])
                    ).order_by(desc(ListingViews.views_redfin) if filter_state.sort_order == SortOptions.desc else (asc(ListingViews.views_redfin) if filter_state.sort_order == SortOptions.asc else desc(Listing.price))
                    )
                else: 
                    listings = db.session.query(Listing).join(ListingViews
                    ).order_by(desc(ListingViews.views_redfin) if filter_state.sort_order == SortOptions.desc else (asc(ListingViews.views_redfin) if filter_state.sort_order == SortOptions.asc else desc(Listing.price))
                    )
            elif filter_state.sort_category == SortCategory.views_cb: 
                if query: 
                    listings = db.session.query(Listing).join(ListingViews
                    ).filter(Listing.id.in_([listing.id for listing in listings.all()])
                    ).order_by(desc(ListingViews.views_cb) if filter_state.sort_order == SortOptions.desc else (asc(ListingViews.views_cb) if filter_state.sort_order == SortOptions.asc else desc(Listing.price))
                    )
                else: 
                    listings = db.session.query(Listing).join(ListingViews
                    ).order_by(desc(ListingViews.views_cb) if filter_state.sort_order == SortOptions.desc else (asc(ListingViews.views_cb) if filter_state.sort_order == SortOptions.asc else desc(Listing.price))
                    )
        else: 
            if query: 
                listings = listings.order_by(desc(Listing.price)
                ).filter(Listing.id.in_([listing.id for listing in listings.all()])
                )
            else: 
                listings = listings.order_by(desc(Listing.price)
                )

        # Further filter the listings by status and agent
        statuses = dict()
        for category in Status:
            if category.value in filter_state.statuses:
                statuses.update({category.value: category.name})

        agents_dict = dict()
        agents = [agent for agent in Agent.query.all()]
        for agent in agents:
            if agent.id in filter_state.agents:
                agents_dict.update({agent.id: agent.id})

        if filter_state.statuses and len(filter_state.statuses):
            listings = listings.filter(Listing.status.in_(statuses.values()))
        if filter_state.agents and len(filter_state.agents):
            listings = listings.filter(Listing.agent_id.in_(agents_dict.values()))

        # Collect (runs the query, generates a list of Listing objects) 
        listings = listings.all()
        
        # Get the most recent ListingViews object for each distinct listing_id
        # https://stackoverflow.com/questions/45775724/sqlalchemy-group-by-and-return-max-date        
        views_subq = db.session.query(
            ListingViews.listing_id,
            func.max(ListingViews.date).label('maxdate')
        ).group_by(ListingViews.listing_id).subquery('t2')

        views_query = db.session.query(ListingViews).join(
            views_subq,
            and_(
                ListingViews.listing_id == views_subq.c.listing_id,
                ListingViews.date == views_subq.c.maxdate
            )
        )

        # Do a final filter to get only the listings we want
        listing_ids = [listing.id for listing in listings]
        latest_listing_views = views_query.filter(ListingViews.listing_id.in_(listing_ids)).all()

        dict_views = dict()
        if len(latest_listing_views): 
            for views in latest_listing_views:
                if views:
                    dict_views[views.listing_id] = views
        if not len(dict_views):
            dict_views = None
        
        statuses = dict()
        for category in Status:
            statuses.update({category.value: category.name})
        agents = Agent.query.all()

        return render_template('list.html', scraper_active=LOCAL, listings=listings, agents=agents, filter_state=filter_state, latest_listing_views=dict_views, statuses=statuses)

@application.route('/toggle_filter_state/<filter_type>/', methods=["POST"])
@login_required
def toggle_filter_state(filter_type):
    state = request.form.get(filter_type)
    filter_state = FilterState.query.filter_by(user=current_user).first()
    if not filter_state:
        filter_state = FilterState(user=current_user, user_id=current_user.id, agents=[agent.id for agent in Agent.query.all()], statuses=[Status.active.value])
    if filter_type == "address":
        if state == "asc":
            filter_state.sort_category = SortCategory.address
            filter_state.sort_order = SortOptions.asc
        elif state == "desc":
            filter_state.sort_category = SortCategory.address
            filter_state.sort_order = SortOptions.desc
    elif filter_type == "agent":
        agents = [int(item) for item in request.form.getlist('check') ]
        filter_state.agents = agents
    elif filter_type == "price":
        if state == "asc":
            filter_state.sort_category = SortCategory.price
            filter_state.sort_order = SortOptions.asc
        else:
            filter_state.sort_category = SortCategory.price
            filter_state.sort_order = SortOptions.desc     
    elif filter_type == "status":
        statuses = [int(item) for item in request.form.getlist('check') ]
        filter_state.statuses = statuses
    elif filter_type == "views_zillow":
        if state == "asc":
            filter_state.sort_category = SortCategory.views_zillow
            filter_state.sort_order = SortOptions.asc
        elif state == "desc":
            filter_state.sort_category = SortCategory.views_zillow
            filter_state.sort_order = SortOptions.desc
    elif filter_type == "views_redfin":
        if state == "asc":
            filter_state.sort_category = SortCategory.views_redfin
            filter_state.sort_order = SortOptions.asc
        elif state == "desc":
            filter_state.sort_category = SortCategory.views_redfin
            filter_state.sort_order = SortOptions.desc
    elif filter_type == "views_cb":
        if state == "asc":
            filter_state.sort_category = SortCategory.views_cb
            filter_state.sort_order = SortOptions.asc
        elif state == "desc":
            filter_state.sort_category = SortCategory.views_cb
            filter_state.sort_order = SortOptions.desc
    elif filter_type == "reset":
        filter_state.sort_category = SortCategory.price
        filter_state.sort_order = SortOptions.desc
        filter_state.agents = [agent.id for agent in Agent.query.all()]
        filter_state.statuses = [Status.active.value]
        filter_state.query_string = None
    elif filter_type == "reset_query":
        filter_state.query_string = None
    db.session.add(filter_state)
    db.session.commit()
    return redirect(request.referrer)

## Listing - Detail View
@application.route('/listing/')
@application.route('/listing/<id>')
@login_required
def detail_listing(id=None, errors=None):
    errors = request.args.getlist("errors")
    statuses = dict()
    for category in Status:
        statuses.update({category.value: category.name})
    listing = Listing.query.filter_by(id=id).first()
    try:
        price = "${:,.2f}".format(listing.price)
    except (ValueError, TypeError, IndexError):
        flash("Price not formatted correctly", 'error')
        price = str(listing.price)
    if errors:
        flash(f"{errors[0]} For more details, please see the Logs.", 'error')
    listing_views = ListingViews.query.filter_by(listing_id=id).order_by(desc(ListingViews.date)).all()
    return render_template('detail_listing.html', id=id, scraper_active=LOCAL, listing=listing, price=price, plot=True, statuses=statuses, listing_views=listing_views)

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
            flash("Address is required", 'error')
        try:
            if price:
                parsed_price = int(price.replace("$","").replace(",",""))
                if parsed_price < 0:
                    valid = False
                    flash("Listing price cannot be negative", 'error')
        except ValueError: 
            valid = False
            flash(f"Price of {price} is invalid.", 'error')
        
        address_exists = len(Listing.query.filter_by(address=address).all()) > 0
        if address_exists:
            valid = False
            flash(f"Listing already exists with this address.", 'warning')

        if url_zillow and "zillow.com" not in url_zillow:
            valid = False
            flash(f"Zillow URL should contain 'zillow.com'", 'error')
        if url_redfin and "redfin.com" not in url_redfin:
            valid = False
            flash(f"Redfin URL should contain 'redfin.com'", 'error')
        if url_cb and "coldwellbankerhomes.com" not in url_cb:
            valid = False
            flash(f"Coldwell Banker URL should contain 'coldwellbankerhomes.com'", 'error')

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
        if not status:
            valid = False
            flash("Status is required", 'error')
            return redirect(url_for('detail_listing', id=id))
        
        status = Status(int(status)) # this should now be an enum

        if not address:
            valid = False
            flash("Address is required", 'error')

        try:
            if price:
                parsed_price = int(price.replace("$","").replace(",",""))
                if parsed_price < 0:
                    valid = False
                    flash("Listing price cannot be negative", 'error')
        except ValueError: 
            valid = False
            flash(f"Price of {price} is invalid.", 'error')
        
        listing = Listing.query.filter_by(id=id).first()
        prev_address = listing.address
        
        address_exists = len(Listing.query.filter_by(address=address).filter(address!=prev_address).all()) > 0
        if address_exists:
            valid = False
            flash(f"Listing already exists with this address.", 'warning')

        if url_zillow and "zillow.com" not in url_zillow:
            valid = False
            flash(f"Zillow URL should contain 'zillow.com'", 'error')
        if url_redfin and "redfin.com" not in url_redfin:
            valid = False
            flash(f"Redfin URL should contain 'redfin.com'", 'error')
        if url_cb and "coldwellbankerhomes.com" not in url_cb:
            valid = False
            flash(f"Coldwell Banker URL should contain 'redfin.com'", 'error')

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

@application.route("/toggle_inactive/<type>/", methods=["POST"])
@login_required
def toggle_inactive(type=None):
    if not type:
        type = request.args.get("type")
        print(f"toggle_inactive(): type: {type}")
    show_inactive = request.form.get("show_inactive")
    print(f"toggle_inactive(): Toggling inactive to {show_inactive}")
    if type == "agent": 
        return redirect(url_for('agents', show_inactive=show_inactive))
    else: 
        print(f"Type {type} not valid.")
        return redirect(url_for('index'))

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
    listings = Listing.query.filter_by(agent_id=agent.id).filter_by(status=Status.active).all()
    return render_template('detail_agent.html', agent=agent, listings=listings)

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
            flash("Name is required", 'error')
        
        agent_exists = len(Agent.query.filter_by(name=name).all()) > 0
        if agent_exists:
            valid = False
            flash(f"Agent already exists with this name.", 'error')

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
        flash("Missing id. Unable to archive this agent.", 'error')
        return redirect(request.referrer)
    else:
        agent = Agent.query.filter_by(id=id).first()
        if agent:
            agent.status = Status.archived
            db.session.add(agent)
            db.session.commit()
            flash("Agent archived.", 'success')
        else:
            flash("No agent found with this id. Unable to archive this agent.", 'error')
    return redirect(request.referrer)

@application.route('/listing/<id>/archive')
@login_required
def listing_archive(id=None):
    if not id:
        flash("Missing id. Unable to archive this listing.", 'error')
    else:
        listing = Listing.query.filter_by(id=id).first()
        if listing:
            listing.status = Status.archived
            db.session.add(listing)
            db.session.commit()
            flash("Listing archived.", 'success')
        else:
            flash("No listing found with this id. Unable to archive this listing.", 'error')
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
            flash("Name is required", 'error')
        
        agent = Agent.query.filter_by(id=id).first()
        prev_name = agent.name

        name_exists = len(Agent.query.filter_by(name=name).filter(name!=prev_name).all()) > 0
        if name_exists:
            valid = False
            flash(f"Agent already exists with this name.", 'error')

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
        flash("Cannot delete. No id provided.", 'error')
        return redirect(request.referrer)
    agent = Agent.query.filter_by(id=id).first()
    if agent:
        agent.status = Status.deleted
        db.session.add(agent)
        db.session.commit()
        flash("Agent deleted successfully.", 'success')
    else:
        flash(f"Agent not found with id: {id}. Unable to delete this agent.", 'error')
    return redirect(request.referrer)

@application.route('/agent/<id>/recover')
@login_required
def recover_agent(id=None):
    if not id:
        flash("Cannot recover agent. No id provided.", 'error')
        return redirect(request.referrer)
    agent = Agent.query.filter_by(id=id).first()
    if agent:
            agent.status = Status.active
            db.session.add(agent)
            db.session.commit()
            flash("Agent recovered successfully.", 'success')
    else:
        flash(f"Agent not found with id: {id}. Unable to recover this agent.", 'error')
    return redirect(request.referrer)

@application.route('/listing/<id>/delete')
@login_required
def delete_listing(id=None):
    if not id:
        flash("Cannot delete. No id provided.", 'error')
        return redirect(request.referrer)
    listing = Listing.query.filter_by(id=id).first()
    if listing:
            listing.status = Status.deleted
            db.session.add(listing)
            db.session.commit()
            flash("Listing deleted successfully.", 'success')
    else:
        flash(f"Listing not found with id: {id}. Unable to delete this listing.", 'error')
    return redirect(request.referrer)

@application.route('/listing/<id>/recover')
@login_required
def recover_listing(id=None):
    if not id:
        flash("Cannot recover. No id provided.", 'error')
        return redirect(request.referrer)
    listing = Listing.query.filter_by(id=id).first()
    if listing:
            listing.status = Status.active
            db.session.add(listing)
            db.session.commit()
            flash("Listing recovered successfully.", 'success')
    else:
        flash(f"Listing not found with id: {id}. Unable to recover this listing.", 'error')
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

    light = '#D6B0B1'
    medium = '#3B5360'
    dark = '#00181f'

    fig = Figure()
    fig.patch.set_facecolor(dark)
    axis = fig.add_subplot(1, 1, 1)
    axis.plot( 'x', 'y_z', data=df, marker='o', markerfacecolor='blue', markersize=12, color='skyblue', linewidth=4, label="zillow")
    axis.plot( 'x', 'y_r', data=df, marker='x', markerfacecolor='red', markersize=12, color='red', linewidth=4, label="redfin")
    axis.plot( 'x', 'y_c', data=df, marker='.', markerfacecolor='olive', markersize=12, color='olive', linewidth=4, label="cb")
    axis.legend(fontsize='large', labelcolor=light, facecolor=dark, edgecolor=light)
    axis.set_facecolor(medium)
    axis.spines['bottom'].set_color('#D6B0B1')
    axis.spines['top'].set_color('#D6B0B1')
    axis.spines['left'].set_color('#D6B0B1')
    axis.spines['right'].set_color('#D6B0B1')
    axis.xaxis.label.set_color('#D6B0B1')
    axis.yaxis.label.set_color('#D6B0B1')
    axis.tick_params(axis='x', colors='#D6B0B1')
    axis.tick_params(axis='y', colors='#D6B0B1')
    axis.labelsize = 'large'
    
    for x,y in zip([] + x + x + x, [] + y_zillow + y_redfin + y_cb):
        # add labels to the points
        if isinstance(x, str) and isinstance(y, int):
            try:
                axis.annotate(
                        y, 
                        (x,y),
                        textcoords="offset points", # how to position the text
                        bbox=dict(boxstyle="round", fc="#D6B0B1", ec="#D6B0B1"),
                        xytext=(0,10), # distance from text to points (x,y)
                        ha='center') # horizontal alignment can be left, right or center.          
            except TypeError:
                continue

    output = io.BytesIO()
    FigureCanvasAgg(fig).print_png(output)
    
    return Response(output.getvalue(), mimetype="image/png")

## Helper - Scrapes all the listings passed in the input array using the WebScraper class
def scrape_listings(listings=None):
    print(f"scrape_listings(): listings: {listings}")
    errors = []
    if not listings:
        errors.append("No listings to scrape.")
        return errors
    
    listings_to_scrape = []
    for listing in listings:
        
        #fifteen_min_ago = datetime.datetime.now() - timedelta(minutes=15)
        #existing_views = ListingViews.query.filter_by(listing_id=listing.id).filter(ListingViews.date > fifteen_min_ago).first()
        #if not existing_views:
        listings_to_scrape.append(listing)
        #else:
        #    errors.append(f"{listing.address} scraped less than 15 minutes ago. Please try again later or talk to your system adminstrator.")
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
    if len(errors):
        flash(errors[0], 'error')
    else:
        flash(f"Scraped listing views for {listing.address}", 'success')
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
        flash(errors[0], 'error')
    else:
        flash("Scraped all listing views.", 'success')
    return redirect(request.referrer)

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
    print("Running scrape_listings_weekly")
    # Retrieve all of the current listings
    listings = Listing.query.all()

    scraped = False
    errors = scrape_listings(listings)
    if not len(errors):
        scraped = True

    if scraped:
        # Log scraping event
        log_data_collection(CollectionType.weekly, listings, status=True, errors=errors)

        # Email admins to notify about scraping run.
        admins = User.query.filter_by(is_admin=True).all()
        if admins:
            body = f"Property views were scraped for this week.\nJob Status: {'Passed' if scraped else 'Failed'}\n"
            emails = [admin.email for admin in admins]
            send_email(emails, "JBG Listings - Weekly Listings Report", body)
    else:
        log_data_collection(CollectionType.weekly, listings, status=False, errors=errors)

def log_data_collection(collection_type=None, listings=[], status=True, errors=[]):
    if not collection_type:
        return
    listing_ids = [listing.id for listing in listings]
    data_collection = DataCollection(listing_ids=listing_ids, collection_type=collection_type, status=status, errors=errors)
    db.session.add(data_collection)
    db.session.commit()

## Invite New User
@application.route("/invite-user/", methods=["POST"])
@login_required
def invite_user():
    if not current_user.is_admin:
        flash("You don't have the privileges to perform this task.", 'error')
        return redirect(url_for("settings"))
    email = request.form.get("email")
    if not email:
        flash("Please provide an email for the invitation.", 'error')
        return redirect(url_for("settings"))

    user_exists = User.query.filter_by(email=email).first()
    if user_exists:
        flash("A user with this email already exists.", 'error')
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
        flash(f"An invitation was emailed to {email}", 'success')
    else:
        flash(f"An invitation was NOT emailed to {email} due to email server issues. Please contact your system administrator.", 'warning')
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
            flash("No changes detected.", 'error')
            valid = False
        elif name == current_user.name and email == current_user.email:
            flash("No changes detected.", 'error')
            valid = False

        # check if email is taken
        user_exists = User.query.filter_by(email=email).filter(email!=current_user.email).first()
        if user_exists: 
            flash("Email already taken.", 'error')
            valid = False

        if valid: 
            if name and name != current_user.name:
                current_user.name = name
            if email and email != current_user.email:
                current_user.email = email
            db.session.add(current_user)
            db.session.commit()
            flash("Profile updated.", 'success')
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
            flash("Invalid email and/or password.", 'error')
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
            flash("Invitation required to create an account. Please contact your system administrator.", 'error')
            return redirect(url_for('login'))

        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        one_hour_ago = datetime.datetime.now() - timedelta(hours=1)
        active_token = Token.query.filter_by(token=token).filter_by(email=email).filter(Token.created_time > one_hour_ago).first()
        if not active_token:
            flash("Invalid access token, please contact your system administrator", 'error')
            return redirect(url_for('register', data=dict(request.form)))

        if not password:
            valid = False
            flash("Password missing", 'error')
            return redirect(url_for("register", data=dict(request.form)))
        elif not password_confirm:
            valid = False
            #errors.append("Retype password")
            flash("Retype password", 'error')
            return redirect(url_for("register", data=dict(request.form)))
        elif password != password_confirm:
            valid = False
            #errors.append("Passwords must match")
            flash("Passwords must match", 'error')
            return redirect(url_for("register", data=dict(request.form)))
        elif len(password) < 8:
            flash("Password must be at least 8 characters long.", 'error')
            return redirect(url_for("register", data=dict(request.form)))

        user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

        if user: # if a user is found, we want to redirect back to signup page so user can try again
            flash('Email address already in use', 'warning')
            return redirect(url_for('register', data=dict(request.form)))

        # delete the tokens associated with this email, ensure one time use
        existing_tokens = Token.query.filter_by(email=email).all()
        for token in existing_tokens:
            db.session.delete(token)
            db.session.commit()

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
            flash("Please check your email for a registration link. Contact your system administrator if you don't receive an email. Make sure to check your spam folder.", 'warning')
        one_hour_ago = datetime.datetime.now() - timedelta(hours=1)
        active_token = Token.query.filter_by(token=token).filter(Token.created_time > one_hour_ago).first()
        if not active_token:
            flash("Your registration link is expired. Please contact your system administrator for a new invitation.", 'error')
            return redirect(url_for("login"))
        
        if request.args.get("data"):
            data = ast.literal_eval(request.args.get("data").rstrip('/'))
        
        return render_template('register.html', data=data, token=token)

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
            print("Daily limits exceeded for primary Gmail SMTP server, switching to backup server.")
            current_app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("BACKUP_EMAIL_LOGIN")
            current_app.config["MAIL_USERNAME"] = os.environ.get("BACKUP_EMAIL_LOGIN")
            current_app.config["MAIL_PASSWORD"] = os.environ.get("BACKUP_EMAIL_PASSWORD")
            current_app.config["MAIL_PORT"] = os.environ.get("BACKUP_EMAIL_PORT")
            current_app.config["MAIL_SERVER"] = os.environ.get("BACKUP_EMAIL_SERVER")
        
            # Reload mail service
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
                flash("Invalid access token and/or email, please check your email for instructions on resetting your password. Make sure to check your spam folder!", 'error')
                return(redirect(url_for("login")))
            
            password = request.form.get("password")
            confirm_password = request.form.get("password-confirm")
            
            if not password:
                flash("Password missing", 'error')
                return render_template("reset_password.html", resetting=True, token=token, email=email)
            elif not confirm_password:
                flash("Retype password", 'error')
                return render_template("reset_password.html", resetting=True, token=token, email=email)
            elif password != confirm_password:
                flash("Passwords must match", 'error')
                return render_template("reset_password.html", resetting=True, token=token, email=email)
            elif len(password) < 8:
                flash("Password must be at least 8 characters long.", 'error')
                return render_template("reset_password.html", resetting=True, token=token, email=email)

            # delete all the tokens for this email, ensure one time use
            existing_tokens = Token.query.filter_by(email=email).all()
            for token in existing_tokens:
                db.session.delete(token)
                db.session.commit()

            user.password = generate_password_hash(password, method='sha256')

            # save the changes in the db 
            db.session.add(user)
            db.session.commit()
            flash("Password successfully reset.", 'success')
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
                flash(f"An email has been sent to {email} with instructions to reset your password. Make sure to check your spam folder!", 'success')
            else:
                flash("Unable to send to email with reset instructions. Please contact your system administrator.", 'warning')
            return redirect(url_for("reset_password"))
            
                    
        else:
            flash("Please provide an email to get instructions for resetting your password.", 'warning')
            return redirect(url_for("reset_password"))
    # GET
    else:
        token = request.args.get("token")
        email = request.args.get("email")
        if not token and not email:
            return render_template("reset_password.html", resetting=False)
        else:
            if not email:
                flash("Invalid reset link, please check your email or request another password reset link.", "error")
            
            # Check token and email before showing password reset form
            user = User.query.filter_by(email=email).first()
            
            if not user or not token:
                flash("Invalid reset link, please check your email for instructions on resetting your password.", 'error')
            else:
                one_hour_ago = datetime.datetime.now() - timedelta(hours=1)
                active_token = Token.query.filter_by(token=token).filter_by(email=email).filter(Token.created_time > one_hour_ago).first()
                if not active_token:
                    flash("Reset link is expired. Please provide your email and request a new reset password link.", 'warning')
                    return(redirect(url_for("reset_password"))) 
            return render_template("reset_password.html", resetting=True, token=token, email=email)

# Set up weekly cron job for scraping the listings
# Only when running in the child reloader process.
# Prevent the scheduler from running in the master 
# process. 
#https://stackoverflow.com/questions/9449101/how-to-stop-flask-from-initialising-twice-in-debug-mode
# Only schedule the background process if this is a local deployment
# because the scraper should only be run on the local version.
if LOCAL or ((application.debug or os.environ.get("FLASK_ENV") == "development") or os.environ.get("WERKZEUG_RUN_MAIN") == "true"):
    print("Scheduling background jobs here")
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.configure(timezone='est')

    #scheduler.add_job(scrape_listings_weekly, 'cron', day_of_week="mon-fri", hour=17, minute=30)
    
    # Every Friday at 5:30 pm 
    scheduler.add_job(scrape_listings_weekly, 'cron', day_of_week="fri", hour=17, minute=30)
    
    # TESTING 

    scheduler.add_job(scrape_listings_weekly, 'cron', day_of_week="wed", hour=21, minute=10)

    # Every minute - TEST
    #scheduler.add_job(scrape_listings_weekly,'cron',second="*")
    
    # Test Job
    # scheduler.add_job(scrape_listings_weekly, 'cron', day_of_week="mon", hour=11, minute=32)

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
    print(f"LOCAL = {LOCAL}")

    
