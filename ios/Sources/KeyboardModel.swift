import SwiftUI

struct Favorite: Identifiable, Codable {
    var id = UUID()
    var name: String
    var text: String
    var key: String
    var mods: [String]
    var isText: Bool
}

@MainActor final class KeyboardModel: ObservableObject {
    @Published var address = UserDefaults.standard.string(forKey: "pcAddress") ?? ""
    @Published var code = ""
    @Published var message = "Connecte ton iPad au compagnon Windows."
    @Published var connected = false
    @Published var busy = false
    @Published var blocked = false
    @Published var text = ""
    @Published var modifiers: Set<String> = []
    @Published var favorites: [Favorite] = []
    var active = true
    private var connection: Connection?
    private var sent = ""
    private var draft = UUID().uuidString

    init() {
        if let data = UserDefaults.standard.data(forKey: "favorites"),
           let saved = try? JSONDecoder().decode([Favorite].self, from: data) {
            favorites = Array(saved.prefix(40))
        }
    }
    func connect(pair: Bool = false) async {
        guard !busy else { return }
        busy = true; defer { busy = false }
        do {
            let candidate = try Connection(address: address)
            try await candidate.post(pair ? "pair" : "command", body: pair ? ["code": code] : ["type": "status"])
            connection = candidate; connected = true; code = ""
            UserDefaults.standard.set(candidate.origin, forKey: "pcAddress")
            message = "Connecté · touche la zone de saisie."
        } catch { connected = false; message = explanation(error) }
    }
    func explanation(_ error: Error) -> String {
        if let e = error as? URLError, [-1200,-1201,-1202,-1203].contains(e.errorCode) {
            return "Certificat non reconnu : installe le certificat du PC et active sa confiance dans les réglages iPad."
        }
        return error.localizedDescription
    }
    func changed(_ value: String) {
        text = value
        guard value.count <= 2000 else { blocked = true; message = "2 000 caractères maximum : ouvre une nouvelle zone."; return }
        Task { await flush() }
    }
    private func flush() async {
        guard !busy, connected, !blocked, active, let connection else { return }
        busy = true; defer { busy = false }
        do {
            while text != sent && active && !blocked {
                let snapshot = text
                try await connection.post("command", body: ["type": "direct", "draft": draft, "base": sent, "text": snapshot])
                sent = snapshot
                message = "Saisie directe · connecté"
            }
        } catch { blocked = true; message = explanation(error) + " Vérifie le PC puis touche Reprendre ici." }
    }
    func action(_ payload: [String: Any]) {
        guard connected, !busy, let connection else { message = "Patiente ou connecte le PC."; return }
        // Never drop an unsent draft when a shortcut arrives.
        guard text == sent else { message = "Attends la fin de la saisie avant ce raccourci."; return }
        if payload["type"] as? String != "media", !sent.isEmpty { blocked = true }
        busy = true
        Task {
            defer { busy = false }
            do { try await connection.post("command", body: payload); message = blocked ? "Commande envoyée · Reprendre ici pour écrire." : "Commande envoyée" }
            catch { blocked = true; message = explanation(error) }
        }
    }
    func key(_ key: String, mods: [String]? = nil) {
        let chosen = mods ?? Array(modifiers)
        modifiers.removeAll()
        action(["type": "key", "key": key, "mods": chosen])
    }
    func resume() {
        guard !busy else { return }
        text = ""; sent = ""; draft = UUID().uuidString; blocked = false
        message = "Nouvelle zone · le document PC reste inchangé."
    }
    func saveFavorites() {
        if let data = try? JSONEncoder().encode(favorites) { UserDefaults.standard.set(data, forKey: "favorites") }
    }
}
