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
        listing.get("views", "collect", use: viewsAdminController.collectViews)
        let listingApi = routes.grouped("api", "listing")
        
        let views = listingApi.grouped("views")
        let viewsApiController = ListingViewsApiController()
        viewsApiController.setupListRoute(routes: views)
        viewsApiController.setupGetRoute(routes: views)
        viewsApiController.setupCreateRoute(routes: views)
        viewsApiController.setupUpdateRoute(routes: views)
        viewsApiController.setupPatchRoute(routes: views)
        viewsApiController.setupDeleteRoute(routes: views)

        

        let agents = listingApi.grouped("agents")
        let agentApiController = ListingAgentApiController()
        agentApiController.setupListRoute(routes: agents)
        agentApiController.setupGetRoute(routes: agents)
        agentApiController.setupCreateRoute(routes: agents)
        agentApiController.setupUpdateRoute(routes: agents)
        agentApiController.setupPatchRoute(routes: agents)
        agentApiController.setupDeleteRoute(routes: agents)


        let postsApiController = ListingPostApiController()
        postsApiController.setupRoutes(routes: listingApi, on: "posts")

    }
}
