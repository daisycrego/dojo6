import Foundation
import Fluent

struct ListingMigration_v1_0_0: Migration {
    
    func prepare(on db: Database) -> EventLoopFuture<Void> {
        db.eventLoop.flatten([
            db.schema(ListingAgentModel.schema)
                .id()
                .field(ListingAgentModel.FieldKeys.name, .string, .required)
                .create(),
            db.schema(ListingPostModel.schema)
                .id()
                .field(ListingPostModel.FieldKeys.address, .string, .required)
                .field(ListingPostModel.FieldKeys.slug, .string, .required)
                .field(ListingPostModel.FieldKeys.url_zillow, .data)
                .field(ListingPostModel.FieldKeys.url_redfin, .data)
                .field(ListingPostModel.FieldKeys.url_cb, .data)
                .field(ListingPostModel.FieldKeys.date, .datetime, .required)
                .field(ListingPostModel.FieldKeys.agentId, .uuid)
                .foreignKey(ListingPostModel.FieldKeys.agentId,
                            references: ListingAgentModel.schema, .id,
                            onDelete: .cascade,
                            onUpdate: .cascade)
                .unique(on: ListingPostModel.FieldKeys.slug)
                .create(),
            db.schema(ListingViewsModel.schema)
                .id()
                .field(ListingViewsModel.FieldKeys.date, .datetime, .required)
                .field(ListingViewsModel.FieldKeys.views_zillow, .int, .required)
                .field(ListingViewsModel.FieldKeys.views_redfin, .int, .required)
                .field(ListingViewsModel.FieldKeys.views_cb, .int, .required)
                .field(ListingViewsModel.FieldKeys.listingId, .uuid)
                .foreignKey(ListingViewsModel.FieldKeys.listingId,
                            references: ListingPostModel.schema, .id,
                            onDelete: .cascade,
                            onUpdate: .cascade)
                .unique(on: ListingViewsModel.FieldKeys.date)
                .create(),
        ])
    }
    
    func revert(on db: Database) -> EventLoopFuture<Void> {
        db.eventLoop.flatten([
            db.schema(ListingAgentModel.schema).delete(),
            db.schema(ListingPostModel.schema).delete(),
            db.schema(ListingViewsModel.schema).delete(),
        ])
    }
}
