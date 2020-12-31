import Vapor
import Fluent
import Leaf
import Kanna
import Foundation

struct ListingViewsAdminController: AdminViewController {
    typealias EditForm = ListingViewsEditForm
    typealias Model = ListingViewsModel
    
    var listView: String = "Listing/Admin/ListingViews/List"
    var editView: String = "Listing/Admin/ListingViews/Edit"

    // @TODO - Update this function to return [String:String], which is [URL:ID], so each URL can have its own return val
    func GetListingURLs() -> [String] {
        let url = URL(string: "http://localhost:8080/api/listing/posts/")
        guard let requestUrl = url else { fatalError() }
        // Create URL Request
        var request = URLRequest(url: requestUrl)
        // Specify HTTP Method to use
        request.httpMethod = "GET"
        var urls = [String]()
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
            if let data = data, let dataString = String(data: data, encoding: .utf8) {
                
                var output = [String: AnyObject]()
                
                do {
                    output = try JSONSerialization.jsonObject(with: data, options: .allowFragments) as! [String: AnyObject]
                    
                    var allListings = output["items"]! as! [Any]
                    for listing in allListings {
                        var current = listing as! Dictionary<String,Any>
                        var url_zillow = current["url_zillow"]! as! String
                        var url_redfin = current["url_redfin"]! as! String
                        var url_cb = current["url_cb"]! as! String
                        urls.append(url_zillow.replacingOccurrences(of: "\"", with: ""))
                        urls.append(url_redfin.replacingOccurrences(of: "\"", with: ""))
                        urls.append(url_zillow.replacingOccurrences(of: "\"", with: ""))
                        
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

    func GetListingView(targetUrl: String) -> (String, Int) {
        // Create URL
        let url = URL(string: targetUrl)
        guard let requestUrl = url else { fatalError() }
        // Create URL Request
        var request = URLRequest(url: requestUrl)
        // Specify HTTP Method to use
        request.httpMethod = "GET"

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

        let sem = DispatchSemaphore(value: 0)
        var output = (targetUrl, -1)

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

            
            
            // Convert HTTP Response Data to a simple String
            if let data = data, let dataString = String(data: data, encoding: .utf8) {
                //print("Response data string:\n \(dataString)")
                 
                if let doc = try? HTML(html: data, encoding: .utf8) {
                    //print(doc.title)
                    
                    /*
                    // Search for nodes by CSS
                    for link in doc.css("a, link") {
                        print(link.text)
                        print(link["href"])
                    }
                    */
                    
                    // Search for nodes by XPath
                    for link in doc.xpath("//button[text()='Views']/parent::div/parent::div/div") {
                        //print(link.text)
                        var value = link.text!.replacingOccurrences(of: ",", with: "")
                        print("value: \(value)")
                        if CharacterSet.decimalDigits.isSuperset(of: CharacterSet(charactersIn: value)) {
                            print(targetUrl)
                            print(value)

                            output.1 = Int(value)!
                            // create a new listingviews object for today's date for this url type
                        } else {
                            print(targetUrl)
                            print("not a number!")
                        }
                    }
                    sem.signal()
                    
                } else {
                    sem.signal()
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
        
        //GetListings()
        //print(req.client.get("http://localhost:8080/api/listing/views/"))
        //print(req.client.get("http://localhost:8080/api/listing/posts/"))
        
        //var url = "https://www.zillow.com/homedetails/205-10th-St-APT-8V-Jersey-City-NJ-07302/2077478011_zpid/?view=public"
        var urls = GetListingURLs()
        var results = [(String, Int)]()
        print(urls)

        let serialQueue = DispatchQueue(label: "serialQueue")
        let group = DispatchGroup()
        print("number of urls: \(urls.count)")

        for url in urls {
            group.enter()
            serialQueue.async {
                results.append(GetListingView(targetUrl: url))
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
        
        // use the API to get the ListingViews, that way you can get the ListingViewsModel's in Content format, which the API already implements. 
        return req.client.get("http://localhost:8080/api/listing/views/")
    }
}