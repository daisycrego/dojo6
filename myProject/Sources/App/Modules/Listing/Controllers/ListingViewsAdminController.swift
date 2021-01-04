import Vapor
import Fluent
import Leaf
import Foundation
import FoundationNetworking

struct ListingViewsAdminController: AdminViewController {
    typealias EditForm = ListingViewsEditForm
    typealias Model = ListingViewsModel
    
    var listView: String = "Listing/Admin/ListingViews/List"
    var editView: String = "Listing/Admin/ListingViews/Edit"

    func fetchAllListings(completion: ([String: String]) -> ()) -> Void {
        // Endpoint for retrieving all of the current Listing objects in the database
        let url = URL(string: "http://localhost:8080/api/listing/posts/")
        guard let requestUrl = url else { fatalError() }
        // Create URL Request
        var request = URLRequest(url: requestUrl)
        // Specify HTTP Method to use
        request.httpMethod = "GET"
        var urls = [String: String]()
        let task = URLSession.shared.dataTask(with: request) { (data, response, error) in
            
            // Check if Error took place
            if let error = error {
                print("Error took place \(error)")
            }
            
            // Read HTTP Response Status code
            if let response = response as? HTTPURLResponse {
                print("Response HTTP Status code: \(response.statusCode)")
            }

            // Convert HTTP Response Data to a simple String
            if let data = data /*, let dataString = String(data: data, encoding: .utf8)*/ {
                
                var output = [String: AnyObject]()
                
                do {
                    output = try JSONSerialization.jsonObject(with: data, options: .allowFragments) as! [String: AnyObject]
                    
                    let allListings = output["items"]! as! [Any]
                    for listing in allListings {
                        let current = listing as! Dictionary<String,Any>
                        let url_zillow = current["url_zillow"]! as! String
                        let url_redfin = current["url_redfin"]! as! String
                        let url_cb = current["url_cb"]! as! String
                        let id = current["id"]! as! String
                        urls[url_zillow] = id
                        urls[url_redfin] = id
                        urls[url_cb] = id 
                    }

                    print("Retrieved Listing data from backend")
                    completion(urls)

                } catch let error as NSError {
                    print(error)
                    sem.signal()
                }

            } 
            
        }
        task.resume()
        print("Fetching Listing data from backend...")
    }

    func scrapeListing(targetUrl: String) {
        let url = URL(string: "/api/endpoint/tbd") // @TODO: Create flask endpoint and supply its URL
        guard let requestUrl = url else { print("Found nil while unwrapping url..."); return -1 }
        var request = URLRequest(url: url!)
        request.httpMethod = "POST"

        // prepare json data
        let json: [String: Any] = ["url": targetUrl]
        let jsonData = try? JSONSerialization.data(withJSONObject: json)

        // insert json data to the request
        request.httpBody = jsonData

        let task = URLSession.shared.dataTask(with: request) { data, response, error in 
        
            guard let data = data, error == nil else {
                print(error?.localizedDescription ?? "No data")
                return
            }
            let responseJSON = try? JSONSerialization.jsonObject(with: data, options: [])
            if let responseJSON = responseJSON as? [String: Any] {
                print(responseJSON)
                print("Scraping job started on Dojo Flask server")
            }
        
        }

        task.resume()
            
    } 

    // will be passed as completion to fetchAllListings 
    func scrapeAllListings(listings: [String: String]) {
        var results = [(String, String, Int)]()
        let serialQueue = DispatchQueue(label: "serialQueue")
        let group = DispatchGroup()

        for (url, id) in urls {

            group.enter()
            serialQueue.async {
                let views = GetListingView(targetUrl: url)
                let tuple = (url, id, views)
                results.append(tuple)
                group.leave()
            }
            DispatchQueue.main.async {
                group.wait()

            }
        }

        group.notify(queue: serialQueue) {
            print(results)
            // post all the results to the API for ListingViews

        }
    }

