document.addEventListener("submit", (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || form.method.toLowerCase() !== "get") {
        return;
    }

    for (const field of Array.from(form.elements)) {
        if (field instanceof HTMLInputElement || field instanceof HTMLSelectElement) {
            if (field.name && field.value === "") {
                field.disabled = true;
            }
        }
    }
});
