const socket = io(), form = document.getElementById("visitorForm"), video = document.getElementById("cameraVideo"), canvas = document.getElementById("cameraCanvas"), preview = document.getElementById("cameraPreview"), toggle = document.getElementById("cameraToggleButton"), capture = document.getElementById("captureButton"), strip = document.getElementById("photoStrip");
let stream = null, piMode = false, photos = [], activeVisitorId = null; const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
function toast(title, message, tone = "primary") { const c = document.getElementById("toastContainer"), t = document.createElement("div"); t.className = `toast text-bg-${tone} border-0`; t.innerHTML = `<div class="d-flex"><div class="toast-body"><strong>${esc(title)}</strong><br>${esc(message)}</div><button class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>`; c.appendChild(t); new bootstrap.Toast(t, { delay: 4500 }).show(); t.addEventListener("hidden.bs.toast", () => t.remove()) }
function renderPhotos() { strip.innerHTML = photos.map((p, i) => `<div class="photo-thumb"><img src="${esc(p)}"><button type="button" data-remove="${i}" aria-label="Remove photo">&times;</button></div>`).join("") }
async function uploadBlob(blob) { const fd = new FormData(); fd.append("photo", blob, "capture.jpg"); const r = await fetch("/api/camera/upload", { method: "POST", body: fd }), d = await r.json(); if (!r.ok) throw Error(d.error); photos.push(d.photo_path); renderPhotos(); toast("Photo saved", `Photo ${photos.length} added.`, "success") }
function getLocalCameraUrl() {
    const hostname = window.location.hostname;
    if (["localhost", "127.0.0.1", "::1", "0.0.0.0"].includes(hostname)) return null;
    const port = window.location.port || "5000";
    const path = `${window.location.pathname}${window.location.search}`;
    return `${window.location.protocol}//127.0.0.1:${port}${path}`;
}

function redirectToLocalCameraView() {
    const target = getLocalCameraUrl();
    if (!target || target === window.location.href) return false;
    window.location.replace(target);
    return true;
}

