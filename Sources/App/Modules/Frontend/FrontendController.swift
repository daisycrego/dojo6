import Vapor
import Leaf

struct FrontendController {
    
    func homeView(req: Request) throws -> EventLoopFuture<View> {
        var email: String?
        if let user = req.auth.get(UserModel.self) {
            email = user.email
        }
        return req.leaf.render(template: "Frontend/Home", context: [
            "title": .string("JBG Listings - Home"),
            "header": .string("Hi there,"),
            "message": .string("This is the JBG Listing Reports site."),
            "isLoggedIn": .bool(email != nil),
            "email": .string(email),
        ])
    }
}
