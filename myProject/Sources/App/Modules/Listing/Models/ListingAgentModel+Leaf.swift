import Leaf

extension ListingAgentModel: LeafDataRepresentable {

    var leafData: LeafData {
        .dictionary([
            "id": .string(id?.uuidString),
            "name": .string(name),
        ])
    }
}

extension ListingAgentModel: FormFieldStringOptionRepresentable {
    var formFieldStringOption: FormFieldStringOption {
        .init(key: id!.uuidString, label: name)
    }
}
