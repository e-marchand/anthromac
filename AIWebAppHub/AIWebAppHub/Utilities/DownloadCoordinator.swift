import Foundation
import WebKit
import AppKit

class DownloadCoordinator: NSObject {
    weak var webView: WKWebView?
    private var activeDownloads: [String: URLSessionDownloadTask] = [:]

    init(webView: WKWebView) {
        self.webView = webView
        super.init()
        setupDownloadHandling()
    }

    private func setupDownloadHandling() {
        // Add JavaScript to intercept download links
        let downloadScript = """
        (function() {
            document.addEventListener('click', function(e) {
                var target = e.target;
                while (target && target.tagName !== 'A') {
                    target = target.parentElement;
                }

                if (target && target.download) {
                    e.preventDefault();
                    window.webkit.messageHandlers.downloadHandler.postMessage({
                        url: target.href,
                        filename: target.download
                    });
                }
            }, true);
        })();
        """

        let script = WKUserScript(
            source: downloadScript,
            injectionTime: .atDocumentEnd,
            forMainFrameOnly: false
        )

        webView?.configuration.userContentController.addUserScript(script)
        webView?.configuration.userContentController.add(self, name: "downloadHandler")
    }

    func handleDownload(url: URL, suggestedFilename: String? = nil) {
        // Show save panel
        let savePanel = NSSavePanel()
        savePanel.canCreateDirectories = true
        savePanel.nameFieldStringValue = suggestedFilename ?? url.lastPathComponent

        savePanel.begin { response in
            if response == .OK, let destinationURL = savePanel.url {
                self.downloadFile(from: url, to: destinationURL)
            }
        }
    }

    private func downloadFile(from url: URL, to destinationURL: URL) {
        let session = URLSession(configuration: .default)
        let downloadTask = session.downloadTask(with: url) { [weak self] tempURL, response, error in
            guard let self = self else { return }

            if let error = error {
                DispatchQueue.main.async {
                    self.showError("Download failed: \(error.localizedDescription)")
                }
                return
            }

            guard let tempURL = tempURL else {
                DispatchQueue.main.async {
                    self.showError("Download failed: No file received")
                }
                return
            }

            do {
                // Remove existing file if it exists
                if FileManager.default.fileExists(atPath: destinationURL.path) {
                    try FileManager.default.removeItem(at: destinationURL)
                }

                // Move downloaded file to destination
                try FileManager.default.moveItem(at: tempURL, to: destinationURL)

                DispatchQueue.main.async {
                    self.showSuccess("File downloaded successfully")
                    // Optionally reveal in Finder
                    NSWorkspace.shared.activateFileViewerSelecting([destinationURL])
                }
            } catch {
                DispatchQueue.main.async {
                    self.showError("Failed to save file: \(error.localizedDescription)")
                }
            }
        }

        downloadTask.resume()
        activeDownloads[url.absoluteString] = downloadTask
    }

    private func showError(_ message: String) {
        let alert = NSAlert()
        alert.messageText = "Download Error"
        alert.informativeText = message
        alert.alertStyle = .warning
        alert.addButton(withTitle: "OK")
        alert.runModal()
    }

    private func showSuccess(_ message: String) {
        let alert = NSAlert()
        alert.messageText = "Download Complete"
        alert.informativeText = message
        alert.alertStyle = .informational
        alert.addButton(withTitle: "OK")
        alert.runModal()
    }

    deinit {
        webView?.configuration.userContentController.removeScriptMessageHandler(forName: "downloadHandler")
    }
}

extension DownloadCoordinator: WKScriptMessageHandler {
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        if message.name == "downloadHandler" {
            guard let dict = message.body as? [String: Any],
                  let urlString = dict["url"] as? String,
                  let url = URL(string: urlString) else {
                return
            }

            let filename = dict["filename"] as? String
            handleDownload(url: url, suggestedFilename: filename)
        }
    }
}
