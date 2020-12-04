import Vapor
import Fluent

struct ListingViewsApiController: ListContentController,
                                  GetContentController,
                                  CreateContentController,
                                  UpdateContentController,
                                  PatchContentController,
                                  DeleteContentController
{
    typealias Model = ListingViewsModel
    
    func get(_ req: Request) throws -> EventLoopFuture<ListingViewsModel.GetContent> {
        try find(req).flatMap { views in
            print(views)
            return ListingPostModel.query(on: req.db)
                //.filter(\.$listing.$id == views)
                .all()
                .map { posts in
                    var details = views.getContent
                    details.posts = posts.map(\.listContent)
                    return details
                }
        }
    }

}
