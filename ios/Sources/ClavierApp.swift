import SwiftUI

@main struct ClavierApp: App {
    @StateObject private var model = KeyboardModel()
    var body: some Scene { WindowGroup { RemoteView(model: model) } }
}

struct RemoteView: View {
    @ObservedObject var model: KeyboardModel
    @Environment(\.scenePhase) private var scene
    @State private var panel = "Raccourcis"
    @State private var settings = false
    @State private var addFavorite = false
    private let panels = ["Raccourcis", "Chiffres", "Navigation", "Applications", "Musique", "Favoris"]
    private let columns = [GridItem(.adaptive(minimum: 160), spacing: 12)]

    var body: some View {
        VStack(spacing: 12) {
            HStack {
                Label("Mon PC · Clavier iPad", systemImage: "desktopcomputer").font(.headline)
                Spacer()
                Button("Connexion", systemImage: "network") { settings = true }
            }
            Text(model.message).font(.footnote).foregroundStyle(.secondary).frame(maxWidth: .infinity, alignment: .leading)
            ScrollView(.horizontal, showsIndicators: false) {
                HStack { ForEach(panels, id: \.self) { title in
                    Button(title) { panel = title }.tint(panel == title ? .green : .gray)
                } }.buttonStyle(.bordered)
            }
            ScrollView {
                LazyVGrid(columns: panel == "Chiffres" ? Array(repeating: GridItem(.flexible(), spacing: 12), count: 4) : columns, spacing: 12) { controls }
            }
            .disabled(!model.connected || model.busy)
            HStack {
                ForEach(["Ctrl", "Alt", "Shift", "Win", "AltGr"], id: \.self) { mod in
                    Button(mod == "Shift" ? "Maj" : mod) {
                        if model.modifiers.contains(mod) { model.modifiers.remove(mod) }
                        else { model.modifiers.insert(mod) }
                    }.tint(model.modifiers.contains(mod) ? .green : .gray)
                    .frame(maxWidth: .infinity)
                }
                Button("Reprendre ici") { model.resume() }.disabled(model.busy)
            }.buttonStyle(.borderedProminent).controlSize(.large)
            Text("Touche ci-dessous pour ouvrir le clavier iPad").font(.caption).foregroundStyle(.secondary)
            NativeInput(model: model).frame(height: 80)
        }
        .padding().background(Color(.systemGroupedBackground))
        .sheet(isPresented: $settings) { connectionSheet }
        .sheet(isPresented: $addFavorite) { FavoriteEditor(model: model) }
        .task {
            await model.connect()
            while !Task.isCancelled {
                do { try await Task.sleep(nanoseconds: 15_000_000_000) } catch { break }
                if model.active && !model.connected { await model.connect() }
            }
        }
        .onChange(of: scene) { _, next in
            model.active = next == .active
            if next != .active { model.blocked = true; model.modifiers.removeAll() }
        }
    }
    private func tile(_ title: String, subtitle: String = "", action: @escaping () -> Void) -> some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 8) {
                Text(title).font(.title3.bold())
                if !subtitle.isEmpty { Text(subtitle).font(.caption).foregroundStyle(.secondary).lineLimit(2) }
            }.frame(maxWidth: .infinity, minHeight: 64, alignment: .leading).padding(12)
        }.buttonStyle(.bordered)
    }
    @ViewBuilder private var controls: some View {
        switch panel {
        case "Chiffres":
            ForEach(["7","8","9","/","4","5","6","*","1","2","3","-","0",",",".","+"], id: \.self) { value in
                tile(value) { model.action(["type":"text", "text":value]) }
            }
            tile("Effacer") { model.key("Backspace", mods: []) }
            tile("Entrée") { model.key("Enter", mods: []) }
        case "Navigation":
            ForEach(["Tab","Esc","Enter","Backspace","Delete","Left","Up","Down","Right","Home","End","PageUp","PageDown"] + (1...12).map { "F\($0)" }, id: \.self) { key in
                tile(key) { model.key(key) }
            }
        case "Applications":
            ForEach(["browser","notepad","discord","explorer","calculator","paint"], id: \.self) { app in
                tile(["browser":"Navigateur", "notepad":"Bloc-notes", "discord":"Discord", "explorer":"Explorateur", "calculator":"Calculatrice", "paint":"Paint"][app]!) { model.action(["type":"app", "app":app]) }
            }
        case "Musique":
            ForEach(["volume_down","volume_up","mute","play_pause","previous","next"], id: \.self) { action in
                tile(["volume_down":"Volume −", "volume_up":"Volume +", "mute":"Muet / son", "play_pause":"Lecture / Pause", "previous":"Précédent", "next":"Suivant"][action]!) { model.action(["type":"media", "action":action]) }
            }
        case "Favoris":
            tile("＋ Créer un bouton") { addFavorite = true }
            ForEach(model.favorites) { item in
                tile(item.name, subtitle: item.isText ? item.text : (item.mods + [item.key]).joined(separator: " + ")) {
                    if item.isText { model.action(["type":"text", "text":item.text]) }
                    else { model.key(item.key, mods: item.mods) }
                }.contextMenu {
                    Button("Supprimer", role: .destructive) { model.favorites.removeAll { $0.id == item.id }; model.saveFavorites() }
                }
            }
        default:
            ForEach(["C","V","X","Z","Y","A","S","F","T","P"], id: \.self) { key in
                tile(["C":"Copier", "V":"Coller", "X":"Couper", "Z":"Annuler", "Y":"Rétablir", "A":"Tout sélectionner", "S":"Enregistrer", "F":"Rechercher", "T":"Nouvel onglet", "P":"Imprimer…"][key]!, subtitle: "Ctrl + \(key)") { model.key(key, mods: ["Ctrl"]) }
            }
            tile("Changer de fenêtre", subtitle: "Alt + Tab") { model.key("Tab", mods: ["Alt"]) }
            tile("Bureau", subtitle: "Win + D") { model.key("D", mods: ["Win"]) }
        }
    }
    private var connectionSheet: some View {
        NavigationStack {
            Form {
                Section("Adresse affichée sur ton PC") {
                    TextField("https://192.168…:18443", text: $model.address).textInputAutocapitalization(.never).autocorrectionDisabled().keyboardType(.URL)
                    Button("Reconnecter l’iPad mémorisé") { Task { await model.connect(); if model.connected { settings = false } } }.disabled(model.busy)
                }
                Section("Premier appairage") {
                    TextField("Code à 8 chiffres", text: $model.code).keyboardType(.numberPad)
                    Button("Mémoriser cet iPad") { Task { await model.connect(pair: true); if model.connected { settings = false } } }.disabled(model.busy || model.code.count != 8)
                    Text("Si Safari était déjà appairé, clique d’abord sur Nouveau code dans le compagnon Windows.").font(.footnote)
                }
                Text(model.message)
                Text("Le certificat local du PC doit être installé et approuvé dans les réglages iPad. L’application ne contourne pas les erreurs de certificat.").font(.footnote)
            }.navigationTitle("Connexion locale").toolbar { Button("Fermer") { settings = false } }
        }
    }
}

