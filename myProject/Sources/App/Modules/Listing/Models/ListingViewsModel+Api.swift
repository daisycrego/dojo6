import Vapor

extension ListingViewsModel: ListContentRepresentable {

    struct ListItem: Content {
        var id: String
        var date: Date
        var views_zillow: Int
        var views_redfin: Int
        var views_cb: Int

        init(model: ListingViewsModel) {
            id = model.id!.uuidString
            date = model.date
            views_zillow = model.views_zillow
            views_redfin = model.views_redfin
            views_cb = model.views_cb
        }
    }

    var listContent: ListItem { .init(model: self) }
}

extension ListingViewsModel: GetContentRepresentable {

    struct GetContent: Content {
        var id: String
        var date: Date
        var views_zillow: Int
        var views_redfin: Int
        var views_cb: Int
        
        var posts: [ListingPostModel.ListItem]?

        init(model: ListingViewsModel) {
            id = model.id!.uuidString
            date = model.date
            views_zillow = model.views_zillow
            views_redfin = model.views_redfin
            views_cb = model.views_cb
        }
    }

    var getContent: GetContent { .init(model: self) }
}

extension ListingViewsModel: CreateContentRepresentable {

    struct CreateContent: ValidatableContent {
        var date: Date
        var views_zillow: Int
        var views_redfin: Int
        var views_cb: Int
        
        static func validations(_ validations: inout Validations) {
            validations.add("date", as: Date.self)
            validations.add("views_zillow", as: Int.self, is: .range(0...))
            validations.add("views_redfin", as: Int.self, is: .range(0...))
            validations.add("views_cb", as: Int.self, is: .range(0...))
        }
    }

    func create(_ content: CreateContent) throws {
        date = content.date
        views_zillow = content.views_zillow
        views_redfin = content.views_redfin
        views_cb = content.views_cb
    }
}

extension ListingViewsModel: UpdateContentRepresentable {

    struct UpdateContent: ValidatableContent {
        var date: Date
        var views_zillow: Int
        var views_redfin: Int
        var views_cb: Int
        
        static func validations(_ validations: inout Validations) {
            validations.add("date", as: Date.self)
            validations.add("views_zillow", as: Int.self, is: .range(0...))
            validations.add("views_redfin", as: Int.self, is: .range(0...))
            validations.add("views_cb", as: Int.self, is: .range(0...))
        }
    }
    
    func update(_ content: UpdateContent) throws {
        date = content.date
        views_zillow = content.views_zillow
        views_redfin = content.views_redfin
        views_cb = content.views_cb
    }
}

extension ListingViewsModel: PatchContentRepresentable {

    struct PatchContent: ValidatableContent {
        var date: Date
        var views_zillow: Int
        var views_redfin: Int
        var views_cb: Int
        
        static func validations(_ validations: inout Validations) {
            validations.add("date", as: Date.self)
            validations.add("views_zillow", as: Int.self, is: .range(0...))
            validations.add("views_redfin", as: Int.self, is: .range(0...))
            validations.add("views_cb", as: Int.self, is: .range(0...))
        }
    }
    
    func patch(_ content: PatchContent) throws {
        date = content.date
        views_zillow = content.views_zillow
        views_redfin = content.views_redfin
        views_cb = content.views_cb
    }
}

extension ListingViewsModel: DeleteContentRepresentable {}
