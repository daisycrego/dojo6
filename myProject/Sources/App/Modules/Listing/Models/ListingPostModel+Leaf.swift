import Leaf

extension ListingPostModel: LeafDataRepresentable {

    var leafData: LeafData {
        .dictionary([
            "id": .string(id?.uuidString),
            "address": .string(address),
            "slug": .string(slug),
            "excerpt": .string(excerpt),
            "date": .double(date.timeIntervalSinceReferenceDate),
            "content": .string(content),
            "agent": $agent.value != nil ? agent.leafData : .dictionary(nil),
        ])
    }
}