    func GetListingURLs() -> [String: String] {
        // Endpoint for retrieving all of the current Listing objects in the database 
        let url = URL(string: "http://localhost:8080/api/listing/posts/")
        guard let requestUrl = url else { fatalError() }
        // Create URL Request
        var request = URLRequest(url: requestUrl)
        // Specify HTTP Method to use
        request.httpMethod = "GET"
        var urls = [String: String]()
        let sem = DispatchSemaphore(value: 0)
        let task = URLSession.shared.dataTask(with: request) { (data, response, error) in
            
            // Check if Error took place
            if let error = error {
                print("Error took place \(error)")
            }
            
            // Read HTTP Response Status code
            if let response = response as? HTTPURLResponse {
                print("Response HTTP Status code: \(response.statusCode)")
            }

            // Convert HTTP Response Data to a simple String
            if let data = data /*, let dataString = String(data: data, encoding: .utf8)*/ {
                
                var output = [String: AnyObject]()
                
                do {
                    output = try JSONSerialization.jsonObject(with: data, options: .allowFragments) as! [String: AnyObject]
                    
                    let allListings = output["items"]! as! [Any]
                    for listing in allListings {
                        let current = listing as! Dictionary<String,Any>
                        let url_zillow = current["url_zillow"]! as! String
                        let url_redfin = current["url_redfin"]! as! String
                        let url_cb = current["url_cb"]! as! String
                        let id = current["id"]! as! String
                        urls[url_zillow] = id
                        urls[url_redfin] = id
                        urls[url_cb] = id 
                    }

                    sem.signal()

                } catch let error as NSError {
                    print(error)
                    sem.signal()
                }

            } 
            
        }
        task.resume()
        sem.wait()
        return urls
    }

