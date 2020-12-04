import Vapor
import Fluent

struct ListingAgentApiController: ListContentController,
                                  GetContentController,
                                  CreateContentController,
                                  UpdateContentController,
                                  PatchContentController,
                                  DeleteContentController
{
    typealias Model = ListingAgentModel
    
    func get(_ req: Request) throws -> EventLoopFuture<ListingAgentModel.GetContent> {
        try find(req).flatMap { agent in
            ListingPostModel.query(on: req.db)
                .filter(\.$agent.$id == agent.id!)
                .all()
                .map { posts in
                    var details = agent.getContent
                    details.posts = posts.map(\.listContent)
                    return details
                }
        }
    }

}
