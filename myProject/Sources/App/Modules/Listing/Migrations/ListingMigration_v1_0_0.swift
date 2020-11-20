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
                .field(ListingPostModel.FieldKeys.excerpt, .data, .required)
                .field(ListingPostModel.FieldKeys.date, .datetime, .required)
                .field(ListingPostModel.FieldKeys.content, .data, .required)
                .field(ListingPostModel.FieldKeys.agentId, .uuid)
                .foreignKey(ListingPostModel.FieldKeys.agentId,
                            references: ListingAgentModel.schema, .id,
                            onDelete: .cascade,
                            onUpdate: .cascade)
                .unique(on: ListingPostModel.FieldKeys.slug)
                .create(),
        ])
    }
    
    func revert(on db: Database) -> EventLoopFuture<Void> {
        db.eventLoop.flatten([
            db.schema(ListingAgentModel.schema).delete(),
            db.schema(ListingPostModel.schema).delete(),
        ])
    }
}
