import Foundation
import Security

enum TokenVault {
    static func query(_ host: String) -> [String: Any] {
        [kSecClass as String: kSecClassGenericPassword,
         kSecAttrService as String: "ClavierIPad.local", kSecAttrAccount as String: host]
    }
    static func read(_ host: String) -> String? {
        var q = query(host); q[kSecReturnData as String] = true
        var result: CFTypeRef?
        guard SecItemCopyMatching(q as CFDictionary, &result) == errSecSuccess,
              let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }
    static func save(_ token: String, host: String) throws {
        var q = query(host)
        let data = Data(token.utf8)
        let update = SecItemUpdate(q as CFDictionary, [kSecValueData as String: data] as CFDictionary)
        if update == errSecSuccess { return }
        guard update == errSecItemNotFound else { throw ClientError.message("Échec de sauvegarde dans le trousseau iOS.") }
        q[kSecValueData as String] = data
        q[kSecAttrAccessible as String] = kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        guard SecItemAdd(q as CFDictionary, nil) == errSecSuccess else {
            throw ClientError.message("Impossible de mémoriser cet iPad.")
        }
    }
}

enum ClientError: LocalizedError {
    case message(String)
    var errorDescription: String? { if case .message(let text) = self { return text }; return nil }
}

// No certificate exceptions: the PC certificate must be trusted in iPad settings.
final class NoRedirect: NSObject, URLSessionTaskDelegate {
    func urlSession(_ session: URLSession, task: URLSessionTask, willPerformHTTPRedirection response: HTTPURLResponse, newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void) { completionHandler(nil) }
}

final class Connection {
    let base: URL
    let origin: String
    private let session: URLSession
    init(address: String) throws {
        let address = address.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let url = URL(string: address), url.scheme == "https",
              let host = url.host, url.user == nil, url.password == nil,
              url.query == nil, url.fragment == nil,
              url.path.isEmpty || url.path == "/" else {
            throw ClientError.message("Utilise l’adresse HTTPS affichée sur le PC.")
        }
        let numbers = host.split(separator: ".").compactMap { Int($0) }
        guard host.split(separator: ".").count == 4, numbers.count == 4, numbers.allSatisfy({ (0...255).contains($0) }),
              numbers[0] == 10 || (numbers[0] == 192 && numbers[1] == 168) ||
              (numbers[0] == 172 && (16...31).contains(numbers[1])) else {
            throw ClientError.message("Seule une adresse IPv4 du réseau privé est acceptée.")
        }
        origin = "https://\(host):\(url.port ?? 18443)"
        base = URL(string: origin)!
        let config = URLSessionConfiguration.ephemeral
        config.httpShouldSetCookies = false
        config.timeoutIntervalForRequest = 5
        config.timeoutIntervalForResource = 8
        session = URLSession(configuration: config, delegate: NoRedirect(), delegateQueue: nil)
    }
    func post(_ path: String, body: [String: Any]) async throws {
        var request = URLRequest(url: base.appendingPathComponent(path))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(origin, forHTTPHeaderField: "Origin")
        request.setValue("1", forHTTPHeaderField: "X-Keyboard")
        if let token = TokenVault.read(origin) {
            request.setValue("keyboard=\(token)", forHTTPHeaderField: "Cookie")
        }
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else { throw ClientError.message("Réponse PC invalide.") }
        guard http.statusCode == 200 else {
            let result = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
            throw ClientError.message(result?["error"] as? String ?? "Connexion refusée.")
        }
        if let value = http.value(forHTTPHeaderField: "Set-Cookie"),
           let cookie = HTTPCookie.cookies(withResponseHeaderFields: ["Set-Cookie": value], for: base).first(where: { $0.name == "keyboard" }) {
            try TokenVault.save(cookie.value, host: origin)
        }
    }
}
