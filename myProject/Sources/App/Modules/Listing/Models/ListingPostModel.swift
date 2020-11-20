import Vapor
import Fluent

final class ListingPostModel: Model {
    
    static let schema: String = "listing_posts"

    struct FieldKeys {
        static var address: FieldKey { "address" }
        static var slug: FieldKey { "slug" }
        static var excerpt: FieldKey { "excerpt" }
        static var date: FieldKey { "date" }
        static var content: FieldKey { "content" }
        static var agentId: FieldKey { "agent_id" }
    }
    
    @ID() var id: UUID?
    @Field(key: FieldKeys.address) var address: String
    @Field(key: FieldKeys.slug) var slug: String
    @Field(key: FieldKeys.excerpt) var excerpt: String
    @Field(key: FieldKeys.date) var date: Date
    @Field(key: FieldKeys.content) var content: String
    @Parent(key: FieldKeys.agentId) var agent: ListingAgentModel

    init() { }

    init(id: UUID? = nil,
         address: String,
         slug: String,
         excerpt: String,
         date: Date,
         content: String,
         agentId: UUID)
    {
        self.id = id
        self.address = address
        self.slug = slug
        self.excerpt = excerpt
        self.date = date
        self.content = content
        $agent.id = agentId
    }
}
