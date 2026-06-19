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

    const similarSearchInput = document.getElementById('editSimilarDishesSearch');
    const similarSearchResults = document.getElementById('editSimilarDishesSearchResults');
    const similarAddBtn = document.getElementById('editAddSimilarDishBtn');
    const selectedSimilarDiv = document.getElementById('editSelectedSimilarDishes');
    const similarChipsContainer = document.getElementById('editSimilarDishesChips');

    let selectedSimilarDishes = [];
    let similarRowCounter = 0;
    let similarSearchTimeout = null;
    let similarSelectedIndex = -1;

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

        // Pre-populate similar dishes from page data
        selectedSimilarDishes = [];
        similarRowCounter = 0;
        similarSelectedIndex = -1;
        similarSearchInput.value = '';
        similarSearchResults.style.display = 'none';
        similarSearchResults.innerHTML = '';
        try {
            const existing = JSON.parse(pageData.dataset.similarDishes || '[]');
            existing.forEach(d => addSimilarDishRow({ id: String(d.id), name: d.name, linked: true }));
        } catch (_) {}

        formError.style.display = 'none';
    });

    // Similar dishes helpers
    function addSimilarDishRow({ id, name, linked }) {
        if (linked && selectedSimilarDishes.find(d => d.linked && d.id === id)) return;
        selectedSimilarDishes.push({ rowId: similarRowCounter++, id, name, linked });
        renderSimilarDishRows();
    }

    function renderSimilarDishRows() {
        if (selectedSimilarDishes.length === 0) {
            selectedSimilarDiv.style.display = 'none';
            similarChipsContainer.innerHTML = '';
            return;
        }
        selectedSimilarDiv.style.display = 'block';
        similarChipsContainer.innerHTML = selectedSimilarDishes.map(dish => {
            const label = dish.linked
                ? `<span class="badge bg-primary me-1">${escapeHtml(dish.name)}</span>`
                : `<span class="badge bg-secondary me-1">${escapeHtml(dish.name)} <em class="small">(new)</em></span>`;
            return `<div class="d-flex align-items-center gap-1" data-row-id="${dish.rowId}">
                ${label}
                <button type="button" class="btn-close btn-sm" data-remove-row-id="${dish.rowId}" aria-label="Remove" style="font-size:0.6rem;"></button>
            </div>`;
        }).join('');
        similarChipsContainer.querySelectorAll('[data-remove-row-id]').forEach(btn => {
            btn.addEventListener('click', function () {
                const rowId = parseInt(this.dataset.removeRowId, 10);
                selectedSimilarDishes = selectedSimilarDishes.filter(d => d.rowId !== rowId);
                renderSimilarDishRows();
            });
        });
    }

    function escapeHtml(text) {
        return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function commitSimilarInput() {
        const items = similarSearchResults.querySelectorAll('.edit-similar-result');
        if (similarSelectedIndex >= 0 && items[similarSelectedIndex]) {
            const item = items[similarSelectedIndex];
            addSimilarDishRow({ id: item.dataset.similarId, name: item.dataset.similarName, linked: true });
        } else {
            const text = similarSearchInput.value.trim();
            if (text) addSimilarDishRow({ id: null, name: text, linked: false });
        }
        similarSearchResults.style.display = 'none';
        similarSearchResults.innerHTML = '';
        similarSelectedIndex = -1;
        similarSearchInput.value = '';
    }

    function updateSimilarSelection(items) {
        items.forEach((item, i) => {
            item.classList.toggle('active', i === similarSelectedIndex);
            if (i === similarSelectedIndex) item.scrollIntoView({ block: 'nearest' });
        });
    }

    similarSearchInput.addEventListener('input', function () {
        clearTimeout(similarSearchTimeout);
        similarSelectedIndex = -1;
        const query = this.value.trim();
        if (query.length < 2) {
            similarSearchResults.style.display = 'none';
            similarSearchResults.innerHTML = '';
            return;
        }
        similarSearchTimeout = setTimeout(() => {
            const searchUrl = pageData.dataset.searchUrl;
            fetch(`${searchUrl}?q=${encodeURIComponent(query)}`)
                .then(r => r.json())
                .then(data => {
                    if (!data.results || data.results.length === 0) {
                        similarSearchResults.style.display = 'none';
                        return;
                    }
                    similarSearchResults.style.display = 'block';
                    similarSearchResults.innerHTML = data.results.map(e => `
                        <button type="button" class="list-group-item list-group-item-action edit-similar-result"
                                data-similar-id="${e.id}" data-similar-name="${escapeHtml(e.name)}">
                            <div class="d-flex w-100 justify-content-between">
                                <span>${escapeHtml(e.name)}</span>
                                ${e.cuisine_type ? `<small class="badge bg-info">${escapeHtml(e.cuisine_type)}</small>` : ''}
                            </div>
                        </button>`).join('');
                    similarSearchResults.querySelectorAll('.edit-similar-result').forEach(item => {
                        item.addEventListener('click', function () {
                            addSimilarDishRow({ id: this.dataset.similarId, name: this.dataset.similarName, linked: true });
                            similarSearchResults.style.display = 'none';
                            similarSearchResults.innerHTML = '';
                            similarSelectedIndex = -1;
                            similarSearchInput.value = '';
                        });
                    });
                })
                .catch(() => { similarSearchResults.style.display = 'none'; });
        }, 300);
    });

    similarSearchInput.addEventListener('keydown', function (e) {
        const items = similarSearchResults.querySelectorAll('.edit-similar-result');
        if (e.key === 'ArrowDown') { e.preventDefault(); similarSelectedIndex = Math.min(similarSelectedIndex + 1, items.length - 1); updateSimilarSelection(items); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); similarSelectedIndex = Math.max(similarSelectedIndex - 1, -1); updateSimilarSelection(items); }
        else if (e.key === 'Enter') { e.preventDefault(); commitSimilarInput(); }
    });

    similarAddBtn.addEventListener('click', commitSimilarInput);

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
            if (f.similar_dishes_globally) {
                const names = f.similar_dishes_globally.split(',').map(s => s.trim()).filter(Boolean);
                selectedSimilarDishes = [];
                similarRowCounter = 0;
                names.forEach(name => addSimilarDishRow({ id: null, name, linked: false }));
            }
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
        const csrfToken = getCsrfToken();

        // Resolve any typed-but-unlinked similar dishes into placeholder entries
        let resolvedSimilarIds;
        try {
            resolvedSimilarIds = await Promise.all(selectedSimilarDishes.map(async dish => {
                if (dish.linked) return dish.id;
                const r = await fetch('/api/encyclopedia/create-placeholder/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                    body: JSON.stringify({ name: dish.name })
                });
                const result = await r.json();
                if (!r.ok) throw new Error(result.error || 'Failed to create placeholder');
                return String(result.entry.id);
            }));
        } catch (err) {
            console.error('Placeholder creation error:', err);
            formError.textContent = err.message || 'Failed to create placeholder entries. Please try again.';
            formError.style.display = 'block';
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="bi bi-check-circle"></i> Save Changes';
            return;
        }

        try {
            const resp = await fetch(editUrl, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    name,
                    description,
                    cuisine_type: cuisineTypeInput.value.trim(),
                    dish_category: dishCategoryInput.value.trim(),
                    region: regionInput.value.trim(),
                    cultural_significance: culturalSignificanceInput.value.trim(),
                    popular_examples: popularExamplesInput.value.trim(),
                    history: historyInput.value.trim(),
                    similar_dishes_ids: resolvedSimilarIds.map(id => parseInt(id, 10))
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

    // Reset on close
    modalElement.addEventListener('hidden.bs.modal', function () {
        formError.style.display = 'none';
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="bi bi-check-circle"></i> Save Changes';
        aiWaitNotice.style.display = 'none';
        selectedSimilarDishes = [];
        similarRowCounter = 0;
        similarSelectedIndex = -1;
        similarSearchInput.value = '';
        similarSearchResults.style.display = 'none';
        similarSearchResults.innerHTML = '';
        selectedSimilarDiv.style.display = 'none';
        similarChipsContainer.innerHTML = '';
    });
});
