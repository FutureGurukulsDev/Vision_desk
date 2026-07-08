const socket = io();
const visitorList = document.getElementById("visitorList");
const searchInput = document.getElementById("searchInput");
const messageModal = new bootstrap.Modal(document.getElementById("messageModal"));

let visitors = [];
let activeHistory = "today";
let searchTimer = null;

const workflowActions = [
    { label: "Approve", type: "status", status: "Approved", className: "btn-success" },
    { label: "Reject", type: "status", status: "Rejected", className: "btn-danger" },
    { label: "Busy", type: "status", status: "Busy", className: "btn-warning" },
    { label: "Meeting Started", type: "status", status: "Meeting Started", className: "btn-primary" },
    { label: "Meeting Finished", type: "status", status: "Meeting Finished", className: "btn-secondary" }
];

const quickActionGroups = [
    {
        title: "Hospitality",
        actions: [
            { label: "Send Water", message: () => "Please serve water to the visitor." },
            { label: "Send Coffee", message: () => "Please serve coffee to the visitor." },
            { label: "Send Tea", message: () => "Please serve tea to the visitor." },
            { label: "Offer Refreshments", message: () => "Please offer refreshments to the visitor." }
        ]
    },
    {
        title: "Reception",
        actions: [
            { label: "Call Reception", message: () => "Please call reception immediately." },
            { label: "Call Person", message: (visitor) => `Please inform ${visitor.person_to_meet} that their visitor has arrived.` },
            { label: "Request ID Proof", message: () => "Please request and verify the visitor ID proof." },
            { label: "Collect Documents", message: () => "Please collect the required documents from the visitor." }
        ]
    },
    {
        title: "Movement",
        actions: [
            { label: "Send Visitor In", message: (visitor) => `Please send ${visitor.name} in for the meeting.` },
            { label: "Escort Visitor", message: () => "Please arrange an escort for the visitor." },
            { label: "Prepare Room", message: () => "Please prepare the meeting room for the visitor." },
            { label: "Meeting Delayed", message: () => "Please inform the visitor that the meeting is delayed." }
        ]
    },
    {
        title: "Waiting",
        actions: [
            { label: "Wait 5 Minutes", message: () => "Please ask the visitor to wait 5 minutes." },
            { label: "Wait 10 Minutes", message: () => "Please ask the visitor to wait 10 minutes." },
            { label: "Manager Unavailable", message: () => "Please inform the visitor that the manager is currently unavailable." },
            { label: "Custom Message", custom: true }
        ]
    }
];

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function showToast(title, message, tone = "primary") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = `toast align-items-center text-bg-${tone} border-0`;
    toast.role = "alert";
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body"><strong>${escapeHtml(title)}</strong><br>${escapeHtml(message)}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>`;
    container.appendChild(toast);
    const instance = new bootstrap.Toast(toast, { delay: 3800 });
    instance.show();
    toast.addEventListener("hidden.bs.toast", () => toast.remove());
}

function statusClass(status) {
    return `status-${status.replaceAll(" ", "-")}`;
}

function renderWorkflowActions() {
    return workflowActions.map((action) => `
        <button class="btn ${action.className}"
                data-action="status"
                data-status="${escapeHtml(action.status)}">
            ${escapeHtml(action.label)}
        </button>
    `).join("");
}

function renderQuickActionGroups(visitor) {
    return quickActionGroups.map((group) => `
        <div class="quick-action-group">
            <div class="quick-action-title">${escapeHtml(group.title)}</div>
            <div class="quick-action-buttons">
                ${group.actions.map((action) => {
                    if (action.custom) {
                        return `<button class="btn btn-outline-info" data-action="custom">${escapeHtml(action.label)}</button>`;
                    }

                    return `
                        <button class="btn btn-outline-light"
                                data-action="message"
                                data-message="${escapeHtml(action.message(visitor))}">
                            ${escapeHtml(action.label)}
                        </button>
                    `;
                }).join("")}
            </div>
        </div>
    `).join("");
}

