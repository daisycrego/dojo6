import Leaf

extension ListingPostModel: LeafDataRepresentable {

    var leafData: LeafData {
        .dictionary([
            "id": .string(id?.uuidString),
            "address": .string(address),
            "slug": .string(slug),
            "url_zillow": .string(url_zillow),
            "url_redfin": .string(url_redfin),
            "url_cb": .string(url_cb),
            "date": .double(date.timeIntervalSinceReferenceDate),
            "agent": $agent.value != nil ? agent.leafData : .dictionary(nil),
        ])
    }
}

extension ListingPostModel: FormFieldStringOptionRepresentable {
    var formFieldStringOption: FormFieldStringOption {
        .init(key: id!.uuidString, label: address)
    }
}
