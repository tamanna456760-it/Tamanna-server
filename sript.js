/**

* Tamanna AI — System Sync Controller
* Owner: HM INSAN ALI
* Module: Pull / Sync Management
* Requires an existing backend API.
* This module does not bypass server permissions.
    */

“use strict”;

const TamannaSync = (() => {
const CONFIG = Object.freeze({
apiBase: “/api/system”,
pullEndpoint: “/pull”,
timeoutMs: 30000,
maxRetries: 2,
retryDelayMs: 1000
});

let isPulling = false;
let activeController = null;
const state = {
    status: "idle",
    lastStartedAt: null,
    lastCompletedAt: null,
    lastResult: null,
    lastError: null
};
function updateStatus(status, details = {}) {
    state.status = status;
    const event = {
        module: "Tamanna AI",
        status,
        timestamp: new Date().toISOString(),
        ...details
    };
    console.log("[Tamanna Sync]", event);
    if (typeof document !== "undefined") {
        document.dispatchEvent(
            new CustomEvent("tamanna:sync-status", {
                detail: event
            })
        );
    }
    return event;
}
function getState() {
    return {
        ...state,
        isPulling
    };
}
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
async function requestJSON(url, options = {}) {
    let lastError;
    for (let attempt = 0; attempt <= CONFIG.maxRetries; attempt++) {
        const controller = new AbortController();
        activeController = controller;
        const timeout = setTimeout(
            () => controller.abort(),
            CONFIG.timeoutMs
        );
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal,
                headers: {
                    Accept: "application/json",
                    ...(options.headers || {})
                },
                credentials: "same-origin"
            });
            const contentType =
                response.headers.get("content-type") || "";
            const payload = contentType.includes("application/json")
                ? await response.json()
                : await response.text();
            if (!response.ok) {
                const message =
                    typeof payload === "object" && payload !== null
                        ? payload.detail || payload.message
                        : payload;
                const error = new Error(
                    message || `HTTP ${response.status}`
                );
                error.status = response.status;
                // Retry only likely temporary server errors.
                if (
                    response.status < 500 ||
                    attempt === CONFIG.maxRetries
                ) {
                    throw error;
                }
                lastError = error;
            } else {
                return payload;
            }
        } catch (error) {
            lastError = error;
            if (
                error.name === "AbortError" ||
                (error.status && error.status < 500) ||
                attempt === CONFIG.maxRetries
            ) {
                throw error;
            }
        } finally {
            clearTimeout(timeout);
            if (activeController === controller) {
                activeController = null;
            }
        }
        await delay(CONFIG.retryDelayMs * (attempt + 1));
    }
    throw lastError || new Error("Request failed.");
}
/**
 * Send a system action to the existing backend.
 * The backend must validate and authorize every action.
 */
async function callAPI(action, extra = {}) {
    if (typeof action !== "string" || !action.trim()) {
        throw new TypeError("A valid API action is required.");
    }
    const response = await requestJSON(
        `${CONFIG.apiBase}${CONFIG.pullEndpoint}`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                action,
                ...extra
            })
        }
    );
    return response;
}
/**
 * Pull the latest approved system changes.
 */
async function pullSystem() {
    if (isPulling) {
        updateStatus("busy", {
            message: "A pull operation is already running."
        });
        return {
            ok: false,
            status: "busy",
            message: "Pull already in progress."
        };
    }
    isPulling = true;
    state.lastStartedAt = new Date().toISOString();
    state.lastError = null;
    updateStatus("pulling", {
        message: "Starting system pull..."
    });
    try {
        const result = await callAPI("pull");
        if (result && result.ok === false) {
            throw new Error(
                result.message || "The server rejected the pull."
            );
        }
        state.lastResult = result;
        state.lastCompletedAt = new Date().toISOString();
        updateStatus("success", {
            message: "System pull completed.",
            result
        });
        return {
            ok: true,
            status: "success",
            result
        };
    } catch (error) {
        state.lastError = error.message || "Unknown error";
        updateStatus("error", {
            message: state.lastError
        });
        return {
            ok: false,
            status: "error",
            message: state.lastError
        };
    } finally {
        isPulling = false;
        activeController = null;
    }
}
/**
 * Cancel the active network request.
 * This does not guarantee that server-side work is cancelled.
 */
function cancelPull() {
    if (!activeController) {
        return false;
    }
    activeController.abort();
    updateStatus("cancel_requested", {
        message: "Cancellation requested."
    });
    return true;
}
/**
 * Optional UI status helper.
 */
function renderStatus(elementId = "tamanna-sync-status") {
    if (typeof document === "undefined") {
        return getState();
    }
    const element = document.getElementById(elementId);
    if (!element) {
        return getState();
    }
    const labels = {
        idle: "Ready",
        pulling: "Pulling system updates...",
        success: "Pull completed",
        error: "Pull failed",
        busy: "Operation already running",
        cancel_requested: "Cancellation requested"
    };
    element.textContent = labels[state.status] || state.status;
    element.dataset.status = state.status;
    return getState();
}
return Object.freeze({
    pullSystem,
    callAPI,
    cancelPull,
    getState,
    renderStatus
});

})();

/**

* Backward-compatible function for existing UI buttons.
    */
    async function pullSystem() {
    const result = await TamannaSync.pullSystem();
    TamannaSync.renderStatus();
    return result;
    }

/**

* Listen for status changes if the UI is present.
    */
    if (typeof document !== “undefined”) {
    document.addEventListener(“tamanna:sync-status”, event => {
    console.log(
    “Tamanna AI Sync Status:”,
    event.detail.status
    );
    });
    }