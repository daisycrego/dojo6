import Vapor
import Leaf

final class ListingAgentEditForm: Form {

    typealias Model = ListingAgentModel
    
    struct Input: Decodable {
        var id: String
        var name: String
    }

    var id: String? = nil
    var name = StringFormField()

    var leafData: LeafData {
        .dictionary([
            "id": .string(id),
            "name": name.leafData,
        ])
    }

    init() {}

    init(req: Request) throws {
        let context = try req.content.decode(Input.self)
        if !context.id.isEmpty {
            id = context.id
        }
        name.value = context.name
    }
    
    func validate(req: Request) -> EventLoopFuture<Bool> {
        var valid = true
        
        if name.value.isEmpty {
            name.error = "Name is required"
            valid = false
        }
        return req.eventLoop.future(valid)
    }
    
    func read(from model: Model)  {
        id = model.id!.uuidString
        name.value = model.name
    }
    
    func write(to model: Model) {
        model.name = name.value
    }
}
