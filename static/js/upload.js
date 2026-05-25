// Upload: drag/drop, file input, API call
document.addEventListener("DOMContentLoaded", () => {
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const btnSelect = document.getElementById("btn-select-file");
    const btnNext = document.getElementById("btn-next-config");
    const uploadResult = document.getElementById("upload-result");

    if (!dropZone || !fileInput) return;

    // Click to select
    dropZone.addEventListener("click", () => fileInput.click());
    btnSelect?.addEventListener("click", (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    // Drag and drop
    ["dragenter", "dragover"].forEach(evt => {
        dropZone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropZone.classList.add("dragover");
        });
    });
    ["dragleave", "drop"].forEach(evt => {
        dropZone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropZone.classList.remove("dragover");
        });
    });

    dropZone.addEventListener("drop", (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) handleFile(files[0]);
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) handleFile(fileInput.files[0]);
    });

    async function handleFile(file) {
        hideError("upload-error");
        uploadResult?.classList.add("hidden");

        const allowedExtensions = [".docx", ".txt", ".md", ".markdown"];
        const ext = "." + file.name.split(".").pop().toLowerCase();
        const checkExt = ext === ".markdown" ? ".md" : ext;
        if (!allowedExtensions.includes(checkExt) && checkExt !== ".markdown") {
            let realExt = ext;
            if (ext === ".markdown") realExt = ".md";
            if (!allowedExtensions.includes(realExt)) {
                showError("upload-error", `不支持的文件格式: ${ext}。支持: ${allowedExtensions.join(", ")}`);
                return;
            }
        }

        if (file.size > 50 * 1024 * 1024) {
            showError("upload-error", `文件过大: ${formatSize(file.size)}。最大允许 50MB`);
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        // Show loading state
        dropZone.style.opacity = "0.5";

        try {
            const resp = await fetch("/api/upload", { method: "POST", body: formData });
            if (!resp.ok) {
                const err = await resp.json();
                throw new Error(err.detail || "上传失败");
            }
            const data = await resp.json();
            AppState.setDocument(data);

            // Populate info
            document.getElementById("info-filename").textContent = data.filename;
            document.getElementById("info-type").textContent = data.detected_format.toUpperCase();
            document.getElementById("info-size").textContent = formatSize(data.size);
            document.getElementById("info-paragraphs").textContent = data.block_counts.paragraphs;
            document.getElementById("info-tables").textContent = data.block_counts.tables;
            uploadResult?.classList.remove("hidden");

            // Load presets into dropdown
            await loadPresets();
        } catch (err) {
            showError("upload-error", err.message);
        } finally {
            dropZone.style.opacity = "1";
        }
    }

    async function loadPresets() {
        try {
            const resp = await fetch("/api/presets");
            if (!resp.ok) return;
            const presets = await resp.json();
            const select = document.getElementById("preset-select");
            if (select) {
                select.innerHTML = '<option value="">-- 请选择预设 --</option>';
                presets.forEach(p => {
                    select.innerHTML += `<option value="${p.name}">${p.label} — ${p.description}</option>`;
                });
            }
        } catch (e) {
            // Silently fail — presets are optional
        }
    }

    // Next button
    btnNext?.addEventListener("click", () => {
        AppState.showPanel("config");
    });
});
