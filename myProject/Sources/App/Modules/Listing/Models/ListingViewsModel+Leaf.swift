import Leaf

extension ListingViewsModel: LeafDataRepresentable {

    var leafData: LeafData {
        .dictionary([
            "id": .string(id?.uuidString),
            "date": .double(date.timeIntervalSinceReferenceDate),
            "views_zillow": .int(views_zillow),
            "views_redfin": .int(views_redfin),
            "views_cb": .int(views_cb),
            "listing": $listing.value != nil ? listing.leafData : .dictionary(nil),
        ])
    }
}

