import Vapor
import Leaf

final class ListingPostEditForm: Form {
    typealias Model = ListingPostModel
    
    struct Input: Decodable {
        var id: String
        var address: String
        var slug: String
        var url_zillow: String
        var url_redfin: String
        var url_cb: String
        var date: String
        var agentId: String
    }

    var id: String? = nil
    var address = StringFormField()
    var slug = StringFormField()
    var url_zillow = StringFormField()
    var url_redfin = StringFormField()
    var url_cb = StringFormField()
    var date = StringFormField()
    var agent = StringSelectionFormField()
    
    var leafData: LeafData {
        .dictionary([
            "id": .string(id),
            "address": address.leafData,
            "slug": slug.leafData,
            "url_zillow": url_zillow.leafData,
            "url_redfin": url_redfin.leafData,
            "url_cb": url_cb.leafData,
            "date": date.leafData,
            "agent": agent.leafData,
        ])
    }

    init() {}

    init(req: Request) throws {
        let context = try req.content.decode(Input.self)
        if !context.id.isEmpty {
            id = context.id
        }
        address.value = context.address
        slug.value = context.slug
        date.value = context.date
        url_zillow.value = context.url_zillow
        url_redfin.value = context.url_redfin
        url_cb.value = context.url_cb
        agent.value = context.agentId
    }
    
    func validate(req: Request) -> EventLoopFuture<Bool> {
        var valid = true
        
        if address.value.isEmpty {
            address.error = "Address is required"
            valid = false
        }
        if DateFormatter.custom.date(from: date.value) == nil {
            date.error = "Invalid date"
            valid = false
        }
        /*
        if url_zillow.value.isEmpty {
            url_zillow.error = "Zillow URL is required"
            valid = false
        }
        if url_redfin.value.isEmpty {
            url_redfin.error = "Redfin URL is required"
            valid = false
        }
        if url_cb.value.isEmpty {
            url_cb.error = "Coldwell Banker URL is required"
            valid = false
        }
        */
        let uuid = UUID(uuidString: self.agent.value)
        return ListingAgentModel.find(uuid, on: req.db).map { [unowned self] model in
            if model == nil {
                agent.error = "Agent identifier error"
                valid = false
            }
            return valid
        }
    }
    
    func read(from model: Model)  {
        id = model.id!.uuidString
        address.value = model.address
        slug.value = model.slug
        url_zillow.value = model.url_zillow
        url_redfin.value = model.url_redfin
        url_cb.value = model.url_cb
        date.value = DateFormatter.custom.string(from: model.date)
        agent.value = model.$agent.id.uuidString
    }
    
    func write(to model: Model) {
        model.address = address.value
        let slug = address.value.lowercased().replacingOccurrences(of: " ", with: "-").replacingOccurrences(of: "#", with: "-")
        let letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        let unique_slug = "\(slug)-\(String((0..<7).map{ _ in letters.randomElement()! }))"
        model.slug = unique_slug
        model.url_zillow = url_zillow.value
        model.url_redfin = url_redfin.value
        model.url_cb = url_cb.value
        model.date = DateFormatter.custom.date(from: date.value)!
        model.$agent.id = UUID(uuidString: agent.value)!
    }
}
