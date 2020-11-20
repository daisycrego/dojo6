import Vapor
import Fluent
import Leaf

struct ListingFrontendController {

    func listingView(req: Request) throws -> EventLoopFuture<View> {
        ListingPostModel.query(on: req.db)
            .sort(\.$date, .descending)
            .with(\.$agent)
            .all()
            .mapEach(\.leafData)
            .flatMap {
                req.leaf.render(template: "Listing/Frontend/Listing", context: [
                    "title": .string("JBG Listings - Listing"),
                    "posts": .array($0),
                ])
            }
    }

    func postView(req: Request) throws -> EventLoopFuture<Response> {
        let slug = req.url.path.trimmingCharacters(in: .init(charactersIn: "/"))
        
        return ListingPostModel.query(on: req.db)
            .filter(\.$slug == slug)
            .with(\.$agent)
            .first()
            .flatMap { post in
                guard let post = post else {
                    return req.eventLoop.future(req.redirect(to: "/"))
                }
                let context: LeafRenderer.Context = [
                    "title": .string("JBG Listings - \(post.title)"),
                    "post": post.leafData,
                ]
                return req.leaf.render(template: "Listing/Frontend/Post", context: context).encodeResponse(for: req)
            }
    }
}
