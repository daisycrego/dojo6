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

    func fetchAllListings(completion: @escaping ([String: String]) -> ()) -> Void {
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
                }

            } 
            
        }
        task.resume()
        print("Fetching Listing data from backend...")
    }

    func scrapeListing(targetUrl: String) {
        let url = URL(string: "/api/endpoint/tbd") // @TODO: Create flask endpoint and supply its URL
        guard let requestUrl = url else { print("Found nil while unwrapping url..."); return; }
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
    func scrapeAllListings(urls: [String: String]) {
        var results = [(String, String)]()
        let serialQueue = DispatchQueue(label: "serialQueue")
        let group = DispatchGroup()

        for (url, id) in urls {

            group.enter()
            serialQueue.async {
                scrapeListing(targetUrl: url)
                let tuple = (url, id)
                results.append(tuple)
                group.leave()
            }
            DispatchQueue.main.async {
                group.wait()

            }
        }

        group.notify(queue: serialQueue) {
            print("passed all of the following listings to the web scraper.")
            print(results)
            print("the scraper will send an API to the backend with the views directly")
        }
    }

    func beforeRender(req: Request, form: ListingViewsEditForm) -> EventLoopFuture<Void> {
        ListingPostModel.query(on: req.db).all()
            .mapEach(\.formFieldStringOption)
            .map { form.listing.options = $0 }
    }

    func collectViews(req: Request) -> EventLoopFuture<ClientResponse> {
        print("collectViews")
        //var url = "https://www.zillow.com/homedetails/205-10th-St-APT-8V-Jersey-City-NJ-07302/2077478011_zpid/?view=public"
        let urls = [("https://www.coldwellbankerhomes.com/nj/weehawken/369-park-ave/pid_37447822/", "abc")]
        let url = URL(string: "https://www.coldwellbankerhomes.com/nj/weehawken/369-park-ave/pid_37447822/")

        fetchAllListings(completion: scrapeAllListings)
        
        // use the API to get the ListingViews, that way you can get the ListingViewsModel's in Content format, which the API already implements. 
        return req.client.get("http://localhost:8080/api/listing/views/")
    }
}
