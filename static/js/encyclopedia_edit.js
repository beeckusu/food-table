document.addEventListener('DOMContentLoaded', function () {
    const modalElement = document.getElementById('encyclopediaEditModal');
    if (!modalElement) return;

    const pageData = document.getElementById('encyclopediaPageData');
    if (!pageData) return;

    const entryId = pageData.dataset.entryId;
    const entryName = pageData.dataset.entryName;

    const modal = new bootstrap.Modal(modalElement);

    const nameInput = document.getElementById('editEntryName');
    const descriptionInput = document.getElementById('editEntryDescription');
    const cuisineTypeInput = document.getElementById('editEntryCuisineType');
    const dishCategoryInput = document.getElementById('editEntryDishCategory');
    const regionInput = document.getElementById('editEntryRegion');
    const culturalSignificanceInput = document.getElementById('editEntryCulturalSignificance');
    const popularExamplesInput = document.getElementById('editEntryPopularExamples');
    const historyInput = document.getElementById('editEntryHistory');
    const formError = document.getElementById('editFormError');
    const saveBtn = document.getElementById('saveEditBtn');
    const aiPrefillBtn = document.getElementById('editAiPrefillBtn');
    const aiWaitNotice = document.getElementById('editAiWaitNotice');

    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
               document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
    }

    // Pre-populate fields from the page when modal opens
    modalElement.addEventListener('show.bs.modal', function () {
        // Read current values from the rendered page
        const h1 = document.querySelector('h1.mb-0');
        if (h1) nameInput.value = h1.textContent.trim();

        // Description: read from the rendered card-text, strip HTML tags
        const descEl = document.querySelector('.card-body .card-text');
        if (descEl) descriptionInput.value = descEl.innerText.trim();

        // Classification badges
        const badges = document.querySelectorAll('.badge');
        cuisineTypeInput.value = '';
        dishCategoryInput.value = '';
        regionInput.value = '';
        badges.forEach(badge => {
            if (badge.classList.contains('bg-secondary') && !cuisineTypeInput.value) {
                cuisineTypeInput.value = badge.textContent.trim();
            } else if (badge.classList.contains('bg-info') && !dishCategoryInput.value) {
                dishCategoryInput.value = badge.textContent.trim();
            } else if (badge.classList.contains('bg-success') && !regionInput.value) {
                regionInput.value = badge.textContent.trim();
            }
        });

        // Long-form fields: read from their respective cards
        culturalSignificanceInput.value = '';
        popularExamplesInput.value = '';
        historyInput.value = '';

        document.querySelectorAll('.card-body').forEach(cardBody => {
            const title = cardBody.querySelector('.card-title');
            const text = cardBody.querySelector('.card-text');
            if (!title || !text) return;
            const label = title.textContent.trim();
            if (label === 'Cultural Significance') culturalSignificanceInput.value = text.innerText.trim();
            if (label === 'Popular Examples') popularExamplesInput.value = text.innerText.trim();
            if (label === 'History') historyInput.value = text.innerText.trim();
        });

        formError.style.display = 'none';
    });

    // AI prefill
    aiPrefillBtn.addEventListener('click', async function () {
        const dishName = nameInput.value.trim() || entryName;
        if (!dishName) return;

        aiPrefillBtn.disabled = true;
        aiPrefillBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Asking Claude...';
        aiWaitNotice.style.display = 'block';
        formError.style.display = 'none';

        const prefillUrl = modalElement.dataset.aiPrefillUrl;
        const csrfToken = getCsrfToken();

        try {
            const resp = await fetch(prefillUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ dish_name: dishName })
            });
            const data = await resp.json();

            if (!resp.ok || !data.success) {
                formError.textContent = data.error || 'AI prefill failed. Please try again.';
                formError.style.display = 'block';
                return;
            }

            const f = data.fields;
            if (f.name) nameInput.value = f.name;
            if (f.description) descriptionInput.value = f.description;
            if (f.cuisine_type) cuisineTypeInput.value = f.cuisine_type;
            if (f.dish_category) dishCategoryInput.value = f.dish_category;
            if (f.region) regionInput.value = f.region;
            if (f.cultural_significance) culturalSignificanceInput.value = f.cultural_significance;
            if (f.popular_examples) popularExamplesInput.value = f.popular_examples;
            if (f.history) historyInput.value = f.history;
        } catch (err) {
            console.error('AI prefill error:', err);
            formError.textContent = 'AI prefill failed. Please try again.';
            formError.style.display = 'block';
        } finally {
            aiPrefillBtn.disabled = false;
            aiPrefillBtn.innerHTML = '<i class="bi bi-stars"></i> Fill with Claude';
            aiWaitNotice.style.display = 'none';
        }
    });

    // Save changes
    saveBtn.addEventListener('click', async function () {
        const name = nameInput.value.trim();
        const description = descriptionInput.value.trim();

        if (!name || !description) {
            formError.textContent = 'Name and Description are required.';
            formError.style.display = 'block';
            return;
        }

        formError.style.display = 'none';
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving...';

        const baseUrl = modalElement.dataset.editUrl;
        const editUrl = baseUrl.replace('/0/', `/${entryId}/`);

        try {
            const resp = await fetch(editUrl, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    name,
                    description,
                    cuisine_type: cuisineTypeInput.value.trim(),
                    dish_category: dishCategoryInput.value.trim(),
                    region: regionInput.value.trim(),
                    cultural_significance: culturalSignificanceInput.value.trim(),
                    popular_examples: popularExamplesInput.value.trim(),
                    history: historyInput.value.trim()
                })
            });

            const data = await resp.json();

            if (resp.ok && data.success) {
                window.location.reload();
            } else {
                formError.textContent = data.error || 'Failed to save changes.';
                formError.style.display = 'block';
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="bi bi-check-circle"></i> Save Changes';
            }
        } catch (err) {
            console.error('Save error:', err);
            formError.textContent = 'An error occurred. Please try again.';
            formError.style.display = 'block';
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="bi bi-check-circle"></i> Save Changes';
        }
    });

    // Reset error on close
    modalElement.addEventListener('hidden.bs.modal', function () {
        formError.style.display = 'none';
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="bi bi-check-circle"></i> Save Changes';
        aiWaitNotice.style.display = 'none';
    });
});
