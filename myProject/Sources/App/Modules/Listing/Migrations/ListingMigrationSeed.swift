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
            "365 Park Ave",
            "116 Bloomfield St #1",
            "709 Monroe St #3",
            "288 Griffith St #1",
            "288 Griffith St #2",
            "290 Griffith St #1",
            "290 Griffith St #2",
            "41 Fulton St",
            "223 Brunswick",
            "176 Ogden Ave",
            "401 Jefferson St #3E",
            "1500 Washington St #7F",
            "315 Court St",
            "100 Manhattan Ave #1109",
            "609 Jefferson St #3B",
            "1 2nd St #1912",
            "84 Adams St #4A",
            "689 Luis Munoz Marin Blvd #PH2A",
            "160 Sussex St",
            "26 Avenue at Port Imperial #420",
            "397 3rd St #2",
            "320 Bloomfield St #1",
            "209 2nd St #4L",
            "205 Adams St #3",
            "754 Murray St",
            "118 Corbin Ave #204",
            "452 2nd St #1",
        ]

        return agent_objs.create(on: db).flatMap {

            let posts = stride(from: 0, to: addresses.count, by: 1).map { index -> ListingPostModel in
                
                //let agents = ListingAgentModel.query(on: db)
                //    .filter(\.$name == "Jill Biggs")
                //    .all()
                
                let agentId = agent_objs.randomElement()!.id! // @TODO - fix this
                let address = addresses[index]
                return ListingPostModel(title: address,
                                     slug: address.lowercased().replacingOccurrences(of: " ", with: "-"),
                                     excerpt: Lorem.sentence,
                                     date: Date().addingTimeInterval(-Double.random(in: 0...(86400 * 60))),
                                     content: Lorem.paragraph,
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




