import Vapor
import Fluent
import Leaf
import Liquid

struct ListingPostAdminController: AdminViewController {
    
    typealias EditForm = ListingPostEditForm
    typealias Model = ListingPostModel
    
    var listView: String = "Listing/Admin/Posts/List"
    var editView: String = "Listing/Admin/Posts/Edit"
    
    func beforeRender(req: Request, form: ListingPostEditForm) -> EventLoopFuture<Void> {
        ListingAgentModel.query(on: req.db).all()
            .mapEach(\.formFieldStringOption)
            .map { form.agent.options = $0 }
    }
}

