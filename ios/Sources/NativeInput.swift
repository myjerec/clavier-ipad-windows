import SwiftUI
import UIKit

// UITextView retains Apple's keyboard, predictions, dictation and composition.
struct NativeInput: UIViewRepresentable {
    @ObservedObject var model: KeyboardModel
    func makeCoordinator() -> Coordinator { Coordinator(self) }
    func makeUIView(context: Context) -> UITextView {
        let view = UITextView()
        view.delegate = context.coordinator
        view.font = .preferredFont(forTextStyle: .title3)
        view.autocorrectionType = .yes
        view.spellCheckingType = .yes
        view.autocapitalizationType = .sentences
        view.backgroundColor = .secondarySystemBackground
        view.layer.cornerRadius = 12
        view.accessibilityLabel = "Écrire directement sur le PC"
        return view
    }
    func updateUIView(_ view: UITextView, context: Context) {
        context.coordinator.parent = self
        if view.markedTextRange == nil && view.text != model.text { view.text = model.text }
        view.isEditable = model.connected && !model.blocked
    }
    final class Coordinator: NSObject, UITextViewDelegate {
        var parent: NativeInput
        init(_ parent: NativeInput) { self.parent = parent }
        func textViewDidChange(_ view: UITextView) {
            guard view.markedTextRange == nil else { return }
            parent.model.changed(view.text)
        }
        func textView(_ view: UITextView, shouldChangeTextIn range: NSRange, replacementText text: String) -> Bool {
            guard !parent.model.modifiers.isEmpty else { return true }
            guard !parent.model.busy else { return false }
            let key = text.uppercased()
            if key.count == 1 && key.range(of: "^[A-Z0-9]$", options: .regularExpression) != nil {
                parent.model.key(key)
            } else { parent.model.message = "Choisis une lettre simple pour la combinaison." }
            return false
        }
    }
}