async function cameraOn() {
    const r = await fetch("/api/camera/start", { method: "POST" });
    const d = await r.json();
    if (!r.ok) throw Error(d.error || "Unable to start camera.");

    piMode = Boolean(d.hardware_started);
    if (piMode) {
        preview.classList.add("camera-on");
        document.getElementById("cameraPlaceholder").style.display = "block";
        document.getElementById("cameraStateText").textContent = "Pi camera ready";
        toggle.textContent = "Turn Camera Off";
        capture.disabled = false;
        return;
    }

    if (!window.isSecureContext && !["localhost", "127.0.0.1", "::1"].includes(window.location.hostname)) {
        if (redirectToLocalCameraView()) {
            return;
        }
        throw Error("Camera access needs a secure local connection. Please open this page on localhost or use the image picker.");
    }

    if (!navigator.mediaDevices?.getUserMedia) {
        throw Error("Camera access is unavailable in this browser. Please use the image picker instead.");
    }

    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false });
    } catch (error) {
        if (error.name === "NotAllowedError" || error.name === "PermissionDeniedError") {
            throw Error("Camera permission was denied. Please allow camera access for this page.");
        }
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        } catch (fallbackError) {
            throw Error("Camera access failed. Please use the image picker instead.");
        }
    }

    video.srcObject = stream;
    video.style.display = "block";
    video.playsInline = true;
    video.muted = true;
    video.autoplay = true;
    await video.play().catch(() => {});

    preview.classList.add("camera-on");
    document.getElementById("cameraPlaceholder").style.display = "none";
    document.getElementById("cameraStateText").textContent = "Device camera ready";
    toggle.textContent = "Turn Camera Off";
    capture.disabled = false;
}
async function cameraOff() { stream?.getTracks().forEach(t => t.stop()); stream = null; video.srcObject = null; video.style.display = "none"; await fetch("/api/camera/stop", { method: "POST" }); preview.classList.remove("camera-on"); document.getElementById("cameraPlaceholder").style.display = "block"; document.getElementById("cameraStateText").textContent = "Tap Turn Camera On"; toggle.textContent = "Turn Camera On"; capture.disabled = true }
toggle.onclick = async () => { toggle.disabled = true; try { stream || piMode ? await cameraOff() : await cameraOn() } catch (e) { toast("Camera unavailable", e.message, "danger") } finally { toggle.disabled = false } };
capture.onclick = async () => {
    capture.disabled = true;
    try {
        if (piMode) {
            const r = await fetch("/api/camera/capture", { method: "POST" }), d = await r.json();
            if (!r.ok) throw Error(d.error);
            photos.push(d.photo_path);
            renderPhotos();
        } else {
            const width = video.videoWidth || 1280;
            const height = video.videoHeight || 720;
            canvas.width = width;
            canvas.height = height;
            canvas.getContext("2d").drawImage(video, 0, 0, width, height);
            await new Promise((resolve, reject) => canvas.toBlob(
                b => b ? uploadBlob(b).then(resolve, reject) : reject(Error("Could not capture photo.")),
                "image/jpeg",
                .92
            ));
        }
        toast("Photo captured", `Photo ${photos.length} is ready.`, "success");
    } catch (e) {
        toast("Capture failed", e.message, "danger");
    } finally {
        capture.disabled = false;
    }
};
document.getElementById("devicePhoto").onchange = async e => { for (const file of e.target.files) { try { await uploadBlob(file) } catch (x) { toast("Upload failed", x.message, "danger") } } e.target.value = "" }; strip.onclick = e => { const b = e.target.closest("[data-remove]"); if (b) { photos.splice(Number(b.dataset.remove), 1); renderPhotos() } };
function firstMissing() { return [...form.querySelectorAll("[required]")].find(x => !x.value.trim()) } form.onsubmit = async e => { e.preventDefault(); const missing = firstMissing(); if (missing) { missing.focus(); missing.classList.add("is-invalid"); return toast("Missing information", `Please fill in ${missing.previousElementSibling?.textContent || missing.name}.`, "warning") } form.querySelectorAll(".is-invalid").forEach(x => x.classList.remove("is-invalid")); const payload = Object.fromEntries(new FormData(form)); payload.photo_paths = photos; try { const r = await fetch("/api/visitors", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }), d = await r.json(); if (!r.ok) throw Error(d.error); activeVisitorId = d.visitor.id; socket.emit("join_visitor", { visitor_id: activeVisitorId }); document.getElementById("statusTitle").textContent = "Registration Successful"; document.getElementById("statusMessage").textContent = "Saved locally and sent to the manager."; document.getElementById("savedRegistration").classList.remove("d-none"); document.getElementById("savedRegistrationDetails").innerHTML = `<strong>${esc(d.visitor.name)}</strong> — ${esc(d.visitor.company)}<br>${d.visitor.photo_paths.length} photo(s) saved`; toast("Registration successful", `${d.visitor.name} is now in the manager queue.`, "success"); form.reset(); photos = []; renderPhotos(); await cameraOff() } catch (x) { toast("Registration failed", x.message, "danger") } };
socket.on("connect", () => socket.emit("join_role", { role: "reception" })); socket.on("visitor_status_updated", ({ visitor, message }) => { if (activeVisitorId && visitor.id !== activeVisitorId) return; document.getElementById("statusTitle").textContent = visitor.status; document.getElementById("managerMessage").textContent = message?.message || ""; toast("Manager update", message?.message || visitor.status, visitor.status === "Rejected" ? "danger" : "success") }); socket.on("reception_message", ({ message }) => { document.getElementById("managerMessage").textContent = message.message; toast("Manager message", message.message, "info") });
function clock() { const n = new Date(); document.getElementById("currentDate").textContent = n.toLocaleDateString(undefined, { weekday: "long", year: "numeric", month: "long", day: "numeric" }); document.getElementById("currentTime").textContent = n.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" }) } clock(); setInterval(clock, 1000);