// Shared "Fill with Claude" wiring for encyclopedia entry forms.
// Used by encyclopedia_link.js, encyclopedia_edit.js, and review_dish_link.js.
function wireEncyclopediaAiPrefill(options) {
    const { button, waitNotice, errorEl, getDishName, setField, prefillUrl } = options;
    if (!button) return;

    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
               document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
    }

    button.addEventListener('click', async function () {
        const dishName = getDishName();
        if (!dishName) {
            if (errorEl) {
                errorEl.textContent = 'No dish name set — please close and reopen the modal.';
                errorEl.style.display = 'block';
            }
            return;
        }

        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Asking Claude...';
        if (waitNotice) waitNotice.style.display = 'block';
        if (errorEl) errorEl.style.display = 'none';

        try {
            const resp = await fetch(prefillUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
                body: JSON.stringify({ dish_name: dishName })
            });
            const data = await resp.json();

            if (!resp.ok || !data.success) {
                if (errorEl) {
                    errorEl.textContent = data.error || 'AI prefill failed. Please try again.';
                    errorEl.style.display = 'block';
                }
                return;
            }

            Object.entries(data.fields || {}).forEach(([key, value]) => {
                if (value && setField[key]) setField[key](value);
            });
        } catch (err) {
            console.error('AI prefill error:', err);
            if (errorEl) {
                errorEl.textContent = 'AI prefill failed. Please try again.';
                errorEl.style.display = 'block';
            }
        } finally {
            button.disabled = false;
            button.innerHTML = '<i class="bi bi-stars"></i> Fill with Claude';
            if (waitNotice) waitNotice.style.display = 'none';
        }
    });
}
