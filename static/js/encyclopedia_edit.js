// Encyclopedia Edit Modal JavaScript
// Also handles converting placeholder entries -- a placeholder is just an entry that
// hasn't had a description added yet, and the edit API already flips is_placeholder
// to false the moment a description is saved. So "edit" and "convert" are the same
// flow, just possibly targeting a different entry than the one whose page you're on
// (e.g. clicking a placeholder referenced in another entry's Similar Dishes list).
document.addEventListener('DOMContentLoaded', function () {
    const modalElement = document.getElementById('encyclopediaEditModal');
    if (!modalElement) return;

    const pageData = document.getElementById('encyclopediaPageData');
    if (!pageData) return;

    const modal = new bootstrap.Modal(modalElement);

    const placeholderNotice = document.getElementById('editPlaceholderNotice');
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

    const similarDishesController = createSimilarDishesController({
        prefix: 'editEntry',
        searchUrl: modalElement.dataset.searchUrl
    });

    let editFormQuills = null;
    function initEditFormQuills() {
        if (editFormQuills) return;
        editFormQuills = {
            description: initQuillEditor(
                document.getElementById('editEntryDescriptionEditor'),
                descriptionInput,
                { placeholder: 'Provide a detailed description of this dish...' }
            ),
            culturalSignificance: initQuillEditor(
                document.getElementById('editEntryCulturalSignificanceEditor'),
                culturalSignificanceInput,
                { placeholder: 'Describe the cultural importance or traditions...' }
            ),
            popularExamples: initQuillEditor(
                document.getElementById('editEntryPopularExamplesEditor'),
                popularExamplesInput,
                { placeholder: 'List well-known examples or variations...' }
            ),
            history: initQuillEditor(
                document.getElementById('editEntryHistoryEditor'),
                historyInput,
                { placeholder: 'Describe the historical background...' }
            )
        };
    }

    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
               document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
    }

    function editUrlFor(entryId) {
        return modalElement.dataset.editUrl.replace('/0/', `/${entryId}/`);
    }

    // The entry to edit. Defaults to the current page's own entry when the modal is
    // opened via the standard "Edit" button (Bootstrap's own data-bs-toggle, no JS call
    // involved) -- openEditModal() overrides this when opened from elsewhere, e.g. a
    // placeholder referenced in this page's Similar Dishes list.
    let targetEntryId = null;

    function openEditModal(entryId) {
        targetEntryId = entryId;
        modal.show();
    }

    modalElement.addEventListener('show.bs.modal', async function () {
        if (targetEntryId === null) {
            targetEntryId = pageData.dataset.entryId;
        }

        initEditFormQuills();
        formError.style.display = 'none';
        placeholderNotice.style.display = 'none';
        similarDishesController.reset();

        try {
            const resp = await fetch(editUrlFor(targetEntryId));
            const data = await resp.json();

            if (!resp.ok || !data.success) {
                formError.textContent = data.error || 'Failed to load entry.';
                formError.style.display = 'block';
                return;
            }

            const entry = data.entry;
            nameInput.value = entry.name;
            cuisineTypeInput.value = entry.cuisine_type;
            dishCategoryInput.value = entry.dish_category;
            regionInput.value = entry.region;
            setQuillContentFromRtf(editFormQuills.description, entry.description);
            setQuillContentFromRtf(editFormQuills.culturalSignificance, entry.cultural_significance);
            setQuillContentFromRtf(editFormQuills.popularExamples, entry.popular_examples);
            setQuillContentFromRtf(editFormQuills.history, entry.history);

            entry.similar_dishes.forEach(d => similarDishesController.addRow({ id: String(d.id), name: d.name, linked: true }));

            placeholderNotice.style.display = entry.is_placeholder ? 'block' : 'none';
        } catch (err) {
            console.error('Failed to load entry:', err);
            formError.textContent = 'Failed to load entry. Please try again.';
            formError.style.display = 'block';
        }
    });

    // AI prefill
    wireEncyclopediaAiPrefill({
        button: aiPrefillBtn,
        waitNotice: aiWaitNotice,
        errorEl: formError,
        prefillUrl: modalElement.dataset.aiPrefillUrl,
        getDishName: () => nameInput.value.trim(),
        setField: {
            name: (v) => { nameInput.value = v; },
            description: (v) => setQuillContentFromRtf(editFormQuills.description, v),
            cuisine_type: (v) => { cuisineTypeInput.value = v; },
            dish_category: (v) => { dishCategoryInput.value = v; },
            region: (v) => { regionInput.value = v; },
            cultural_significance: (v) => setQuillContentFromRtf(editFormQuills.culturalSignificance, v),
            popular_examples: (v) => setQuillContentFromRtf(editFormQuills.popularExamples, v),
            history: (v) => setQuillContentFromRtf(editFormQuills.history, v),
            similar_dishes_globally: async (v) => {
                similarDishesController.reset();
                const names = v.split(',').map(s => s.trim()).filter(Boolean);
                const rows = await Promise.all(names.map(name => similarDishesController.resolveExactMatch(name)));
                rows.forEach(row => similarDishesController.addRow(row));
            }
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

        const csrfToken = getCsrfToken();

        let resolvedSimilarIds;
        try {
            resolvedSimilarIds = await similarDishesController.resolveIds(csrfToken);
        } catch (err) {
            console.error('Placeholder creation error:', err);
            formError.textContent = err.message || 'Failed to create placeholder entries. Please try again.';
            formError.style.display = 'block';
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="bi bi-check-circle"></i> Save Changes';
            return;
        }

        try {
            const resp = await fetch(editUrlFor(targetEntryId), {
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
        targetEntryId = null;
        formError.style.display = 'none';
        placeholderNotice.style.display = 'none';
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="bi bi-check-circle"></i> Save Changes';
        aiWaitNotice.style.display = 'none';
        similarDishesController.reset();
    });

    // Clicking a placeholder referenced elsewhere on this page (e.g. in Similar Dishes)
    // opens this same modal targeting that placeholder instead of the page's own entry.
    document.querySelectorAll('.encyclopedia-placeholder').forEach(element => {
        element.addEventListener('click', function (e) {
            e.preventDefault();
            openEditModal(this.dataset.placeholderId);
        });
    });
});
