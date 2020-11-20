import Vapor
import Fluent
import Leaf

final class ListingAgentModel: Model {

    static let schema = "listing_agents"
    
    struct FieldKeys {
        static var name: FieldKey { "name" }
    }
    
    @ID() var id: UUID?
    @Field(key: FieldKeys.name) var name: String
    @Children(for: \.$agent) var posts: [ListingPostModel]
    
    init() { }
    
    init(id: UUID? = nil,
         name: String)
    {
        self.id = id
        self.name = name
    }
}

