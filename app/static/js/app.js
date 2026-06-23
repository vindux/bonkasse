/* Bonkasse - Keyboard shortcuts and UI helpers */

/* On the register page a tapped button must NOT keep keyboard focus.
   Otherwise a focused <button> gets re-triggered by Space/Enter, which would
   re-add the last item. Blur it the moment it gains focus (the click itself
   still goes through). */
document.addEventListener("focusin", function (e) {
    if (!document.getElementById("register-page")) return;
    var t = e.target;
    if (t && t.tagName === "BUTTON" && typeof t.blur === "function") {
        t.blur();
    }
});

/* Register page keyboard: ONLY Enter does anything (print the bons).
   Every other key is swallowed so nothing else can affect the cart. */
document.addEventListener("keydown", function (e) {
    if (!document.getElementById("register-page")) return;

    /* Change modal handles its own keys (any key dismisses it). */
    if (document.getElementById("change-overlay")) return;

    if (e.key === "Enter") {
        e.preventDefault();
        var btn = document.getElementById("finalize-btn");
        if (btn && !btn.disabled) {
            btn.click();
        }
        return;
    }

    e.preventDefault();
});

/* Close change modal on ANY click or keypress */
function dismissChangeModal() {
    var modal = document.getElementById("modal-container");
    if (modal && modal.innerHTML.trim()) {
        modal.innerHTML = "";
    }
}

document.addEventListener("click", function (e) {
    if (document.getElementById("change-overlay")) {
        dismissChangeModal();
    } else if (e.target.classList.contains("modal-overlay")) {
        dismissChangeModal();
    }
});

document.addEventListener("keydown", function (e) {
    var modal = document.getElementById("modal-container");
    if (modal && modal.innerHTML.trim()) {
        /* Change modal: any key dismisses */
        if (document.getElementById("change-overlay")) {
            e.preventDefault();
            dismissChangeModal();
            return;
        }
        /* Other modals: only Escape */
        if (e.key === "Escape") {
            dismissChangeModal();
        }
    }
});

/* Kiosk: disable right-click context menu */
document.addEventListener("contextmenu", function (e) {
    if (document.getElementById("register-page")) {
        e.preventDefault();
    }
});

/* Auto-scroll cart to bottom when updated */
document.body.addEventListener("htmx:afterSwap", function (e) {
    if (e.detail.target.id === "cart") {
        var cart = document.getElementById("cart");
        if (cart) {
            cart.scrollTop = cart.scrollHeight;
        }
    }
});

/* Auto-dismiss toasts */
document.body.addEventListener("htmx:afterSwap", function (e) {
    var toasts = document.querySelectorAll(".toast");
    toasts.forEach(function (toast) {
        setTimeout(function () {
            toast.remove();
        }, 3500);
    });
});
