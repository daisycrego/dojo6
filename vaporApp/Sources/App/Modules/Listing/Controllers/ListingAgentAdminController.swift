import Vapor
import Fluent
import Leaf

struct ListingAgentAdminController: AdminViewController {
    typealias EditForm = ListingAgentEditForm
    typealias Model = ListingAgentModel
    
    var listView: String = "Listing/Admin/Agents/List"
    var editView: String = "Listing/Admin/Agents/Edit"
}
