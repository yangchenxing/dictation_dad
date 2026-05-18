// app.js - Dictation Dad 前端逻辑

const App = {
    state: {
        currentPath: "",
        currentFile: null,
        entries: [],
        playParams: null,
        dictationPath: "",
        settings: {},
        pollInterval: null,
        audioContext: null,
    },

    async init() {
        this.bindEvents();
        await this.loadSettings();
        await this.showHome();
    },

    bindEvents() {
        document.getElementById("back-btn").addEventListener("click", () => this.goHome());
        document.getElementById("settings-btn").addEventListener("click", () => this.openSettings());
        document.getElementById("home-settings-btn").addEventListener("click", () => this.openSettings());


        document.getElementById("add-modal-close").addEventListener("click", () => this.closeAddModal());
        document.getElementById("create-dir-option").addEventListener("click", () => this.showCreateDirForm());
        document.getElementById("upload-file-option").addEventListener("click", () => this.showUploadForm());
        document.getElementById("create-dir-confirm").addEventListener("click", () => this.createDirectory());
        document.getElementById("create-dir-cancel").addEventListener("click", () => this.hideAddForms());
        document.getElementById("upload-file-confirm").addEventListener("click", () => this.uploadFile());
        document.getElementById("upload-file-cancel").addEventListener("click", () => this.hideAddForms());

        document.getElementById("preview-close").addEventListener("click", () => this.closePreview());
        document.getElementById("start-dictation-btn").addEventListener("click", () => this.startDictation());
        document.getElementById("delete-file-btn").addEventListener("click", () => this.deleteFile());

        document.getElementById("prepare-confirm").addEventListener("click", () => this.confirmPreGenerate());
        document.getElementById("prepare-cancel").addEventListener("click", () => this.goHome());

        document.getElementById("wait-sequential").addEventListener("click", () => this.startPlay(false));
        document.getElementById("wait-random").addEventListener("click", () => this.startPlay(true));

        document.getElementById("finish-stage").addEventListener("click", () => this.showReview());

        document.getElementById("settings-save").addEventListener("click", () => this.saveSettings());
        document.getElementById("settings-cancel").addEventListener("click", () => this.closeSettings());
    },

    async callApi(method, ...args) {
        if (window.pywebview && window.pywebview.api && typeof window.pywebview.api[method] === "function") {
            const timeout = new Promise((_, reject) =>
                setTimeout(() => reject(new Error("API 调用超时")), 10000)
            );
            try {
                return await Promise.race([window.pywebview.api[method](...args), timeout]);
            } catch (e) {
                console.error("API call failed:", method, e);
                return { success: false, error: e.message || "API 调用失败" };
            }
        }
        console.warn("pywebview API not ready, method:", method, args);
        return { success: false, error: "pywebview API 尚未就绪" };
    },

    // 首页
    async showHome() {
        this.hideAllPages();
        document.getElementById("home-page").classList.remove("hidden");
        document.getElementById("global-nav").classList.add("hidden");
        await this.loadDirectory(this.state.currentPath);
    },

    goHome() {
        this.stopDictation();
        this.state.currentPath = "";
        this.showHome();
    },

    async loadDirectory(path) {
        let res;
        for (let attempt = 0; attempt < 3; attempt++) {
            res = await this.callApi("list_directory", path);
            if (res.success) break;
            // Wait before retry, giving pywebview bridge time to stabilize
            await this.sleep(300);
        }
        if (!res.success) {
            this.renderFileListError("加载目录失败: " + res.error);
            return;
        }
        this.renderBreadcrumb(path);
        this.renderFileList(res.data);
    },

    renderBreadcrumb(path) {
        const parts = path ? path.split(/[\\/]/) : [];
        const build = (containerId) => {
            const container = document.getElementById(containerId);
            container.innerHTML = "";
            const rootSpan = document.createElement("span");
            rootSpan.textContent = "首页";
            rootSpan.addEventListener("click", () => {
                this.state.currentPath = "";
                this.loadDirectory("");
            });
            container.appendChild(rootSpan);
            let current = "";
            for (const part of parts) {
                if (!part) continue;
                const sep = document.createElement("span");
                sep.textContent = " / ";
                sep.className = "sep";
                container.appendChild(sep);
                current = current ? current + "/" + part : part;
                const span = document.createElement("span");
                span.textContent = part;
                const captured = current;
                span.addEventListener("click", () => {
                    this.state.currentPath = captured;
                    this.loadDirectory(captured);
                });
                container.appendChild(span);
            }
        };
        build("breadcrumb");
        build("home-breadcrumb");
    },

    renderFileList(data) {
        const container = document.getElementById("file-list");
        container.innerHTML = "";
        for (const dir of data.directories) {
            const item = document.createElement("div");
            item.className = "file-item";
            item.innerHTML = `<div class="file-icon">📁</div><div class="file-name">${dir.name}</div>`;
            item.addEventListener("click", () => {
                this.state.currentPath = this.state.currentPath ? this.state.currentPath + "/" + dir.name : dir.name;
                this.loadDirectory(this.state.currentPath);
            });
            container.appendChild(item);
        }
        for (const file of data.files) {
            const item = document.createElement("div");
            item.className = "file-item";
            item.innerHTML = `<div class="file-icon">${file.icon}</div><div class="file-name">${file.display_name}</div>`;
            item.addEventListener("click", () => this.openPreview(file));
            container.appendChild(item);
        }
        // 在文件列表最后添加 + 按钮
        const addItem = document.createElement("div");
        addItem.className = "file-item add-item";
        addItem.innerHTML = `<div class="file-icon" style="font-size:36px;">+</div><div class="file-name">新增</div>`;
        addItem.addEventListener("click", () => this.openAddModal());
        container.appendChild(addItem);
    },

    renderFileListError(message) {
        const container = document.getElementById("file-list");
        container.innerHTML = "";
        const errorDiv = document.createElement("div");
        errorDiv.style.cssText = "padding:24px;text-align:center;color:#c62828;";
        errorDiv.innerHTML = `<p>${message}</p><button class="btn" style="margin-top:12px;">重试</button>`;
        errorDiv.querySelector("button").addEventListener("click", () => this.loadDirectory(this.state.currentPath));
        container.appendChild(errorDiv);
    },

    // 预览
    async openPreview(file) {
        this.state.currentFile = file;
        const filePath = this.state.currentPath ? this.state.currentPath + "/" + file.name : file.name;
        const res = await this.callApi("preview_csv", filePath);
        if (!res.success) {
            alert("预览失败: " + res.error);
            return;
        }
        document.getElementById("preview-title").textContent = file.name;
        document.getElementById("preview-modal").classList.remove("hidden");

        const columns = res.data.length > 0
            ? Object.keys(res.data[0]).map(k => ({ title: k, field: k }))
            : [];

        if (this.previewTable) {
            this.previewTable.destroy();
        }
        this.previewTable = new Tabulator("#preview-table", {
            data: res.data,
            columns: columns,
            layout: "fitColumns",
            height: "400px",
        });
    },

    closePreview() {
        document.getElementById("preview-modal").classList.add("hidden");
        this.state.currentFile = null;
    },

    async deleteFile() {
        if (!this.state.currentFile) return;
        if (!confirm("确定要删除文件 " + this.state.currentFile.name + " 吗？")) return;
        const filePath = this.state.currentPath ? this.state.currentPath + "/" + this.state.currentFile.name : this.state.currentFile.name;
        const res = await this.callApi("delete_file", filePath);
        if (!res.success) {
            alert("删除失败: " + res.error);
            return;
        }
        this.closePreview();
        await this.loadDirectory(this.state.currentPath);
    },

    // 添加模态框
    openAddModal() {
        document.getElementById("add-modal").classList.remove("hidden");
        document.getElementById("add-options").classList.remove("hidden");
        document.getElementById("create-dir-form").classList.add("hidden");
        document.getElementById("upload-file-form").classList.add("hidden");
        document.getElementById("add-modal-title").textContent = "选择操作";
    },

    closeAddModal() {
        document.getElementById("add-modal").classList.add("hidden");
    },

    showCreateDirForm() {
        document.getElementById("add-options").classList.add("hidden");
        document.getElementById("create-dir-form").classList.remove("hidden");
        document.getElementById("add-modal-title").textContent = "创建目录";
    },

    showUploadForm() {
        document.getElementById("add-options").classList.add("hidden");
        document.getElementById("upload-file-form").classList.remove("hidden");
        document.getElementById("add-modal-title").textContent = "上传CSV";
    },

    hideAddForms() {
        document.getElementById("create-dir-form").classList.add("hidden");
        document.getElementById("upload-file-form").classList.add("hidden");
        document.getElementById("add-options").classList.remove("hidden");
        document.getElementById("add-modal-title").textContent = "选择操作";
    },

    async createDirectory() {
        const name = document.getElementById("dir-name-input").value.trim();
        if (!name) {
            alert("请输入目录名");
            return;
        }
        const res = await this.callApi("create_directory", this.state.currentPath, name);
        if (!res.success) {
            alert("创建失败: " + res.error);
            return;
        }
        document.getElementById("dir-name-input").value = "";
        this.closeAddModal();
        await this.loadDirectory(this.state.currentPath);
    },

    async uploadFile() {
        const input = document.getElementById("file-input");
        if (!input.files || input.files.length === 0) {
            alert("请选择文件");
            return;
        }
        const file = input.files[0];
        const reader = new FileReader();
        reader.onload = async (e) => {
            const content = e.target.result;
            const res = await this.callApi("upload_csv", this.state.currentPath, file.name, content, false);
            if (!res.success) {
                if (res.exists) {
                    if (confirm("文件已存在，是否覆盖？")) {
                        const overwriteRes = await this.callApi("upload_csv", this.state.currentPath, file.name, content, true);
                        if (!overwriteRes.success) {
                            alert("上传失败: " + overwriteRes.error);
                            return;
                        }
                    } else {
                        return;
                    }
                } else {
                    alert("上传失败: " + res.error);
                    return;
                }
            }
            input.value = "";
            this.closeAddModal();
            await this.loadDirectory(this.state.currentPath);
        };
        reader.readAsText(file);
    },

    // 听写流程
    async startDictation() {
        if (!this.state.currentFile) return;
        this.state.dictationPath = this.state.currentPath ? this.state.currentPath + "/" + this.state.currentFile.name : this.state.currentFile.name;
        this.closePreview();
        this.hideAllPages();
        document.getElementById("dictation-page").classList.remove("hidden");
        document.getElementById("global-nav").classList.remove("hidden");
        await this.showPrepare();
    },

    hideAllPages() {
        document.getElementById("home-page").classList.add("hidden");
        document.getElementById("dictation-page").classList.add("hidden");
        document.querySelectorAll(".dictation-stage").forEach(el => el.classList.add("hidden"));
    },

    async showPrepare() {
        const stage = document.getElementById("prepare-stage");
        stage.classList.remove("hidden");
        document.getElementById("prepare-actions").classList.add("hidden");
        document.getElementById("progress-container").classList.add("hidden");

        const res = await this.callApi("get_dictation_info", this.state.dictationPath);
        if (!res.success) {
            alert("加载听写信息失败: " + res.error);
            this.goHome();
            return;
        }
        this.state.entries = res.data.entries;
        this.state.playParams = res.data.play_params;

        const msg = document.getElementById("prepare-message");
        if (res.data.missing_count === 0) {
            this.showWait();
            return;
        } else {
            msg.textContent = `需要预生成 ${res.data.missing_count} 个音频，是否开始？`;
            document.getElementById("prepare-actions").classList.remove("hidden");
        }
    },

    async confirmPreGenerate() {
        document.getElementById("prepare-actions").classList.add("hidden");
        document.getElementById("progress-container").classList.remove("hidden");

        const res = await this.callApi("start_pre_generate", this.state.dictationPath);
        if (!res.success) {
            alert("启动预生成失败: " + res.error);
            this.goHome();
            return;
        }
        if (!res.data.started) {
            this.showWait();
            return;
        }

        this.state.pollInterval = setInterval(async () => {
            const progressRes = await this.callApi("get_pre_generate_progress");
            if (!progressRes.success) {
                clearInterval(this.state.pollInterval);
                alert("获取进度失败: " + progressRes.error);
                this.goHome();
                return;
            }
            const p = progressRes.data;
            if (p.error) {
                clearInterval(this.state.pollInterval);
                alert("生成失败: " + p.error);
                this.goHome();
                return;
            }
            const total = p.total || 1;
            const pct = total > 0 ? (p.current / total) * 100 : 100;
            document.getElementById("progress-fill").style.width = pct + "%";
            let text = p.text;
            if (text.length > 30) text = text.substring(0, 27) + "...";
            document.getElementById("progress-text").textContent = `${p.current}/${total} ${text}`;
            if (p.done) {
                clearInterval(this.state.pollInterval);
                this.showWait();
            }
        }, 500);
    },

    showWait() {
        document.querySelectorAll(".dictation-stage").forEach(el => el.classList.add("hidden"));
        document.getElementById("wait-stage").classList.remove("hidden");
    },

    stopDictation() {
        if (this.state.pollInterval) {
            clearInterval(this.state.pollInterval);
            this.state.pollInterval = null;
        }
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio = null;
        }
        if (this.timerId) {
            clearTimeout(this.timerId);
            this.timerId = null;
        }
    },

    // 播放
    async startPlay(shuffle) {
        document.querySelectorAll(".dictation-stage").forEach(el => el.classList.add("hidden"));
        document.getElementById("play-stage").classList.remove("hidden");

        // Initialize AudioContext on user gesture to avoid suspension
        if (!this.state.audioContext && (window.AudioContext || window.webkitAudioContext)) {
            this.state.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (this.state.audioContext && this.state.audioContext.state === "suspended") {
            await this.state.audioContext.resume();
        }

        let entries = [...this.state.entries];
        if (shuffle) {
            entries.sort(() => Math.random() - 0.5);
        }
        this.state.playEntries = entries;
        this.state.currentIndex = 0;
        await this.playCurrent();
    },

    async playCurrent() {
        const idx = this.state.currentIndex;
        const entries = this.state.playEntries;
        const total = entries.length;
        if (idx >= total) {
            this.showFinish();
            return;
        }
        const entry = entries[idx];
        document.getElementById("play-progress").textContent = `${idx + 1}/${total}`;
        document.getElementById("play-timer").textContent = "-";

        const count = this.state.playParams.play_count;
        for (let i = 0; i < count; i++) {
            await this.playAudio(entry);
            if (i < count - 1) {
                await this.sleep(2000);
            }
        }

        const wait = this.state.playParams.wait_time;
        const audioDuration = this.currentAudioDuration || 0;
        const waitTime = Math.ceil(Math.max(audioDuration * wait.audio_duration_factor + wait.extra_wait_time, wait.min_wait_time));
        await this.countdown(waitTime);
        this.state.currentIndex++;
        await this.playCurrent();
    },

    playAudio(entry) {
        return new Promise(async (resolve) => {
            const res = await this.callApi("get_audio_base64", entry.speech);
            if (!res.success) {
                console.error("Failed to load audio:", res.error);
                resolve();
                return;
            }
            const blob = this.base64ToBlob(res.data, "audio/mpeg");
            const url = URL.createObjectURL(blob);
            this.currentAudio = new Audio(url);
            this.currentAudioDuration = 0;
            this.currentAudio.addEventListener("loadedmetadata", () => {
                this.currentAudioDuration = this.currentAudio.duration || 0;
            });
            this.currentAudio.addEventListener("ended", () => {
                URL.revokeObjectURL(url);
                resolve();
            });
            this.currentAudio.addEventListener("error", () => {
                URL.revokeObjectURL(url);
                resolve();
            });
            this.currentAudio.play().catch(resolve);
        });
    },

    base64ToBlob(base64, mime) {
        const binary = atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return new Blob([bytes], { type: mime });
    },

    sleep(ms) {
        return new Promise(r => setTimeout(r, ms));
    },

    async countdown(seconds) {
        const beepCount = this.state.playParams.countdown_beep_count;
        const timerEl = document.getElementById("play-timer");
        for (let s = seconds; s > 0; s--) {
            timerEl.textContent = s;
            if (s <= beepCount) {
                await this.beep();
                await this.sleep(900);
            } else {
                await this.sleep(1000);
            }
        }
        timerEl.textContent = "0";
    },

    async beep() {
        if (!window.AudioContext && !window.webkitAudioContext) return;
        if (!this.state.audioContext) {
            this.state.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        const ctx = this.state.audioContext;
        if (ctx.state === "suspended") {
            await ctx.resume();
        }
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.frequency.value = 800;
        gain.gain.value = 0.1;
        osc.start();
        await this.sleep(100);
        osc.stop();
    },

    showFinish() {
        document.querySelectorAll(".dictation-stage").forEach(el => el.classList.add("hidden"));
        document.getElementById("finish-stage").classList.remove("hidden");
    },

    // 回顾
    showReview() {
        document.querySelectorAll(".dictation-stage").forEach(el => el.classList.add("hidden"));
        document.getElementById("review-stage").classList.remove("hidden");
        const grid = document.getElementById("review-grid");
        grid.innerHTML = "";

        const entries = this.state.playEntries || this.state.entries;
        const items = entries.map(e => ({
            answer: e.answer,
            hint: e.speech !== e.answer ? e.speech : "",
        }));

        // 计算列数
        let columns = 5;
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        const marginW = vw * 0.01; // 0.5vw each side
        const paddingW = vw * 0.01;
        const availWidth = vw - marginW * 2;
        const gap = 8;

        const answerFontSize = Math.min(vw * 0.05, vh * 0.11);
        const hintFontSize = Math.min(vw * 0.02, vh * 0.05);

        // 尝试逐步减少列数
        for (let c = 5; c >= 1; c--) {
            const colWidth = (availWidth - (c - 1) * gap) / c - paddingW * 2;
            let fits = true;
            for (const item of items) {
                const answerWidth = item.answer.length * answerFontSize * 0.8;
                const hintWidth = item.hint ? item.hint.length * hintFontSize * 0.8 : 0;
                if (Math.max(answerWidth, hintWidth) > colWidth) {
                    fits = false;
                    break;
                }
            }
            if (fits) {
                columns = c;
                break;
            }
        }
        grid.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;

        for (const item of items) {
            const div = document.createElement("div");
            div.className = "review-item";
            let html = `<div class="review-answer">${this.escapeHtml(item.answer)}</div>`;
            if (item.hint) {
                html += `<div class="review-hint">${this.escapeHtml(item.hint)}</div>`;
            }
            div.innerHTML = html;
            grid.appendChild(div);
        }
    },

    escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    },

    // 设置
    async loadSettings() {
        const res = await this.callApi("get_settings");
        if (res.success) {
            this.state.settings = res.data;
        }
    },

    openSettings() {
        const s = this.state.settings;
        document.getElementById("setting-duration").value = s.audio_duration_factor ?? 1.5;
        document.getElementById("setting-extra").value = s.extra_wait_time ?? 3.0;
        document.getElementById("setting-min").value = s.min_wait_time ?? 5.0;
        document.getElementById("setting-beep").value = s.countdown_beep_count ?? 3;
        document.getElementById("settings-modal").classList.remove("hidden");
    },

    closeSettings() {
        document.getElementById("settings-modal").classList.add("hidden");
    },

    showErrorModal(message) {
        let modal = document.getElementById("error-modal");
        if (!modal) {
            modal = document.createElement("div");
            modal.id = "error-modal";
            modal.className = "modal";
            modal.innerHTML = `
                <div class="modal-content error-content">
                    <p id="error-message"></p>
                    <button id="error-back-btn" class="btn">返回</button>
                </div>
            `;
            document.body.appendChild(modal);
            document.getElementById("error-back-btn").addEventListener("click", () => {
                modal.classList.add("hidden");
                this.goHome();
            });
        }
        document.getElementById("error-message").textContent = message;
        modal.classList.remove("hidden");
    },

    async saveSettings() {
        const data = {
            audio_duration_factor: parseFloat(document.getElementById("setting-duration").value),
            extra_wait_time: parseFloat(document.getElementById("setting-extra").value),
            min_wait_time: parseFloat(document.getElementById("setting-min").value),
            countdown_beep_count: parseInt(document.getElementById("setting-beep").value),
        };
        const res = await this.callApi("save_settings", data);
        if (!res.success) {
            alert("保存失败: " + res.error);
            return;
        }
        this.state.settings = { ...this.state.settings, ...data };
        this.closeSettings();
    },
};

function startApp() {
    // Small delay to let pywebview's Python-side message handler fully initialize
    setTimeout(() => App.init(), 50);
}

function isApiReady() {
    return window.pywebview && window.pywebview.api && Object.keys(window.pywebview.api).length > 0;
}

if (isApiReady()) {
    startApp();
} else {
    let started = false;
    const doStart = () => {
        if (!started) {
            started = true;
            startApp();
        }
    };

    window.addEventListener("pywebviewready", doStart);

    let attempts = 0;
    const timer = setInterval(() => {
        if (isApiReady()) {
            clearInterval(timer);
            doStart();
        } else if (++attempts >= 100) {
            clearInterval(timer);
            if (!started) {
                document.body.innerHTML = '<div style="padding:40px;text-align:center;"><h1>Dictation Dad</h1><p>加载失败：未检测到 pywebview 环境。<br>请通过 <code>python main.py</code> 启动程序。</p></div>';
            }
        }
    }, 100);
}
