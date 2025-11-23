import Foundation
import SwiftUI

/// Manages service instances, including support for multiple instances of the same service
class ServiceManager: ObservableObject {
    @Published var services: [ServiceInstance] = []

    init() {
        loadDefaultServices()
    }

    private func loadDefaultServices() {
        // Add default services
        services = [
            ServiceInstance(
                service: WebService.allServices.first(where: { $0.name == "ChatGPT" })!,
                instanceName: nil
            ),
            ServiceInstance(
                service: WebService.allServices.first(where: { $0.name == "Claude" })!,
                instanceName: nil
            ),
            ServiceInstance(
                service: WebService.allServices.first(where: { $0.name == "Claude Code" })!,
                instanceName: nil
            ),
            ServiceInstance(
                service: WebService.allServices.first(where: { $0.name == "Gemini" })!,
                instanceName: nil
            ),
            ServiceInstance(
                service: WebService.allServices.first(where: { $0.name == "Grok" })!,
                instanceName: nil
            ),
            ServiceInstance(
                service: WebService.allServices.first(where: { $0.name == "GitHub Copilot" })!,
                instanceName: "Account 1"
            )
        ]
    }

    func addServiceInstance(service: WebService, customName: String? = nil) {
        let instance = ServiceInstance(service: service, instanceName: customName)
        services.append(instance)
    }

    func removeServiceInstance(at index: Int) {
        guard index < services.count else { return }
        services.remove(at: index)
    }

    func duplicateService(at index: Int, newName: String) {
        guard index < services.count else { return }
        let original = services[index]
        let duplicate = ServiceInstance(
            service: original.service,
            instanceName: newName
        )
        services.insert(duplicate, at: index + 1)
    }
}

/// Represents an instance of a web service (allows multiple instances of the same service)
struct ServiceInstance: Identifiable, Equatable {
    let id = UUID()
    let service: WebService
    let instanceName: String?

    var displayName: String {
        if let instanceName = instanceName {
            return "\(service.name) - \(instanceName)"
        }
        return service.name
    }

    var dataStoreID: String {
        // Unique identifier for separate cookie/cache stores
        return "\(service.name)-\(id.uuidString)"
    }

    static func == (lhs: ServiceInstance, rhs: ServiceInstance) -> Bool {
        lhs.id == rhs.id
    }
}
