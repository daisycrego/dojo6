import Vapor

struct ListingRouter: RouteCollection {
    
    let frontendController = ListingFrontendController()
    let postAdminController = ListingPostAdminController()
    let agentAdminController = ListingAgentAdminController()
    let viewsAdminController = ListingViewsAdminController()
    
    func boot(routes: RoutesBuilder) throws {

        routes.get("listing", use: frontendController.listingView)
        routes.get("listing", "views", use: frontendController.listingViews)
        routes.get("listing", "views", .anything, use: frontendController.listingViewsDetailView)
        routes.get(.anything, use: frontendController.postView)

        let protected = routes.grouped([
            UserModelSessionAuthenticator(),
            UserModel.redirectMiddleware(path: "/")
        ])
        let listing = protected.grouped("admin", "listing")
        
        postAdminController.setupRoutes(on: listing, as: "posts")
        agentAdminController.setupRoutes(on: listing, as: "agents")
        viewsAdminController.setupRoutes(on: listing, as: "views")
    }
}
