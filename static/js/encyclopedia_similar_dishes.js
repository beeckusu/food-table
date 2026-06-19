// Shared "Similar Dishes Globally" controller for encyclopedia entry forms.
// Used by the Create/Link modal (encyclopedia_link.js, review_dish_link.js) and the
// Edit modal (encyclopedia_edit.js). Chips can be "linked" (an existing entry) or
// "new placeholder" (not yet a real entry) — unlinked chips get an inline "Link existing"
// toggle so a mistakenly-unlinked row can be retroactively linked without removing it.
function createSimilarDishesController(options) {
    const prefix = options.prefix;
    const searchUrl = options.searchUrl;

    const searchInput = document.getElementById(prefix + 'SimilarDishesSearch');
    const searchResults = document.getElementById(prefix + 'SimilarDishesSearchResults');
    const addBtn = document.getElementById(prefix + 'AddSimilarDishBtn');
    const selectedDiv = document.getElementById(prefix + 'SelectedSimilarDishes');
    const chipsContainer = document.getElementById(prefix + 'SimilarDishesChips');

    let selectedDishes = []; // Array of {rowId, id, name, linked}
    let rowCounter = 0;
    let selectedIndex = -1;
    let searchTimeout = null;

    function reset() {
        selectedDishes = [];
        rowCounter = 0;
        selectedIndex = -1;
        if (searchInput) searchInput.value = '';
        if (searchResults) {
            searchResults.style.display = 'none';
            searchResults.innerHTML = '';
        }
        renderRows();
    }

    function addRow({ id, name, linked }) {
        if (linked && selectedDishes.find(d => d.linked && d.id === id)) return;
        selectedDishes.push({ rowId: rowCounter++, id, name, linked });
        renderRows();
    }

    function getSelected() {
        return selectedDishes;
    }

    async function resolveIds(csrfToken) {
        if (selectedDishes.length === 0) return [];
        return Promise.all(selectedDishes.map(async dish => {
            if (dish.linked) return dish.id;
            const resp = await fetch('/api/encyclopedia/create-placeholder/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ name: dish.name })
            });
            const result = await resp.json();
            if (!resp.ok) throw new Error(result.error || 'Failed to create placeholder');
            return result.entry.id;
        }));
    }

    function renderRows() {
        if (!selectedDiv || !chipsContainer) return;

        if (selectedDishes.length === 0) {
            selectedDiv.style.display = 'none';
            chipsContainer.innerHTML = '';
            return;
        }

        selectedDiv.style.display = 'block';
        chipsContainer.innerHTML = selectedDishes.map(dish => {
            const removeBtn = `<button type="button" class="btn-close btn-sm" data-remove-row-id="${dish.rowId}" aria-label="Remove" style="font-size:0.6rem;"></button>`;
            if (dish.linked) {
                return `
                    <div class="d-flex align-items-center gap-2 mb-1" data-row-id="${dish.rowId}">
                        <span class="badge bg-success d-flex align-items-center gap-1" style="font-size:0.85rem;padding:0.4rem 0.65rem;">
                            <i class="bi bi-book"></i> ${dish.name}
                        </span>
                        ${removeBtn}
                    </div>`;
            }
            return `
                <div class="d-flex align-items-center gap-2 mb-1 flex-wrap" data-row-id="${dish.rowId}">
                    <span class="badge bg-warning text-dark" style="font-size:0.85rem;padding:0.4rem 0.65rem;">
                        <i class="bi bi-plus-circle"></i> New placeholder
                    </span>
                    <span>${dish.name}</span>
                    <button type="button" class="badge bg-secondary border-0 link-similar-row-btn text-white"
                            data-row-id="${dish.rowId}"
                            style="font-size:0.75rem;padding:0.3rem 0.5rem;cursor:pointer;">
                        <i class="bi bi-link-45deg"></i> Link existing
                    </button>
                    ${removeBtn}
                    <div class="inline-similar-search w-100 mt-1" data-row-id="${dish.rowId}" style="display:none;">
                        <input type="text" class="form-control form-control-sm inline-similar-input" placeholder="Search to link existing entry...">
                        <div class="list-group mt-1 inline-similar-results" style="max-height:150px;overflow-y:auto;display:none;"></div>
                    </div>
                </div>`;
        }).join('');

        chipsContainer.querySelectorAll('[data-remove-row-id]').forEach(btn => {
            btn.addEventListener('click', function () {
                const rowId = parseInt(this.dataset.removeRowId, 10);
                selectedDishes = selectedDishes.filter(d => d.rowId !== rowId);
                renderRows();
            });
        });

        chipsContainer.querySelectorAll('.link-similar-row-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                const rowId = parseInt(this.dataset.rowId, 10);
                const searchDiv = chipsContainer.querySelector(`.inline-similar-search[data-row-id="${rowId}"]`);
                if (searchDiv) {
                    searchDiv.style.display = searchDiv.style.display === 'none' ? 'block' : 'none';
                    const input = searchDiv.querySelector('.inline-similar-input');
                    if (input && searchDiv.style.display === 'block') input.focus();
                }
            });
        });

        chipsContainer.querySelectorAll('.inline-similar-input').forEach(input => {
            let inlineTimeout = null;
            input.addEventListener('input', function () {
                clearTimeout(inlineTimeout);
                const query = this.value.trim();
                const resultsEl = this.closest('.inline-similar-search').querySelector('.inline-similar-results');
                const rowId = parseInt(this.closest('.inline-similar-search').dataset.rowId, 10);

                if (query.length < 2) {
                    resultsEl.style.display = 'none';
                    resultsEl.innerHTML = '';
                    return;
                }

                inlineTimeout = setTimeout(() => {
                    fetch(`${searchUrl}?q=${encodeURIComponent(query)}`)
                        .then(r => r.json())
                        .then(data => {
                            if (!data.results || data.results.length === 0) {
                                resultsEl.style.display = 'none';
                                return;
                            }
                            resultsEl.style.display = 'block';
                            resultsEl.innerHTML = data.results.map(entry => `
                                <button type="button" class="list-group-item list-group-item-action inline-similar-result"
                                        data-row-id="${rowId}"
                                        data-entry-id="${entry.id}"
                                        data-entry-name="${entry.name}">
                                    <div class="d-flex w-100 justify-content-between">
                                        <span>${entry.name}</span>
                                        ${entry.cuisine_type ? `<small class="badge bg-info">${entry.cuisine_type}</small>` : ''}
                                    </div>
                                </button>
                            `).join('');

                            resultsEl.querySelectorAll('.inline-similar-result').forEach(item => {
                                item.addEventListener('click', function () {
                                    const targetRowId = parseInt(this.dataset.rowId, 10);
                                    const row = selectedDishes.find(d => d.rowId === targetRowId);
                                    if (row) {
                                        row.id = this.dataset.entryId;
                                        row.name = this.dataset.entryName;
                                        row.linked = true;
                                    }
                                    renderRows();
                                });
                            });
                        })
                        .catch(() => { resultsEl.style.display = 'none'; });
                }, 300);
            });
        });
    }

    function updateSelection(items) {
        items.forEach((item, index) => {
            if (index === selectedIndex) {
                item.classList.add('active');
                item.scrollIntoView({ block: 'nearest' });
            } else {
                item.classList.remove('active');
            }
        });
    }

    function commitInput() {
        const items = searchResults.querySelectorAll('.similar-dish-result');
        if (selectedIndex >= 0 && items[selectedIndex]) {
            const item = items[selectedIndex];
            addRow({ id: item.dataset.similarId, name: item.dataset.similarName, linked: true });
        } else {
            const text = searchInput.value.trim().replace(/,+$/, '');
            if (text) addRow({ id: null, name: text, linked: false });
        }
        searchResults.style.display = 'none';
        selectedIndex = -1;
        searchInput.value = '';
    }

    if (searchInput) {
        searchInput.addEventListener('input', function () {
            clearTimeout(searchTimeout);
            selectedIndex = -1;
            const query = this.value.trim();

            if (query.length < 2) {
                searchResults.style.display = 'none';
                searchResults.innerHTML = '';
                return;
            }

            searchTimeout = setTimeout(() => {
                fetch(`${searchUrl}?q=${encodeURIComponent(query)}`)
                    .then(r => r.json())
                    .then(data => {
                        if (!data.results || data.results.length === 0) {
                            searchResults.style.display = 'none';
                            return;
                        }

                        searchResults.style.display = 'block';
                        searchResults.innerHTML = data.results.map(entry => `
                            <button type="button" class="list-group-item list-group-item-action similar-dish-result"
                                    data-similar-id="${entry.id}"
                                    data-similar-name="${entry.name}">
                                <div class="d-flex w-100 justify-content-between">
                                    <span>${entry.name}</span>
                                    ${entry.cuisine_type ? `<small class="badge bg-info">${entry.cuisine_type}</small>` : ''}
                                </div>
                                ${entry.hierarchy ? `<small class="text-muted">${entry.hierarchy}</small>` : ''}
                            </button>
                        `).join('');

                        searchResults.querySelectorAll('.similar-dish-result').forEach(item => {
                            item.addEventListener('click', function () {
                                addRow({ id: this.dataset.similarId, name: this.dataset.similarName, linked: true });
                                searchResults.style.display = 'none';
                                selectedIndex = -1;
                                searchInput.value = '';
                            });
                        });
                    })
                    .catch(() => { searchResults.style.display = 'none'; });
            }, 300);
        });

        searchInput.addEventListener('keydown', function (e) {
            const items = searchResults.querySelectorAll('.similar-dish-result');

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
                updateSelection(items);
                return;
            }
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                selectedIndex = Math.max(selectedIndex - 1, -1);
                updateSelection(items);
                return;
            }
            if (e.key === 'Enter' || e.key === ',') {
                e.preventDefault();
                commitInput();
            }
        });

        searchInput.addEventListener('paste', function (e) {
            e.preventDefault();
            const text = (e.clipboardData || window.clipboardData).getData('text');
            const names = text.split(/[,\n]/).map(s => s.trim()).filter(Boolean);
            if (names.length === 0) return;

            Promise.all(names.map(name =>
                fetch(`${searchUrl}?q=${encodeURIComponent(name)}`)
                    .then(r => r.json())
                    .then(data => {
                        const match = data.results && data.results[0];
                        const isClose = match && match.name.toLowerCase() === name.toLowerCase();
                        return isClose
                            ? { id: match.id, name: match.name, linked: true }
                            : { id: null, name, linked: false };
                    })
                    .catch(() => ({ id: null, name, linked: false }))
            )).then(rows => {
                rows.forEach(row => addRow(row));
                searchInput.value = '';
            });
        });
    }

    if (addBtn) addBtn.addEventListener('click', commitInput);

    return { reset, addRow, getSelected, resolveIds };
}
