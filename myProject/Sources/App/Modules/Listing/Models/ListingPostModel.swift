import Vapor
import Fluent

final class ListingPostModel: Model {
    
    static let schema: String = "listing_posts"

    struct FieldKeys {
        static var title: FieldKey { "title" }
        static var slug: FieldKey { "slug" }
        static var excerpt: FieldKey { "excerpt" }
        static var date: FieldKey { "date" }
        static var content: FieldKey { "content" }
        static var AgentId: FieldKey { "agent_id" }
    }
    
    @ID() var id: UUID?
    @Field(key: FieldKeys.title) var title: String
    @Field(key: FieldKeys.slug) var slug: String
    @Field(key: FieldKeys.excerpt) var excerpt: String
    @Field(key: FieldKeys.date) var date: Date
    @Field(key: FieldKeys.content) var content: String
    @Parent(key: FieldKeys.AgentId) var agent: ListingAgentModel

    init() { }

    init(id: UUID? = nil,
         title: String,
         slug: String,
         excerpt: String,
         date: Date,
         content: String,
         agentId: UUID)
    {
        self.id = id
        self.title = title
        self.slug = slug
        self.excerpt = excerpt
        self.date = date
        self.content = content
        $agent.id = agentId
    }
}
