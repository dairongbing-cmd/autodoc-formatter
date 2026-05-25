// Config: preset selection, form serialization, rule management
document.addEventListener("DOMContentLoaded", () => {
    const presetSelect = document.getElementById("preset-select");
    const btnApplyPreset = document.getElementById("btn-apply-preset");
    const btnPreview = document.getElementById("btn-preview");
    const btnFormat = document.getElementById("btn-format");

    // Apply preset to form
    btnApplyPreset?.addEventListener("click", async () => {
        const name = presetSelect?.value;
        if (!name) return;
        try {
            const resp = await fetch(`/api/presets/${name}`);
            if (!resp.ok) throw new Error("预设加载失败");
            const rules = await resp.json();
            populateForm(rules);
            AppState.rules = rules;
        } catch (e) {
            alert("加载预设失败: " + e.message);
        }
    });

    // Preview button
    btnPreview?.addEventListener("click", async () => {
        if (!AppState.docId) return;
        const rules = serializeForm();
        await saveRulesAndNavigate(rules, "preview");
    });

    // Format button
    btnFormat?.addEventListener("click", async () => {
        if (!AppState.docId) return;
        const rules = serializeForm();
        await saveRulesAndNavigate(rules, "download");
    });
});

function populateForm(rules) {
    const set = (id, val) => { const el = document.getElementById(id); if (el) el.value = val ?? ""; };
    const setChk = (id, val) => { const el = document.getElementById(id); if (el) el.checked = !!val; };

    if (rules.font) {
        set("cfg-font-family", rules.font.family);
        set("cfg-font-size", rules.font.size_pt);
        set("cfg-font-color", rules.font.color_hex);
    }
    if (rules.paragraph) {
        set("cfg-para-align", rules.paragraph.alignment);
        set("cfg-line-spacing", rules.paragraph.line_spacing);
        set("cfg-indent", rules.paragraph.first_line_indent_cm);
        set("cfg-space-before", rules.paragraph.space_before_pt);
        set("cfg-space-after", rules.paragraph.space_after_pt);
    }
    if (rules.page) {
        set("cfg-page-size", rules.page.size);
        set("cfg-orientation", rules.page.orientation);
        if (rules.page.margins_cm) {
            set("cfg-margin-top", rules.page.margins_cm.top_cm);
            set("cfg-margin-bottom", rules.page.margins_cm.bottom_cm);
            set("cfg-margin-left", rules.page.margins_cm.left_cm);
            set("cfg-margin-right", rules.page.margins_cm.right_cm);
        }
    }
    if (rules.header) {
        setChk("cfg-header-enabled", rules.header.enabled);
        set("cfg-header-text", rules.header.text);
        setChk("cfg-header-pagenum", rules.header.show_page_numbers);
    }
    if (rules.footer) {
        setChk("cfg-footer-enabled", rules.footer.enabled);
        set("cfg-footer-text", rules.footer.text);
        setChk("cfg-footer-pagenum", rules.footer.show_page_numbers);
    }
    AppState.rules = rules;
}

function serializeForm() {
    const get = (id) => document.getElementById(id)?.value;
    const getFloat = (id) => parseFloat(document.getElementById(id)?.value) || 0;
    const getChk = (id) => document.getElementById(id)?.checked || false;

    return {
        font: {
            family: get("cfg-font-family") || "Times New Roman",
            size_pt: getFloat("cfg-font-size") || 12,
            color_hex: get("cfg-font-color") || "#000000",
            bold_default: false,
            italic_default: false,
        },
        paragraph: {
            alignment: get("cfg-para-align") || "left",
            line_spacing: getFloat("cfg-line-spacing") || 1.15,
            first_line_indent_cm: parseFloat(get("cfg-indent")) || null,
            space_before_pt: getFloat("cfg-space-before"),
            space_after_pt: getFloat("cfg-space-after") || 6,
        },
        page: {
            size: get("cfg-page-size") || "A4",
            orientation: get("cfg-orientation") || "portrait",
            margins_cm: {
                top_cm: getFloat("cfg-margin-top") || 2.54,
                bottom_cm: getFloat("cfg-margin-bottom") || 2.54,
                left_cm: getFloat("cfg-margin-left") || 2.54,
                right_cm: getFloat("cfg-margin-right") || 2.54,
            },
        },
        headings: {
            1: { font_size_pt: 22, bold: true, italic: false },
            2: { font_size_pt: 18, bold: true, italic: false },
            3: { font_size_pt: 16, bold: true, italic: false },
            4: { font_size_pt: 14, bold: true, italic: false },
            5: { font_size_pt: 12, bold: true, italic: false },
            6: { font_size_pt: 11, bold: true, italic: false },
        },
        header: {
            enabled: getChk("cfg-header-enabled"),
            text: get("cfg-header-text") || null,
            show_page_numbers: getChk("cfg-header-pagenum"),
        },
        footer: {
            enabled: getChk("cfg-footer-enabled"),
            text: get("cfg-footer-text") || null,
            show_page_numbers: getChk("cfg-footer-pagenum"),
        },
        images: {
            max_width_cm: 16.0,
            alignment: "center",
            add_captions: true,
        },
    };
}

async function saveRulesAndNavigate(rules, target) {
    if (!AppState.docId) return;
    try {
        const resp = await fetch(`/api/documents/${AppState.docId}/rules`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ rules: rules }),
        });
        if (!resp.ok) throw new Error("保存规则失败");
        AppState.rules = rules;

        if (target === "preview") {
            loadPreview();
            AppState.showPanel("preview");
        } else if (target === "download") {
            await formatAndDownload();
        }
    } catch (e) {
        alert(e.message);
    }
}

async function formatAndDownload() {
    if (!AppState.docId) return;
    const status = document.getElementById("download-status");
    if (status) {
        status.textContent = "正在排版...";
        status.classList.remove("hidden");
    }

    try {
        const rules = AppState.rules || serializeForm();
        const resp = await fetch(`/api/documents/${AppState.docId}/format`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ rules: rules }),
        });
        if (!resp.ok) throw new Error("排版失败");
        const data = await resp.json();

        // Trigger download
        window.location.href = data.download_url;

        if (status) {
            status.textContent = "排版完成，文件已开始下载";
            status.classList.add("success");
        }
    } catch (e) {
        if (status) {
            status.textContent = "排版失败: " + e.message;
            status.classList.remove("success");
        }
    }
}
