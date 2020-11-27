import Vapor
import Fluent
import Foundation

struct ListingMigrationSeed: Migration {

    func getStringFromFile(_ path: String) throws -> String {
        let url = URL(fileURLWithPath: path)
        let string = try String(contentsOf: url)
        return string
    }
    
    func prepare(on db: Database)-> EventLoopFuture<Void> {

        var addresses = [String]()
        var agents_for_listings = [String]()
        var all_agents = Set<String>()
        var url_dict = [
            "zillow": [],
            "redfin": [],
            "cb": []
        ]
        let path = "listings.csv"
        var string : String
        do { 
            string = try self.getStringFromFile(path)
        } catch {
            string = ""
            print("getStringFromFile(\(path)) failed...")
        }
        
        let lines = string.split(separator: "\r\n")
        for (lineNumber, line) in lines.enumerated() {
        
            // skip the first line of headers: 
            // Address,LP,Agent,MLS,Zillow URL,Redfin URL,Coldwell Banker URL
            if lineNumber == 0 {
                continue
            } 

            let pattern = ",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)"
            let s = String(line)
            let regex = try! NSRegularExpression(pattern: pattern, options: NSRegularExpression.Options.caseInsensitive)
            let range = NSMakeRange(0, s.count)
            let modString = regex.stringByReplacingMatches(
                in: s, 
                options: [], 
                range: range, 
                withTemplate: ";"
            )
            let columns = modString.split(separator: ";", omittingEmptySubsequences: false)

            for (columnNumber, column) in columns.enumerated() {
                let string_col = String(column)
                print(string_col)
                if columnNumber == 0 {
                    // handle addresses
                    addresses.append(string_col)
                } else if columnNumber == 1 {
                    // handle prices
                } else if columnNumber == 2 {
                    agents_for_listings.append(string_col)
                    all_agents.insert(string_col)
                    // handle agent
                } else if columnNumber == 3 {
                    // handle MLS
                }
                // handle urls 
                else if columnNumber == 4 {
                    url_dict["zillow"]!.append(string_col)
                } else if columnNumber == 5 {
                    url_dict["redfin"]!.append(string_col)
                } else if columnNumber == 6 {
                    url_dict["cb"]!.append(string_col)
                }
            }
        }

        var agent_objs = [ListingAgentModel]()
        for agent in all_agents {
            agent_objs.append(ListingAgentModel(name: agent))
        }

        return agent_objs.create(on: db).flatMap {

            let posts = stride(from: 0, to: addresses.count, by: 1).map { index -> ListingPostModel in
                //let agents = ListingAgentModel.query(on: db)
                //    .filter(\.$name == "Jill Biggs")
                //    .all()
                let agentId = agent_objs.randomElement()!.id! // @TODO - fix this
                let address = addresses[index]
                let slug = address.lowercased().replacingOccurrences(of: " ", with: "-").replacingOccurrences(of: "#", with: "-")
                // Generate random 7-character string to append to slug to avoid db conflicts with identical addresses
                let letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                let random = String((0..<7).map{ _ in letters.randomElement()! })
                let unique_slug = "\(slug)-\(random)"
                /*
                let views = stride(from: 0, to: addresses.count, by: 1).map { index -> ListingViewsModel in 
                    let listingId = posts[index]
                }
                */
                return ListingPostModel(address: address,
                                     slug: unique_slug,
                                     url_zillow: url_dict["zillow"]![index] as! String,
                                     url_redfin: url_dict["redfin"]![index] as! String,
                                     url_cb: url_dict["cb"]![index] as! String,
                                     date: Date(),
                                     agentId: agentId)
            }
            //print("posts: \(posts)")
            return posts.create(on: db)
        }
    }
    
    func revert(on db: Database) -> EventLoopFuture<Void> {
        db.eventLoop.flatten([
            ListingPostModel.query(on: db).delete(),
            ListingAgentModel.query(on: db).delete(),
        ])
    }
}




