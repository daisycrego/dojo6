from flask import Flask, render_template, Response, request, redirect, url_for
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
import requests
import lxml.etree
import lxml.html
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options

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
        if listing.url_zillow and "zillow.com" in listing.url_zillow:
            url = listing.url_zillow
            r = requests.get(url=url, headers=zillow_headers)
            root = lxml.html.fromstring(r.content)
            results = root.xpath('//button[text()="Views"]/parent::div/parent::div/div')
            try: 
                zillow_views = int(results[1].text.replace(',',''))
            except IndexError:
                zillow_views = None
            final_results["zillow"] = zillow_views
        
        # redfin 
        if listing.url_redfin and "redfin.com" in listing.url_redfin:
            url = listing.url_redfin
            r = requests.get(url=url, headers=redfin_headers)
            root = lxml.html.fromstring(r.content)
            try:
                redfin_views = int(root.xpath('//span[@data-rf-test-name="activity-count-label"]')[0].text.replace(',',''))
            except IndexError:
                redfin_views = None
            final_results["redfin"] = redfin_views

        # cb 
        if listing.url_cb and "coldwellbankerhomes.com" in listing.url_cb:
            url = listing.url_cb
            cb_request = requests.get(url=url, headers=cb_headers)
            root = lxml.html.fromstring(cb_request.content)
            options = Options()
            options.headless = True
            driver = webdriver.Firefox(options=options)
            driver.get(url) 

            attempts = 0
            while attempts < 100: 
                try: 
                    #elem = driver.find_element_by_css_selector('body > section.content.single-photo-carousel > div:nth-child(2) > div.layout-main.property-details > div:nth-child(5) > div.toggle-body > div.details-block.details-block-full-property-details > div.col-1 > ul > li[-1]')
                    elem_parent = driver.find_element_by_xpath("//*[contains(text(),'Viewed:')]/parent::*")
                    print(url)
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

        views = ListingViews(listing_id=id, listing=listing, views_zillow=final_results["zillow"], views_redfin=final_results["redfin"], views_cb=final_results["cb"] )

        db.session.add(views)
        db.session.commit()
        print("Done scraping from all 3 urls, results committed to the db.")

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
    views = ListingViews.query.filter_by(listing_id=id).order_by(asc(ListingViews.date)).all()
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

    output = io.BytesIO()
    FigureCanvasAgg(fig).print_png(output)
    return Response(output.getvalue(), mimetype="image/png")

@application.route('/scrape/<id>/')
def scraper(id=None):
    scraper = WebScraper()
    scraper.scrape_listing(id)
    listing = getListing(id)
    return redirect(url_for('detail', id=id))
    #return redirect(f`/listing/${id}`, code=302)

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

