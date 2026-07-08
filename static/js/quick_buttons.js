let socket;
try {
    socket = io();
} catch (e) {
    console.warn("Socket.IO not available:", e.message);
}

const grid = document.getElementById("quickButtonGrid");
const customPanel = document.getElementById("customPanel");
const addPanel = document.getElementById("addPanel");
const oneOffMessageInput = document.getElementById("oneOffMessage");
const quickScrollUpButton = document.getElementById("quickScrollUp");
const quickScrollDownButton = document.getElementById("quickScrollDown");
let touchStartY = 0;
let touchScrollStart = 0;
let isTouchDragging = false;

const STATUS_ACTIONS = {
    "Approve": "Approved",
    "Reject": "Rejected",
    "Busy": "Busy",
    "Meeting Started": "Meeting Started",
    "Meeting Finished": "Meeting Finished"
};

function esc(str) {
    return String(str ?? "").replace(/[&<>"']/g, c => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[c]);
}

/* =====================================================
    Bootstrap Icons for every quick button
===================================================== */

const ICONS = {
    "Approve": "bi-check-circle-fill",
    "Reject": "bi-x-circle-fill",
    "Busy": "bi-person-fill-lock",
    "Meeting Started": "bi-play-circle-fill",
    "Meeting Finished": "bi-stop-circle-fill",
    "Wait 5 Minutes": "bi-clock-history",
    "Wait 10 Minutes": "bi-alarm",
    "Send Water": "bi-droplet-fill",
    "Send Coffee": "bi-cup-hot-fill",
    "Send Tea": "bi-cup-straw",
    "Offer Refreshments": "bi-emoji-smile-fill",
    "Call Reception": "bi-telephone-fill",
    "Call Person": "bi-telephone-forward-fill",
    "Request ID Proof": "bi-person-vcard-fill",
    "Collect Documents": "bi-file-earmark-text-fill",
    "Send Visitor In": "bi-box-arrow-in-right",
    "Escort Visitor": "bi-person-walking",
    "Prepare Room": "bi-door-open-fill",
    "Meeting Delayed": "bi-hourglass-split",
    "Manager Unavailable": "bi-slash-circle-fill",
    "Custom Message": "bi-chat-dots-fill"
};

function getIcon(label) {

    return ICONS[label] || "bi-lightning-charge-fill";

}

function syncQuickScroll() {
    const controls = document.querySelector(".quick-scroll-controls");
    if (!controls || !grid) return;

    const canScroll = grid.scrollHeight > grid.clientHeight + 1;
    controls.classList.toggle("is-visible", canScroll);

    if (quickScrollUpButton) {
        quickScrollUpButton.disabled = grid.scrollTop <= 2;
    }

    if (quickScrollDownButton) {
        quickScrollDownButton.disabled = grid.scrollTop + grid.clientHeight >= grid.scrollHeight - 2;
    }
}

function scrollGridBy(distance) {
    grid.scrollBy({ top: distance, behavior: "smooth" });
}

/* =====================================================
    Toast
===================================================== */

function toast(title, message, tone = "primary") {

    const container = document.getElementById("toastContainer");

    const toastElement = document.createElement("div");

    toastElement.className = `toast text-bg-${tone} border-0`;

    toastElement.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <strong>${esc(title)}</strong><br>
                ${esc(message)}
            </div>
            <button class="btn-close btn-close-white me-2 m-auto"
                    data-bs-dismiss="toast"></button>
        </div>
    `;

    container.appendChild(toastElement);

    new bootstrap.Toast(toastElement, {
        delay: 3500
    }).show();

    toastElement.addEventListener("hidden.bs.toast", () => {

        toastElement.remove();

    });

}

/* =====================================================
    Load Buttons
===================================================== */

async function load() {

    const buttons = await fetch("/api/quick-buttons").then(r => r.json());

    grid.innerHTML = buttons.buttons.map(button => {

        return `
<div class="quick-button-item">

    <button
        class="quick-send"
        data-label="${esc(button.label)}"
        data-message="${esc(button.message)}"
        title="${esc(button.message)}">

        <div class="quick-icon">
            <i class="bi ${getIcon(button.label)}"></i>
        </div>

        <div class="quick-text">
            <strong>${esc(button.label)}</strong>
            <small>Tap to send</small>
        </div>

    </button>

    <button
        class="quick-delete"
        type="button"
        data-delete="${button.id}"
        data-builtin="${button.is_custom ? "false" : "true"}"
        title="Delete">
        <i class="bi bi-x"></i>
    </button>

</div>
`;

    }).join("") + `
<div class="quick-button-item">
    <button id="quickAddButton" class="quick-send quick-add-card" type="button" data-add-button="true">
        <div class="quick-icon add-icon">
            <i class="bi bi-plus-circle-fill"></i>
        </div>
        <div class="quick-text">
            <strong>Add Button</strong>
            <small>Create a reusable quick button</small>
        </div>
    </button>
</div>
`;

    requestAnimationFrame(syncQuickScroll);

}

/* =====================================================
    Send Message
===================================================== */

async function send(message) {

    const response = await fetch("/api/messages", {

        method: "POST",

        headers: {

            "Content-Type": "application/json"

        },

        body: JSON.stringify({

            visitor_id: null,

            message

        })

    });

    const data = await response.json();

    if (!response.ok)

        throw new Error(data.error);

    toast("Instruction Sent", message, "success");

}

async function updateStatus(visitorId, status) {
    const response = await fetch(`/api/visitors/${visitorId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status, message: `${status} action sent by manager.` })
    });
    const data = await response.json();
    if (!response.ok)
        throw new Error(data.error);
    toast("Status Updated", status, "success");
}

/* =====================================================
    Grid Clicks
===================================================== */

