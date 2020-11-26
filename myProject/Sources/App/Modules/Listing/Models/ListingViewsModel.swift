import Vapor
import Fluent

final class ListingViewsModel: Model {
    
    static let schema: String = "listing_views"

    struct FieldKeys {
        static var date: FieldKey { "date" }
        static var views_zillow: FieldKey { "views_zillow" }
        static var views_redfin: FieldKey { "views_redfin "}
        static var views_cb: FieldKey { "views_cb" }
        static var listingId: FieldKey { "listing_id" }
    }
    
    @ID() var id: UUID?
    @Field(key: FieldKeys.date) var date: Date
    @Field(key: FieldKeys.views_zillow) var views_zillow: Int
    @Field(key: FieldKeys.views_redfin) var views_redfin: Int
    @Field(key: FieldKeys.views_cb) var views_cb: Int
    @Parent(key: FieldKeys.listingId) var listing: ListingPostModel

    init() { }

    init(id: UUID? = nil,
         date: Date,
         views_zillow: Int,
         views_redfin: Int,
         views_cb: Int,
         listingId: UUID)
    {
        self.id = id
        self.date = date
        self.views_zillow = views_zillow
        self.views_redfin = views_redfin
        self.views_cb = views_cb
        $listing.id = listingId
    }
}
