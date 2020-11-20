import Vapor

struct ListingRouter: RouteCollection {
    
    let frontendController = ListingFrontendController()
    let postAdminController = ListingPostAdminController()
    let agentAdminController = ListingAgentAdminController()
    
    func boot(routes: RoutesBuilder) throws {

        routes.get("listing", use: frontendController.listingView)
        routes.get(.anything, use: frontendController.postView)

        let protected = routes.grouped([
            UserModelSessionAuthenticator(),
            UserModel.redirectMiddleware(path: "/")
        ])
        let listing = protected.grouped("admin", "listing")
        
        postAdminController.setupRoutes(on: listing, as: "posts")
        agentAdminController.setupRoutes(on: listing, as: "agents")
    }
}