grid.onclick = async (event) => {

    const deleteButton = event.target.closest("[data-delete]");

    const quickButton = event.target.closest(".quick-send");

    try {

        if (deleteButton) {

            const isBuiltin = deleteButton.dataset.builtin === "true";
            if (isBuiltin) {
                if (!confirm('This is a built-in button. Do you want to delete it? This will hide the built-in button permanently unless restored.')) {
                    return;
                }
            } else {
                if (!confirm('Delete this quick button?')) return;
            }

            const response = await fetch(`/api/quick-buttons/${deleteButton.dataset.delete}`,
                {
                    method: "DELETE",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ force: isBuiltin })
                }
            );

            const data = await response.json();

            if (!response.ok)
                throw new Error(data.error);

            toast("Deleted", "Quick button removed.", "warning");
            load();
            return;

        }

        const addCard = event.target.closest("[data-add-button]");
        if (addCard) {
            addPanel.classList.remove("d-none");
            customPanel.classList.add("d-none");
            document.getElementById("buttonLabel").focus();
            return;
        }

        if (!quickButton) {
            return;
        }

        const label = quickButton.dataset.label;

        if (label === "Custom Message") {
            addPanel.classList.add("d-none");
            customPanel.classList.toggle("d-none");
            if (!customPanel.classList.contains("d-none")) {
                oneOffMessageInput.focus();
            }
            return;
        }

        if (STATUS_ACTIONS[label]) {
            quickButton.classList.add("sent");
            await send(STATUS_ACTIONS[label]);
            setTimeout(() => {
                quickButton.classList.remove("sent");
            }, 600);
            return;
        }

        quickButton.classList.add("sent");

        await send(quickButton.dataset.message);

        setTimeout(() => {

            quickButton.classList.remove("sent");

        }, 600);

    }

    catch (err) {

        toast(

            "Error",

            err.message,

            "danger"

        );

    }

};

if (quickScrollUpButton) {
    quickScrollUpButton.addEventListener("click", () => scrollGridBy(-220));
}

if (quickScrollDownButton) {
    quickScrollDownButton.addEventListener("click", () => scrollGridBy(220));
}

grid.addEventListener("scroll", syncQuickScroll, { passive: true });
window.addEventListener("resize", syncQuickScroll);

grid.addEventListener("touchstart", (event) => {
    if (event.touches.length !== 1) return;
    touchStartY = event.touches[0].clientY;
    touchScrollStart = grid.scrollTop;
    isTouchDragging = true;
}, { passive: true });

grid.addEventListener("touchmove", (event) => {
    if (!isTouchDragging || event.touches.length !== 1) return;
    const delta = event.touches[0].clientY - touchStartY;
    grid.scrollTop = touchScrollStart - delta;
    event.preventDefault();
}, { passive: false });

grid.addEventListener("touchend", () => {
    isTouchDragging = false;
});
grid.addEventListener("touchcancel", () => {
    isTouchDragging = false;
});

// Right-click to delete custom quick buttons (context menu)
grid.addEventListener('contextmenu', async (event) => {
    event.preventDefault();
    const item = event.target.closest('.quick-button-item');
    if (!item) return;
    const del = item.querySelector('[data-delete]');
    if (!del) {
        toast('Protected', 'Built-in buttons cannot be deleted.', 'warning');
        return;
    }
    if (!confirm('Delete this quick button?')) return;
    try {
        const resp = await fetch(`/api/quick-buttons/${del.dataset.delete}`, { method: 'DELETE' });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.error);
        toast('Deleted', 'Quick button removed.', 'warning');
        load();
    } catch (err) {
        toast('Error', err.message, 'danger');
    }
});

/* =====================================================
    Add Button Panel
===================================================== */

document.getElementById("cancelCustom").onclick = () => {
    customPanel.classList.add("d-none");
};
document.getElementById("cancelAdd").onclick = () => {

    addPanel.classList.add("d-none");

};

document.getElementById("addButton").onclick = async () => {

    const label = document.getElementById("buttonLabel").value.trim();

    const message = document.getElementById("buttonMessage").value.trim();

    const response = await fetch("/api/quick-buttons", {

        method: "POST",

        headers: {

            "Content-Type": "application/json"

        },

        body: JSON.stringify({

            label,

            message

        })

    });

    const data = await response.json();

    if (!response.ok) {

        toast(

            "Failed",

            data.error,

            "danger"

        );

        return;

    }

    document.getElementById("buttonLabel").value = "";

    document.getElementById("buttonMessage").value = "";

    addPanel.classList.add("d-none");

    toast(

        "Created",

        label,

        "success"

    );

    load();

};

/* =====================================================
    Custom Message
===================================================== */

document.getElementById("sendOneOff").onclick = async () => {

    const input = document.getElementById("oneOffMessage");

    const message = input.value.trim();

    if (!message) {

        toast(

            "Message Required",

            "Please type a message.",

            "warning"

        );

        return;

    }

    try {

        await send(message);

        input.value = "";

    }

    catch (err) {

        toast(

            "Failed",

            err.message,

            "danger"

        );

    }

};

document.getElementById("oneOffMessage").addEventListener("keydown", e => {

    if (e.key === "Enter") {

        e.preventDefault();

        document.getElementById("sendOneOff").click();

    }

});

/* =====================================================
    Socket.IO
===================================================== */

if (socket) {
    socket.on("connect", () => {

        socket.emit("join_role", {

            role: "manager"

        });

    });

    socket.on("visitor_registered", ({ visitor }) => {

        toast(

            "New Visitor",

            `${visitor.name} has registered.`,

            "info"

        );

        load();

    });
}

/* =====================================================
    Initialize Page
===================================================== */

load();

load();