struct FavoriteEditor: View {
    @ObservedObject var model: KeyboardModel
    @Environment(\.dismiss) private var dismiss
    @State private var name = ""
    @State private var text = ""
    @State private var key = "C"
    @State private var isText = true
    @State private var mods: Set<String> = []
    var body: some View {
        NavigationStack {
            Form {
                TextField("Nom du bouton", text: $name)
                Toggle("Texte favori", isOn: $isText)
                if isText { TextEditor(text: $text).frame(minHeight: 130) }
                else {
                    Picker("Touche", selection: $key) { ForEach(Array("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789").map(String.init) + ["Tab","Esc","Enter"] + (1...12).map { "F\($0)" }, id: \.self) { Text($0).tag($0) } }
                    ForEach(["Ctrl","Alt","Shift","Win"], id: \.self) { mod in
                        Toggle(mod, isOn: Binding(get: { mods.contains(mod) }, set: { on in if on { mods.insert(mod) } else { mods.remove(mod) } }))
                    }
                }
            }.navigationTitle("Nouveau bouton").toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Annuler") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Enregistrer") {
                        model.favorites.append(Favorite(name: name.trimmingCharacters(in: .whitespacesAndNewlines), text: text, key: key, mods: Array(mods), isText: isText))
                        model.saveFavorites(); dismiss()
                    }.disabled(name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || name.count > 40 || model.favorites.count >= 40 || (isText && (text.isEmpty || text.count > 2000)))
                }
            }
        }
    }
}
