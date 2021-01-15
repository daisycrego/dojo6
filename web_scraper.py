from models import db, ListingViews, Listing
import lxml.etree
import lxml.html
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
import requests
import datetime
from datetime import date, timedelta, time

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
            if final_results["zillow"] > existing_views.views_zillow:
                existing_views.views_zillow = final_results["zillow"]
                changed = True 
            if final_results["redfin"] > existing_views.views_redfin:
                existing_views.views_redfin = final_results["redfin"]
                changed = True 
            if final_results["cb"] > existing_views.views_cb:
                existing_views.views_cb = final_results["cb"]
                changed = True 
            if changed:
                existing_views.date = datetime.datetime.now()
            db.session.add(existing_views)
            db.session.commit()

        print(f"Listing {id}, {listing.address}: Done scraping from all 3 urls ({url_zillow}, {url_redfin}, {url_cb}) results committed to the db.")
