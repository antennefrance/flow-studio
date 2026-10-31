/**
 * FLOW Studio Frontend Controller.
 * Modular ES6 architecture. Zero inline JS.
 */

const CONFIG = Object.freeze({
    TELEMETRY_POLL_INTERVAL_MS: 2000,
    ENDPOINTS: {
        TELEMETRY: "/api/telemetry",
        GENERATE: "/api/generate"
    }
});

class FlowStudioApp {
    constructor() {
        this.ramValEl = document.getElementById("ram-val");
        this.messagesEl = document.getElementById("messages");
        this.promptInputEl = document.getElementById("prompt-input");
        this.modelSelectEl = document.getElementById("model-select");
        this.maxTokensEl = document.getElementById("max-tokens");
        this.sendBtnEl = document.getElementById("btn-send");

        this.initEventListeners();
        this.startTelemetryPolling();
    }

    initEventListeners() {
        this.sendBtnEl.addEventListener("click", () => this.handlePromptSubmit());

        this.promptInputEl.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                this.handlePromptSubmit();
            }
        });
    }

    async updateTelemetry() {
        try {
            const res = await fetch(CONFIG.ENDPOINTS.TELEMETRY);
            if (!res.ok) return;
            const data = await res.json();
            this.ramValEl.textContent = `${data.used_gb} GB / ${data.total_gb} GB (${data.percent}%)`;
        } catch (err) {
            console.debug("Telemetry polling skipped:", err);
        }
    }

    startTelemetryPolling() {
        this.updateTelemetry();
        setInterval(() => this.updateTelemetry(), CONFIG.TELEMETRY_POLL_INTERVAL_MS);
    }

    appendUserMessage(text) {
        const msg = document.createElement("div");
        msg.className = "msg user";
        msg.textContent = text;
        this.messagesEl.appendChild(msg);
        this.scrollToBottom();
    }

    createAssistantMessageElement() {
        const msg = document.createElement("div");
        msg.className = "msg assistant";
        msg.innerHTML = "<em>⚡ FLOW オンデマンド・ストリーミング開始...</em>";
        this.messagesEl.appendChild(msg);
        this.scrollToBottom();
        return msg;
    }

    scrollToBottom() {
        this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
    }

    async handlePromptSubmit() {
        const prompt = this.promptInputEl.value.trim();
        if (!prompt) return;

        this.appendUserMessage(prompt);
        this.promptInputEl.value = "";

        const assistantMsgEl = this.createAssistantMessageElement();
        const model = this.modelSelectEl.value;
        const maxTokens = parseInt(this.maxTokensEl.value, 10) || 128;

        try {
            const response = await fetch(CONFIG.ENDPOINTS.GENERATE, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt, model, max_tokens: maxTokens })
            });

            if (!response.ok) {
                throw new Error(`Server returned HTTP ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            assistantMsgEl.innerHTML = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const textChunk = decoder.decode(value);
                assistantMsgEl.innerHTML += textChunk.replace(/\n/g, "<br>");
                this.scrollToBottom();
            }
        } catch (error) {
            assistantMsgEl.innerHTML += `<br><span style="color:var(--danger-red);">エラー: ${error.message}</span>`;
            this.scrollToBottom();
        }
    }
}

// Bootstrap application on DOM ready
document.addEventListener("DOMContentLoaded", () => {
    window.flowStudio = new FlowStudioApp();
});