function renderVisitors() {
    document.getElementById("waitingCount").textContent = visitors.filter((visitor) => visitor.status === "Waiting").length;
    document.getElementById("approvedCount").textContent = visitors.filter((visitor) => visitor.status === "Approved").length;
    document.getElementById("totalCount").textContent = visitors.length;

    if (!visitors.length) {
        visitorList.innerHTML = `<div class="empty-state">No visitors found for the selected view.</div>`;
        return;
    }

    visitorList.innerHTML = visitors.map((visitor) => `
        <article class="visitor-card" data-id="${visitor.id}">
            <div class="visitor-gallery">${(visitor.photo_paths?.length ? visitor.photo_paths : [visitor.photo_path || "/static/icons/person.svg"]).map((path,index) => `<img class="visitor-photo ${index ? "visitor-photo-small" : ""}" src="${escapeHtml(path)}" alt="${escapeHtml(visitor.name)} photo ${index+1}">`).join("")}</div>
            <div class="visitor-meta">
                <h3>${escapeHtml(visitor.name)}</h3>
                <p><strong>${escapeHtml(visitor.company)}</strong> visiting <strong>${escapeHtml(visitor.person_to_meet)}</strong></p>
                <p>${escapeHtml(visitor.purpose)}</p>
                <p>Arrival: ${escapeHtml(visitor.arrival_display)}</p>
                <span class="badge-status ${statusClass(visitor.status)}">${escapeHtml(visitor.status)}</span>
                <div class="action-section">
                    <div class="quick-action-title">Workflow</div>
                    <div class="visitor-actions workflow-actions">
                        ${renderWorkflowActions()}
                    </div>
                </div>
                <div class="quick-actions-panel">
                    ${renderQuickActionGroups(visitor)}
                </div>
            </div>
        </article>
    `).join("");
}

async function loadVisitors() {
    const params = new URLSearchParams({
        history: activeHistory,
        search: searchInput.value.trim()
    });
    const response = await fetch(`/api/visitors?${params.toString()}`);
    const data = await response.json();
    visitors = data.visitors || [];
    renderVisitors();
}

async function updateStatus(visitorId, status, message = status) {
    const response = await fetch(`/api/visitors/${visitorId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status, message })
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Unable to update status.");
    }
    showToast("Visitor Updated", `${data.visitor.name}: ${data.visitor.status}`, "success");
}

async function sendMessage(visitorId, message) {
    const response = await fetch("/api/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ visitor_id: visitorId, message })
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Unable to send message.");
    }
    showToast("Message Sent", message, "info");
}

socket.on("connect", () => {
    socket.emit("join_role", { role: "manager" });
});

socket.on("visitor_registered", ({ visitor }) => {
    visitors.unshift(visitor);
    renderVisitors();
    showToast("New Visitor", `${visitor.name} from ${visitor.company}`, "primary");
});

socket.on("visitor_status_updated", ({ visitor }) => {
    visitors = visitors.map((item) => item.id === visitor.id ? visitor : item);
    renderVisitors();
});

visitorList.addEventListener("click", async (event) => {
    const button = event.target.closest("button");
    if (!button) {
        return;
    }

    const card = event.target.closest(".visitor-card");
    const visitorId = Number(card.dataset.id);
    const action = button.dataset.action;

    try {
        if (action === "status") {
            await updateStatus(visitorId, button.dataset.status);
        } else if (action === "message") {
            await sendMessage(visitorId, button.dataset.message);
        } else if (action === "custom") {
            document.getElementById("messageVisitorId").value = visitorId;
            document.getElementById("customMessage").value = "";
            messageModal.show();
        }
    } catch (error) {
        showToast("Action Failed", error.message, "danger");
    }
});

document.getElementById("sendCustomMessage").addEventListener("click", async () => {
    const visitorId = Number(document.getElementById("messageVisitorId").value);
    const message = document.getElementById("customMessage").value.trim();
    if (!message) {
        showToast("Message Required", "Please type a message before sending.", "warning");
        return;
    }

    try {
        await sendMessage(visitorId, message);
        messageModal.hide();
    } catch (error) {
        showToast("Action Failed", error.message, "danger");
    }
});

document.querySelectorAll(".nav-pill").forEach((button) => {
    button.addEventListener("click", () => {
        document.querySelectorAll(".nav-pill").forEach((item) => item.classList.remove("active"));
        button.classList.add("active");
        activeHistory = button.dataset.history;
        loadVisitors();
    });
});

searchInput.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadVisitors, 250);
});

loadVisitors();
