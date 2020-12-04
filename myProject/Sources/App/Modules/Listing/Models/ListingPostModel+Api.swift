import Vapor

extension ListingPostModel: ApiRepresentable {

    struct ListItem: Content {
        var id: UUID
        var address: String
        var slug: String
        var url_zillow: String
        var url_redfin: String
        var url_cb: String
        var date: Date
    }

    struct GetContent: Content {
        var id: UUID
        var address: String
        var slug: String
        var url_zillow: String
        var url_redfin: String
        var url_cb: String
        var date: Date
    }
    
    struct UpsertContent: ValidatableContent {
        var address: String
        var slug: String
        var url_zillow: String
        var url_redfin: String
        var url_cb: String
        var date: Date
    }

    struct PatchContent: ValidatableContent {
        var address: String?
        var slug: String?
        var url_zillow: String
        var url_redfin: String
        var url_cb: String
        var date: Date?
    }
    
    var listContent: ListItem {
        .init(id: id!,
              address: address,
              slug: slug,
              url_zillow: url_zillow,
              url_redfin: url_redfin,
              url_cb: url_cb,
              date: date)
    }

    var getContent: GetContent {
        .init(id: id!,
              address: address,
              slug: slug,
              url_zillow: url_zillow,
              url_redfin: url_redfin,
              url_cb: url_redfin,
              date: date)
    }
    
    private func upsert(_ newValue: UpsertContent) throws {
        address = newValue.address
        slug = newValue.slug
        url_zillow = newValue.url_zillow
        url_redfin = newValue.url_redfin
        url_cb = newValue.url_cb
        date = newValue.date
    }

    func create(_ content: UpsertContent) throws {
        try upsert(content)
    }

    func update(_ content: UpsertContent) throws {
        try upsert(content)
    }

    func patch(_ newValue: PatchContent) throws {
        address = newValue.address ?? address
        slug = newValue.slug ?? slug
        url_zillow = newValue.url_zillow ?? url_zillow
        url_redfin = newValue.url_redfin ?? url_redfin
        url_cb = newValue.url_cb ?? url_cb
        date = newValue.date ?? date
    }
}