    func GetListingView(targetUrl: String) -> Int {
        print("Processing ListingViews for \(targetUrl)")
        // Create URL
        let url = URL(string: targetUrl)
        //let url = URL(string: "https://www.coldwellbankerhomes.com/nj/hoboken/609-jefferson-st-4a/pid_38470159/")    
        guard let requestUrl = url else { print("Found nil while unwrapping url..."); return -1 }
        // Create URL Request
        var request = URLRequest(url: url!)
        // Specify HTTP Method to use
        request.httpMethod = "GET"

        var xpath = ""
        var type : String

        if targetUrl.contains("zillow.com") {
            type = "zillow"
            xpath = "//button[text()='Views']/parent::div/parent::div/div"
            request.setValue("text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", forHTTPHeaderField: "accept")
            request.setValue("gzip, deflate, br", forHTTPHeaderField: "accept-encoding")
            request.setValue("en-US,en;q=0.9", forHTTPHeaderField: "accept-language")
            request.setValue("no-cache", forHTTPHeaderField: "cache-control")
            request.setValue("JSESSIONID=E988E25011499DF287B3336BE0E5F5F0; zguid=23|%2422236d48-1875-434d-b8f2-d1421d073afd; zgsession=1|2b52934e-1667-431f-9ec9-82007785df2a; _ga=GA1.2.1982612433.1604442799; _gid=GA1.2.620325738.1604442799; zjs_user_id=null; zjs_anonymous_id=%2222236d48-1875-434d-b8f2-d1421d073afd%22; _pxvid=92a1511a-1e24-11eb-8532-0242ac120018; _gcl_au=1.1.1767744341.1604442801; KruxPixel=true; DoubleClickSession=true; __gads=ID=41906d69e2453aa2-22d228f5397a006b:T=1604442801:S=ALNI_MYdXvUPJMu2Teg1lshpPkb5Ji_RVA; _fbp=fb.1.1604442801842.727886612; _pin_unauth=dWlkPU5EQmpaVGxoWkRrdE5qWTJPUzAwTVRJd0xUaGlNekF0TXpNeFlUZzVaREF3T0RReg; search=6|1607034817342%7Crect%3D40.78606556037442%252C-73.85258674621582%252C40.71688335199443%252C-74.20723915100098%26rid%3D25146%26disp%3Dmap%26mdm%3Dauto%26p%3D1%26z%3D1%26pt%3Dpmf%252Cpf%26fs%3D1%26fr%3D0%26mmm%3D1%26rs%3D0%26ah%3D0%26singlestory%3D0%26housing-connector%3D0%26abo%3D0%26garage%3D0%26pool%3D0%26ac%3D0%26waterfront%3D0%26finished%3D0%26unfinished%3D0%26cityview%3D0%26mountainview%3D0%26parkview%3D0%26waterview%3D0%26hoadata%3D1%26zillow-owned%3D0%263dhome%3D0%09%09%09%09%09%09%09%09; _px3=3429246752721cd227605773f1b990296844cc3b7adf99d73db1641b9fbd7524:HyhtsCiMCjoXm9YCLqUyYvVN6efdCzIdoSd+zu5Fou3woWXM3ouLAMEgw+vvoadA2GEfCRLJMBAtsdG3obEb2Q==:1000:WFzQZqPXu1SGFlXAM2Sa3b1ddSBnf/TdcWupq2Muc7NzUQfxNTQK9Mzpbt86RfiaHArwpcS4V3i9V+VEVoB7v58pm0C9FL2IkALrsTHHlQWQ25JMYDjgm8kPx8qWlas1+OSEOjGKwf+nuBKX7kjdN2KzMdxkpVySMkvEtZLoJ3k=; _uetsid=940faaa01e2411eb878aa964e2fb93d7; _uetvid=940ffda01e2411eb9bb3456f6030a021; AWSALB=lOVOVmEArl7Hkta9wCWOwWj3OzDo8E0zavfRORSHJRtpjlgqblhOKL0o7n0wNhn3CR7zrJpDRDgFMiPRuLsb/zny6hY2Ttw4KoOm5fRdnA2WU729Z1jXP6lLvtc5; AWSALBCORS=lOVOVmEArl7Hkta9wCWOwWj3OzDo8E0zavfRORSHJRtpjlgqblhOKL0o7n0wNhn3CR7zrJpDRDgFMiPRuLsb/zny6hY2Ttw4KoOm5fRdnA2WU729Z1jXP6lLvtc5; KruxAddition=true", forHTTPHeaderField: "cookie")
            request.setValue("no-cache", forHTTPHeaderField: "pragma")
            request.setValue("document", forHTTPHeaderField: "sec-fetch-dest")
            request.setValue("navigate", forHTTPHeaderField: "sec-fetch-mode")
            request.setValue("same-origin", forHTTPHeaderField: "sec-fetch-site")
            request.setValue("?1", forHTTPHeaderField: "sec-fetch-user")
            request.setValue("1", forHTTPHeaderField: "upgrade-insecure-requests")
            request.setValue("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36", forHTTPHeaderField: "user-agent")
        } else if targetUrl.contains("redfin.com") {
            type = "redfin"
            xpath = "//span[@data-rf-test-name=\"activity-count-label\"]"
            request.setValue("text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", forHTTPHeaderField: "accept")
            request.setValue("gzip, deflate, br", forHTTPHeaderField: "accept-encoding")
            request.setValue("en-US,en;q=0.9", forHTTPHeaderField: "accept-language")
            request.setValue("no-cache", forHTTPHeaderField: "cache-control")
            request.setValue("RF_CORVAIR_LAST_VERSION=338.2.1; RF_BROWSER_ID=68NeycsSR0u5ZYJe3HNFeg; RF_VISITED=false; RF_BID_UPDATED=1; RF_MARKET=newjersey; RF_BUSINESS_MARKET=41; AKA_A2=A; _gcl_au=1.1.594105178.1604444441; AMP_TOKEN=%24NOT_FOUND; _ga=GA1.2.241545075.1604444442; _gid=GA1.2.517680459.1604444442; _uetsid=65e404c01e2811eb9ad809962c95ca2f; _uetvid=65e44e601e2811eb93ecc7484b75a7c7; RF_BROWSER_CAPABILITIES=%7B%22screen-size%22%3A4%2C%22ie-browser%22%3Afalse%2C%22events-touch%22%3Afalse%2C%22ios-app-store%22%3Afalse%2C%22google-play-store%22%3Afalse%2C%22ios-web-view%22%3Afalse%2C%22android-web-view%22%3Afalse%7D; RF_LAST_SEARCHED_CITY=Hoboken; userPreferences=parcels%3Dtrue%26schools%3Dfalse%26mapStyle%3Ds%26statistics%3Dtrue%26agcTooltip%3Dfalse%26agentReset%3Dfalse%26ldpRegister%3Dfalse%26afCard%3D2%26schoolType%3D0%26lastSeenLdp%3DnoSharedSearchCookie; RF_LDP_VIEWS_FOR_PROMPT=%7B%22viewsData%22%3A%7B%2211-03-2020%22%3A%7B%22122200495%22%3A1%7D%7D%2C%22expiration%22%3A%222022-11-03T23%3A00%3A43.223Z%22%2C%22totalPromptedLdps%22%3A0%7D; FEED_COUNT=0%3Af; G_ENABLED_IDPS=google; RF_LISTING_VIEWS=122200495", forHTTPHeaderField: "cookie")
            request.setValue("no-cache", forHTTPHeaderField: "pragma")
            request.setValue("document", forHTTPHeaderField: "sec-fetch-dest")
            request.setValue("navigate", forHTTPHeaderField: "sec-fetch-mode")
            request.setValue("same-origin", forHTTPHeaderField: "sec-fetch-site")
            request.setValue("?1", forHTTPHeaderField: "sec-fetch-user")
            request.setValue("1", forHTTPHeaderField: "upgrade-insecure-requests")
            request.setValue("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36", forHTTPHeaderField: "user-agent")
        } else if targetUrl.contains("coldwellbankerhomes.com") {
            type = "cb"
            //xpath = "/html/body/section[2]/div[1]/div[6]/div[5]/div[2]/div[1]/div[1]/ul/li[8]/text()"
            //xpath = "//*[contains(text(),'Viewed:')]/parent::*"
            xpath = "/html/body"
            
            request.setValue("*/*", forHTTPHeaderField: "accept")
            request.setValue("gzip, deflate, br", forHTTPHeaderField: "accept-encoding")
            request.setValue("en-US,en;q=0.9", forHTTPHeaderField: "accept-language")
            request.setValue("no-cache", forHTTPHeaderField: "cache-control")
            request.setValue("0", forHTTPHeaderField: "content-length")
            request.setValue("text/plain", forHTTPHeaderField: "content-type")
            request.setValue("IDE=AHWqTUkqjk9aEsiwwq7Of_DhztqOLy8hRBhPMSenMOcZsNelDowpIl4Mng4ScA1C; DSID=AAO-7r7zzuHNo0Cqvl0Fu2PGvpAEl4mR_KdOuVZpergV7fKeY8emo1Tw4bZ-92VdKbS2-aT3jRqAQtTL_1TTcRMO9XDTZt3Lo7GiPdv5W4ku3JU9-fjNcE0", forHTTPHeaderField: "cookie")
            request.setValue("https://www.coldwellbankerhomes.com", forHTTPHeaderField: "origin")
            request.setValue("no-cache", forHTTPHeaderField: "pragma")
            request.setValue("https://www.coldwellbankerhomes.com", forHTTPHeaderField: "referer")
            request.setValue("empty", forHTTPHeaderField: "sec-fetch-dest")
            request.setValue("cors", forHTTPHeaderField: "sec-fetch-mode")
            request.setValue("cross-site", forHTTPHeaderField: "sec-fetch-site")
            request.setValue("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36", forHTTPHeaderField: "user-agent")
            request.setValue("CKO1yQEIkLbJAQimtskBCMG2yQEIqZ3KAQi3uMoBCKvHygEI9sfKAQjpyMoBCNzVygEI/ZfLAQiRmcsBCMiZywEIl5rLARiLwcoB", forHTTPHeaderField
            : "x-client-data")
        } else {
            print("url doesn't match redfin, zillow, or cb...")
            return -1
        }

        let sem = DispatchSemaphore(value: 0)
        var output = -1
            
        // Send HTTP Request
        let task = URLSession.shared.dataTask(with: request) { (data, response, error) in
            
            // Check if Error took place
            if let error = error {
                print("Error took place \(error)")
            }
            
            // Read HTTP Response Status code
            if let response = response as? HTTPURLResponse {
                print("Response HTTP Status code: \(response.statusCode)")
            }

            var range = 1
            if type == "cb" {
                range = 100
            }

            for i in 1...range {
                // Convert HTTP Response Data to a simple String
                if let data = data, let dataString = String(data: data, encoding: .utf8) {
                    //print("Response data string:\n \(dataString)")

                    if dataString.contains("Viewed:") {
                        print(dataString)
                    }

                    if let doc = try? HTML(html: data, encoding: .utf8) {
                        sleep(5)
                        if type == "redfin" {
                            let link = doc.xpath(xpath)[0]
                            let value = link.text!.replacingOccurrences(of: ",", with: "")
                            if CharacterSet.decimalDigits.isSuperset(of: CharacterSet(charactersIn: value)) {
                                print(targetUrl)
                                print(value)

                                output = Int(value)!
                                // create a new listingviews object for today's date for this url type
                            } else {
                                print(targetUrl)
                                print("not a number!")
                            }
                        } else if type == "zillow" {
                            // Search for nodes by XPath
                            for link in doc.xpath(xpath) {
                                
                                let value = link.text!.replacingOccurrences(of: ",", with: "")
                                if CharacterSet.decimalDigits.isSuperset(of: CharacterSet(charactersIn: value)) {
                                    print(targetUrl)
                                    print(value)

                                    output = Int(value)!
                                    // create a new listingviews object for today's date for this url type
                                } else {
                                    print(targetUrl)
                                    print("not a number!")
                                }
                            }
                        } else if type == "cb" {
                            print("CB")
                            print(targetUrl)
                            
                            
                            let links = doc.xpath(xpath)
                            print(links)
                            for link in links {
                                let value = link.text!.replacingOccurrences(of: ",", with: "")
                                if value.contains("Viewed: ") {
                                    print(value)
                                } else {
                                    print("Viewed: data hasn't loaded...")
                                }
                                
                            }
                        }
                        
                        sem.signal()
                        
                    } else {
                        sem.signal()
                        
                    }
                        
                } 
            }
            
            
            
        }
        task.resume()
        sem.wait()
        return output
        
    }

