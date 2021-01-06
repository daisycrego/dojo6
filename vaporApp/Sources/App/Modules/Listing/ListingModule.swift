import Vapor
import Fluent

struct ListingModule: Module {
    
    var name: String = "listing"

    var router: RouteCollection? { ListingRouter() }

    var migrations: [Migration] {
        [
            ListingMigration_v1_0_0(),
            ListingMigrationSeed(),
        ]
    }
}
