import Vapor
import Leaf

final class ListingViewsEditForm: Form {
    typealias Model = ListingViewsModel
    
    struct Input: Decodable {
        var id: String
        var date: String
        var views_zillow: Int
        var views_redfin: Int
        var views_cb: Int
        var listingId: String
    }

    var id: String? = nil
    var date = StringFormField()
    var views_zillow = StringFormField()
    var views_redfin = StringFormField()
    var views_cb = StringFormField()
    var listing = StringSelectionFormField()
    
    var leafData: LeafData {
        .dictionary([
            "id": .string(id),
            "date": date.leafData,
            "views_zillow": views_zillow.leafData,
            "views_redfin": views_redfin.leafData,
            "views_cb": views_cb.leafData,
            "listing": listing.leafData,
        ])
    }

    init() {}

    init(req: Request) throws {
        let context = try req.content.decode(Input.self)
        if !context.id.isEmpty {
            id = context.id
        }
        date.value = context.date
        views_zillow.value = String(context.views_zillow)
        views_redfin.value = String(context.views_redfin)
        views_cb.value = String(context.views_cb)
        listing.value = context.listingId
    }
    
    func validate(req: Request) -> EventLoopFuture<Bool> {
        var valid = true
        
        if views_zillow.value.isEmpty {
            views_zillow.error = "Zillow views missing"
            valid = false
        }
        if views_redfin.value.isEmpty {
            views_redfin.error = "Redfin views missing"
            valid = false
        }
        if views_cb.value.isEmpty {
            views_cb.error = "Coldwell Banker views missing"
            valid = false
        }
        if DateFormatter.custom.date(from: date.value) == nil {
            date.error = "Invalid date"
            valid = false
        }
        
        let uuid = UUID(uuidString: self.listing.value)
        return ListingPostModel.find(uuid, on: req.db).map { [unowned self] model in
            if model == nil {
                listing.error = "Listing identifier error"
                valid = false
            }
            return valid
        }
    }
    
    func read(from model: Model)  {
        id = model.id!.uuidString
        date.value = DateFormatter.custom.string(from: model.date)
        views_zillow.value = String(model.views_zillow)
        views_redfin.value = String(model.views_redfin)
        views_cb.value = String(model.views_cb)
        listing.value = model.$listing.id.uuidString
    }
    
    func write(to model: Model) {
        model.date = DateFormatter.custom.date(from: date.value)!
        model.views_zillow = Int(views_zillow.value) ?? 0 
        model.views_redfin = Int(views_redfin.value) ?? 0
        model.views_cb = Int(views_cb.value) ?? 0
        model.$listing.id = UUID(uuidString: listing.value)!
    }
}