    func beforeRender(req: Request, form: ListingViewsEditForm) -> EventLoopFuture<Void> {
        ListingPostModel.query(on: req.db).all()
            .mapEach(\.formFieldStringOption)
            .map { form.listing.options = $0 }
    }

    func collectViews(req: Request) -> EventLoopFuture<ClientResponse> {
        print("collectViews")
        // var listings = req.client.get("http://localhost:8080/api/listing/posts/") --> retrieves all of the lists, need this for the next steps
        
        //print(req.client.get("http://localhost:8080/api/listing/views/"))
        //print(req.client.get("http://localhost:8080/api/listing/posts/"))
        //var url = "https://www.zillow.com/homedetails/205-10th-St-APT-8V-Jersey-City-NJ-07302/2077478011_zpid/?view=public"
        
        // @TODO - add this back
        //let urls = GetListingURLs()

        let urls = [("https://www.coldwellbankerhomes.com/nj/weehawken/369-park-ave/pid_37447822/", "abc")]
        let url = URL(string: "https://www.coldwellbankerhomes.com/nj/weehawken/369-park-ave/pid_37447822/")

        Get()

        /*
        var results = [(String, String, Int)]()
        let serialQueue = DispatchQueue(label: "serialQueue")
        let group = DispatchGroup()

        for (url, id) in urls {
            
            group.enter()
            serialQueue.async {
                let views = GetListingView(targetUrl: url)
                let tuple = (url, id, views)
                results.append(tuple)
                group.leave()
            }
            DispatchQueue.main.async {
                group.wait()
                
            }
        }

        group.notify(queue: serialQueue) {
            print(results)
            // post all the results to the API for ListingViews

        }
        */
        
        // use the API to get the ListingViews, that way you can get the ListingViewsModel's in Content format, which the API already implements. 
        return req.client.get("http://localhost:8080/api/listing/views/")
    }
}

class CustomWebView: WKWebView {
    override func load(_ request: URLRequest) -> WKNavigation? {
        guard let mutableRequest: NSMutableURLRequest = request as? NSMutableURLRequest else {
            return super.load(request)
        }
        mutableRequest.setValue("custom value", forHTTPHeaderField: "custom field")
        return super.load(mutableRequest as URLRequest)
    }
}
