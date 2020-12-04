import Vapor

extension ListingAgentModel: ListContentRepresentable {

    struct ListItem: Content {
        var id: String
        var name: String

        init(model: ListingAgentModel) {
            id = model.id!.uuidString
            name = model.name
        }
    }

    var listContent: ListItem { .init(model: self) }
}

extension ListingAgentModel: GetContentRepresentable {

    struct GetContent: Content {
        var id: String
        var name: String
        
        var posts: [ListingPostModel.ListItem]?

        init(model: ListingAgentModel) {
            id = model.id!.uuidString
            name = model.name
        }
    }

    var getContent: GetContent { .init(model: self) }
}

extension ListingAgentModel: CreateContentRepresentable {

    struct CreateContent: ValidatableContent {
        var name: String
        
        static func validations(_ validations: inout Validations) {
            validations.add("name", as: String.self, is: !.empty)
        }
    }

    func create(_ content: CreateContent) throws {
        name = content.name
    }
}

extension ListingAgentModel: UpdateContentRepresentable {

    struct UpdateContent: ValidatableContent {
        var name: String
        
        static func validations(_ validations: inout Validations) {
            validations.add("name", as: String.self, is: !.empty)
        }
    }
    
    func update(_ content: UpdateContent) throws {
        name = content.name
    }
}

extension ListingAgentModel: PatchContentRepresentable {

    struct PatchContent: ValidatableContent {
        var name: String
        
        static func validations(_ validations: inout Validations) {
            validations.add("name", as: String.self, is: !.empty)
        }
    }
    
    func patch(_ content: PatchContent) throws {
        name = content.name
    }
}

extension ListingAgentModel: DeleteContentRepresentable {}
