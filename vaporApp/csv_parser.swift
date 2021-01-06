import Foundation

func process(string: String) throws { 

    var addresses = [String]()
    var agents_for_listings = [String]()
    var all_agents = Set<String>()

    var url_dict = [
        "zillow": [],
        "redfin": [],
        "cb": []
    ]
	
    let lines = string.split(separator: "\r\n")
    print(lines.count)
    for (lineNumber, line) in lines.enumerated() {
        
        // skip the first line of headers: 
        // Address,LP,Agent,MLS,Zillow URL,Redfin URL,Coldwell Banker URL
        if lineNumber == 0 {
            continue
        } 

        let pattern = ",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)"
        let string = String(line)
        let regex = try! NSRegularExpression(pattern: pattern, options: NSRegularExpression.Options.caseInsensitive)
        let range = NSMakeRange(0, string.count)
        let modString = regex.stringByReplacingMatches(
            in: string, 
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
    print(addresses)
    print(agents_for_listings)
    print(url_dict)   
    print(all_agents)
}

func processFile(at url: URL) throws {
    let s = try String(contentsOf: url)
    try process(string: s)
}

func main() {
    guard CommandLine.arguments.count > 1 else {
        print("usage: \(CommandLine.arguments[0]) file...")
        return
    }
    for path in CommandLine.arguments[1...] {
        do {
            let u = URL(fileURLWithPath: path)
            try processFile(at: u)
        } catch {
            print("error processing: \(path): \(error)")
        }
    }
}

main()
exit(EXIT_SUCCESS)
