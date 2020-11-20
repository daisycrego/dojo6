import Vapor
import Fluent
import LoremSwiftum

struct ListingMigrationSeed: Migration {
    
    func prepare(on db: Database) -> EventLoopFuture<Void> {

        //let agents = stride(from: 0, to: 3, by: 1).map { _ in ListingAgentModel(name: Lorem.title) }
        //print("agents: \(agents)")

        let agents = [
            "Andy Elkins", 
            "Bruna Santana", 
            "Elysa Lyons", 
            "Erica Pransky",
            "Francisco Ferreira",
            "Jeremy Lindberg",
            "Jill Biggs",
            "Sonia Lander",
            "Lauren Blumenfeld",
            "Matt Kraus",
            "Phoebe Crego",
            "Vanessa Mahapatra"
        ]

        var agent_objs = [ListingAgentModel]()
        for agent in agents {
            agent_objs.append(ListingAgentModel(name: agent))
        }

        let addresses = [
            "205 10th St #8V",
            "650 2nd St #2L",
            "218 Jefferson St #8",
            "609 Jefferson St #4A",
            "6600 Blvd E #9K",
            "154 Bowers St #1C",
            "20 East 43rd St",
            "604-606 Grand St #1",
            "369 Park Ave",
            "357 Park Ave",
            
        ]

        let url_dict = [
            "zillow": [
                "https://www.zillow.com/homedetails/205-10th-St-APT-8V-Jersey-City-NJ-07302/2077478011_zpid/?view=public",
                "https://www.zillow.com/homes/650-2nd-St-APT-2L,-Hoboken,-NJ-07030_rb/88862179_zpid/",
                "https://www.zillow.com/homes/202023986_rb/108622869_zpid/",
                "https://www.zillow.com/homes/202023440_rb/55346620_zpid/",
                "https://www.zillow.com/homedetails/6600-Blvd-E-APT-9K-West-New-York-NJ-07093/2083809279_zpid/?view=public",
                "https://www.zillow.com/homes/202024238_rb/38896873_zpid/",
                "https://www.zillow.com/homes/202011038_rb/38870506_zpid/",
                "https://www.zillow.com/homedetails/604-606-Grand-St-1-Hoboken-NJ-07030/108632712_zpid/?view=public",
                "https://www.zillow.com/homedetails/369-Park-Ave-Weehawken-NJ-07086/2078302584_zpid/?view=public",
                "https://www.zillow.com/homedetails/357-Park-Ave-Weehawken-NJ-07086/2077358151_zpid/?view=public",
            ], 
            "redfin": [
                "https://www.redfin.com/NJ/Jersey-City/205-10th-St-07302/unit-8V/home/173433600",
                "https://www.redfin.com/NJ/Hoboken/650-2nd-St-07030/unit-2L/home/36427568",
                "https://www.redfin.com/NJ/Hoboken/218-Jefferson-St-07030/unit-8/home/39922549",
                "https://www.redfin.com/NJ/Hoboken/609-Jefferson-St-07030/unit-4A/home/36650701",
                "https://www.redfin.com/NJ/West-New-York/6600-JFK-Blvd-E-07093/unit-9K/home/59144954",
                "https://www.redfin.com/NJ/Jersey-City/154-Bowers-St-07307/unit-1C/home/173213335",
                "https://www.redfin.com/NJ/Bayonne/20-E-43rd-St-07002/home/36463923",
                "https://www.redfin.com/NJ/Hoboken/604-Grand-St-07030/unit-1/home/39921891",
                "https://www.redfin.com/NJ/Weehawken/369-Park-Ave-07086/home/172689922",
                "https://www.redfin.com/NJ/Weehawken/357-Park-Ave-07086/home/173531770",
            ], 
            "cb": [
                "https://www.coldwellbankerhomes.com/nj/jersey-city/205-10th-st-8v/pid_38490669/",
                "https://www.coldwellbankerhomes.com/nj/hoboken/650-2nd-st-2l/pid_37856855/",
                "https://www.coldwellbankerhomes.com/nj/hoboken/218-jefferson-st-8/pid_38552610/",
                "https://www.coldwellbankerhomes.com/nj/hoboken/609-jefferson-st-4a/pid_38470159/",
                "https://www.coldwellbankerhomes.com/nj/west-new-york/6600-blvd-e-9k/pid_38488296/",
                "https://www.coldwellbankerhomes.com/nj/jersey-city/154-bowers-st-1c/pid_38583255/",
                "https://www.coldwellbankerhomes.com/nj/bayonne/20-east-43rd-st/pid_36523174/",
                "https://www.coldwellbankerhomes.com/nj/hoboken/604-606-grand-st-1/pid_37325335/",
                "https://www.coldwellbankerhomes.com/nj/weehawken/369-park-ave/pid_37447822/",
                "https://www.coldwellbankerhomes.com/nj/weehawken/357-park-ave/pid_38643138/"
                ]
        ]

        return agent_objs.create(on: db).flatMap {

            let posts = stride(from: 0, to: addresses.count, by: 1).map { index -> ListingPostModel in
                
                //let agents = ListingAgentModel.query(on: db)
                //    .filter(\.$name == "Jill Biggs")
                //    .all()
                
                let agentId = agent_objs.randomElement()!.id! // @TODO - fix this
                let address = addresses[index]
                let zillow_urls = url_dict["zillow"]
                print(zillow_urls)
                return ListingPostModel(address: address,
                                     slug: address.lowercased().replacingOccurrences(of: " ", with: "-").replacingOccurrences(of: "#", with: "-"),
                                     url_zillow: url_dict["zillow"]![index],
                                     url_redfin: url_dict["redfin"]![index],
                                     url_cb: url_dict["cb"]![index],
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




