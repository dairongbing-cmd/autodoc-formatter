// AppState — holds the current document context and panel navigation
const AppState = {
    docId: null,
    filename: null,
    detectedFormat: null,
    rules: null,
    currentPanel: "upload",

    setDocument(data) {
        this.docId = data.doc_id;
        this.filename = data.filename;
        this.detectedFormat = data.detected_format;
    },

    reset() {
        this.docId = null;
        this.filename = null;
        this.detectedFormat = null;
        this.rules = null;
    },

    showPanel(name) {
        document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
        const panel = document.getElementById("panel-" + name);
        if (panel) {
            panel.classList.add("active");
            this.currentPanel = name;
        }
    }
};

// Error display helper
function showError(elementId, message) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = message;
        el.classList.remove("hidden");
    }
}

function hideError(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
        el.classList.add("hidden");
        el.textContent = "";
    }
}

// Format file size for display
function formatSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1024 / 1024).toFixed(1) + " MB";
}
