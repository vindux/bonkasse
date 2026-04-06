/* Bonkasse - Keyboard shortcuts and UI helpers */

/* Keyboard shortcuts for register page */
document.addEventListener("keydown", function (e) {
    /* Only on register page */
    if (!document.getElementById("register-page")) return;

    /* Enter = finalize (print receipt) */
    if (e.key === "Enter") {
        var btn = document.getElementById("finalize-btn");
        if (btn && !btn.disabled) {
            btn.click();
        }
    }

    /* Backspace = remove last item */
    if (e.key === "Backspace") {
        e.preventDefault();
        htmx.ajax("POST", "/cart/remove-last", { target: "#cart", swap: "innerHTML" });
    }
});

/* Close modal on click outside */
document.addEventListener("click", function (e) {
    if (e.target.classList.contains("modal-overlay")) {
        document.getElementById("modal-container").innerHTML = "";
    }
});

/* Close modal on Escape */
document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
        var modal = document.getElementById("modal-container");
        if (modal && modal.innerHTML.trim()) {
            modal.innerHTML = "";
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
