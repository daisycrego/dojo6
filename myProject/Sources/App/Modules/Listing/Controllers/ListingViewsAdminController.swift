import Vapor
import Fluent
import Leaf

struct ListingViewsAdminController: AdminViewController {
    typealias EditForm = ListingViewsEditForm
    typealias Model = ListingViewsModel
    
    var listView: String = "Listing/Admin/ListingViews/List"
    var editView: String = "Listing/Admin/ListingViews/Edit"

    func beforeRender(req: Request, form: ListingViewsEditForm) -> EventLoopFuture<Void> {
        ListingPostModel.query(on: req.db).all()
            .mapEach(\.formFieldStringOption)
            .map { form.listing.options = $0 }
    }
}
