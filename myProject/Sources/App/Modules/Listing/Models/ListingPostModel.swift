import Vapor
import Fluent

final class ListingPostModel: Model {
    
    static let schema: String = "listing_posts"

    struct FieldKeys {
        static var address: FieldKey { "address" }
        static var slug: FieldKey { "slug" }
        static var url_zillow: FieldKey { "url_zillow" }
        static var url_redfin: FieldKey { "url_redfin "}
        static var url_cb: FieldKey { "url_cb" }
        static var date: FieldKey { "date" }
        static var agentId: FieldKey { "agent_id" }
    }
    
    @ID() var id: UUID?
    @Field(key: FieldKeys.address) var address: String
    @Field(key: FieldKeys.slug) var slug: String
    @Field(key: FieldKeys.url_zillow) var url_zillow: String
    @Field(key: FieldKeys.url_redfin) var url_redfin: String
    @Field(key: FieldKeys.url_cb) var url_cb: String
    @Field(key: FieldKeys.date) var date: Date
    @Parent(key: FieldKeys.agentId) var agent: ListingAgentModel

    init() { }

    init(id: UUID? = nil,
         address: String,
         slug: String,
         url_zillow: String,
         url_redfin: String,
         url_cb: String,
         date: Date,
         agentId: UUID)
    {
        self.id = id
        self.address = address
        self.slug = slug
        self.url_zillow = url_zillow
        self.url_redfin = url_redfin
        self.url_cb = url_cb
        self.date = date
        $agent.id = agentId
    }
}
