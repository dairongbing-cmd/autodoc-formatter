// Preview: render formatted HTML in iframe
document.addEventListener("DOMContentLoaded", () => {
    const btnBack = document.getElementById("btn-back-config");
    const btnDownload = document.getElementById("btn-download");

    btnBack?.addEventListener("click", () => {
        AppState.showPanel("config");
    });

    btnDownload?.addEventListener("click", async () => {
        await formatAndDownload();
    });
});

async function loadPreview() {
    if (!AppState.docId) return;
    const frame = document.getElementById("preview-frame");
    if (!frame) return;

    try {
        const rules = AppState.rules || {};
        const resp = await fetch(`/api/documents/${AppState.docId}/rules`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ rules: rules }),
        });
        if (!resp.ok) throw new Error("保存规则失败");

        const previewResp = await fetch(`/api/documents/${AppState.docId}/preview`);
        if (!previewResp.ok) throw new Error("生成预览失败");

        const html = await previewResp.text();
        frame.srcdoc = html;
    } catch (e) {
        alert("预览加载失败: " + e.message);
    }
}
