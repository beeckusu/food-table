// Encyclopedia Link Modal JavaScript
// Handles linking/unlinking dishes to encyclopedia entries and creating new entries

document.addEventListener('DOMContentLoaded', function() {
    const modalElement = document.getElementById('encyclopediaLinkModal');
    if (!modalElement) return; // Modal not present (user not authenticated)

    const modal = new bootstrap.Modal(modalElement);
    const searchInput = document.getElementById('encyclopediaSearch');
    const searchResults = document.getElementById('searchResults');
    const searchStatus = document.getElementById('searchStatus');
    const currentDishNameEl = document.getElementById('currentDishName');
    const suggestedMatchesSection = document.getElementById('suggestedMatchesSection');
    const suggestedMatches = document.getElementById('suggestedMatches');

    // Create form elements
    const searchSection = document.getElementById('searchSection');
    const createEntrySection = document.getElementById('createEntrySection');
    const searchFooter = document.getElementById('searchFooter');
    const createFooter = document.getElementById('createFooter');
    const showCreateFormBtn = document.getElementById('showCreateFormBtn');
    const backToSearchBtn = document.getElementById('backToSearch');
    const cancelCreateBtn = document.getElementById('cancelCreate');
    const saveAndLinkBtn = document.getElementById('saveAndLinkBtn');
    const createEntryForm = document.getElementById('createEntryForm');
    const createFormError = document.getElementById('createFormError');

    // Form fields
    const entryNameInput = document.getElementById('entryName');
    const entryDescriptionInput = document.getElementById('entryDescription');
    const entryCuisineTypeInput = document.getElementById('entryCuisineType');
    const entryDishCategoryInput = document.getElementById('entryDishCategory');
    const entryRegionInput = document.getElementById('entryRegion');
    const entryCulturalSignificanceInput = document.getElementById('entryCulturalSignificance');
    const entryPopularExamplesInput = document.getElementById('entryPopularExamples');
    const entryHistoryInput = document.getElementById('entryHistory');
    const entryParentSearchInput = document.getElementById('entryParentSearch');
    const parentSearchResults = document.getElementById('parentSearchResults');
    const selectedParentDiv = document.getElementById('selectedParent');
    const selectedParentNameSpan = document.getElementById('selectedParentName');
    const clearParentBtn = document.getElementById('clearParent');
    const entrySimilarDishesSearchInput = document.getElementById('entrySimilarDishesSearch');
    const similarDishesSearchResults = document.getElementById('similarDishesSearchResults');
    const selectedSimilarDishesDiv = document.getElementById('selectedSimilarDishes');
    const similarDishesChips = document.getElementById('similarDishesChips');

    let currentDishId = null;
    let currentDishName = null;
    let searchTimeout = null;
    let parentSearchTimeout = null;
    let selectedIndex = -1;
    let selectedParentId = null;
    let similarDishesSearchTimeout = null;
    let selectedSimilarDishes = []; // Array of {rowId, id, name, linked}
    let similarDishRowCounter = 0;
    let similarDishesSelectedIndex = -1;

    // Open modal when "Link to Encyclopedia" button is clicked
    function attachLinkHandlers() {
        document.querySelectorAll('.link-dish-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                currentDishId = this.dataset.dishId;
                currentDishName = this.dataset.dishName;
                currentDishNameEl.textContent = currentDishName;
                searchInput.value = '';
                selectedIndex = -1;
                showCreateFormBtn.style.display = 'inline-block';
                modal.show();
                // Load suggestions based on dish name
                loadSuggestions(currentDishName);
                // Focus on search input
                setTimeout(() => searchInput.focus(), 100);
            });
        });
    }
    attachLinkHandlers();

    // Handle unlink button clicks
    function attachUnlinkHandlers() {
        document.querySelectorAll('.unlink-dish-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const dishId = this.dataset.dishId;
                if (confirm('Are you sure you want to unlink this encyclopedia entry?')) {
                    unlinkDishFromEncyclopedia(dishId);
                }
            });
        });
    }
    attachUnlinkHandlers();

    // Reset modal on close
    modalElement.addEventListener('hidden.bs.modal', function() {
        searchInput.value = '';
        searchResults.innerHTML = '';
        searchStatus.style.display = 'none';
        suggestedMatchesSection.style.display = 'none';
        suggestedMatches.innerHTML = '';
        currentDishId = null;
        currentDishName = null;
        selectedIndex = -1;
        resetToSearchView();
    });

    // Show/hide create form functions
    function showCreateForm() {
        searchSection.style.display = 'none';
        createEntrySection.style.display = 'block';
        searchFooter.style.display = 'none';
        createFooter.style.display = 'block';

        // Pre-populate name with dish name
        entryNameInput.value = currentDishName || '';
        entryDescriptionInput.value = '';
        entryCuisineTypeInput.value = '';
        entryDishCategoryInput.value = '';
        entryRegionInput.value = '';
        entryCulturalSignificanceInput.value = '';
        entryPopularExamplesInput.value = '';
        entryHistoryInput.value = '';
        entryParentSearchInput.value = '';
        selectedParentId = null;
        selectedParentDiv.style.display = 'none';
        parentSearchResults.style.display = 'none';
        entrySimilarDishesSearchInput.value = '';
        selectedSimilarDishes = [];
        similarDishRowCounter = 0;
        similarDishesSelectedIndex = -1;
        selectedSimilarDishesDiv.style.display = 'none';
        similarDishesSearchResults.style.display = 'none';
        createFormError.style.display = 'none';

        // Focus on description field since name is pre-filled
        setTimeout(() => entryDescriptionInput.focus(), 100);
    }

    function resetToSearchView() {
        searchSection.style.display = 'block';
        createEntrySection.style.display = 'none';
        searchFooter.style.display = 'block';
        createFooter.style.display = 'none';
        showCreateFormBtn.style.display = 'none';
        createEntryForm.reset();
        selectedParentId = null;
    }

    // Button handlers
    showCreateFormBtn.addEventListener('click', showCreateForm);
    backToSearchBtn.addEventListener('click', resetToSearchView);
    cancelCreateBtn.addEventListener('click', resetToSearchView);

    // Prevent Enter from submitting the form (save is handled by the button click)
    createEntryForm.addEventListener('submit', function(e) { e.preventDefault(); });

    // Debounced search
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();

        if (query.length < 2) {
            searchResults.innerHTML = '';
            searchStatus.style.display = 'block';
            searchStatus.innerHTML = '<em>Type at least 2 characters to search</em>';
            showCreateFormBtn.style.display = 'inline-block';
            return;
        }

        searchStatus.style.display = 'block';
        searchStatus.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">Loading...</span></div> Searching...';

        searchTimeout = setTimeout(() => performSearch(query), 300);
    });

    // Keyboard navigation
    searchInput.addEventListener('keydown', function(e) {
        const items = searchResults.querySelectorAll('.list-group-item');

        if (e.key === 'Escape') {
            modal.hide();
            return;
        }

        if (items.length === 0) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
            updateSelection(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedIndex = Math.max(selectedIndex - 1, -1);
            updateSelection(items);
        } else if (e.key === 'Enter' && selectedIndex >= 0) {
            e.preventDefault();
            items[selectedIndex].click();
        }
    });

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

    function loadSuggestions(dishName) {
        if (!dishName || dishName.trim().length === 0) {
            suggestedMatchesSection.style.display = 'none';
            return;
        }

        fetch(`/api/encyclopedia/suggest/?dish_name=${encodeURIComponent(dishName)}`)
            .then(response => response.json())
            .then(data => {
                if (data.suggestions.length === 0) {
                    suggestedMatchesSection.style.display = 'none';
                    return;
                }

                suggestedMatchesSection.style.display = 'block';
                suggestedMatches.innerHTML = data.suggestions.map(entry => `
                    <button type="button" class="list-group-item list-group-item-action suggestion-result"
                            data-entry-id="${entry.id}"
                            data-entry-name="${entry.name}"
                            data-entry-slug="${entry.slug}">
                        <div class="d-flex w-100 justify-content-between align-items-center">
                            <div>
                                <h6 class="mb-1">${entry.name}</h6>
                                ${entry.hierarchy ? `<small class="text-muted">${entry.hierarchy}</small>` : ''}
                            </div>
                            <span class="badge bg-success">${Math.round(entry.similarity * 100)}%</span>
                        </div>
                        ${entry.description ? `<p class="mb-0 mt-1 small text-muted">${entry.description}</p>` : ''}
                    </button>
                `).join('');

                // Add click handlers to suggestions
                document.querySelectorAll('.suggestion-result').forEach(item => {
                    item.addEventListener('click', function() {
                        linkDishToEncyclopedia(
                            currentDishId,
                            this.dataset.entryId,
                            this.dataset.entryName,
                            this.dataset.entrySlug
                        );
                    });
                });
            })
            .catch(error => {
                console.error('Suggestion loading error:', error);
                suggestedMatchesSection.style.display = 'none';
            });
    }

    function performSearch(query) {
        const apiUrl = document.getElementById('encyclopediaLinkModal').dataset.searchUrl;

        fetch(`${apiUrl}?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                searchStatus.style.display = 'none';

                if (data.results.length === 0) {
                    searchResults.innerHTML = '';
                    searchStatus.style.display = 'block';
                    searchStatus.innerHTML = '<em>No results found</em>';
                    showCreateFormBtn.style.display = 'inline-block';
                    return;
                }

                // Keep create button visible even with results
                showCreateFormBtn.style.display = 'inline-block';

                selectedIndex = -1;
                searchResults.innerHTML = data.results.map(entry => `
                    <button type="button" class="list-group-item list-group-item-action encyclopedia-result"
                            data-entry-id="${entry.id}"
                            data-entry-name="${entry.name}"
                            data-entry-slug="${entry.slug}">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">${entry.name}</h6>
                            ${entry.cuisine_type ? `<small class="badge bg-info">${entry.cuisine_type}</small>` : ''}
                        </div>
                        ${entry.hierarchy ? `<small class="text-muted"><i class="bi bi-arrow-right-short"></i> ${entry.hierarchy}</small>` : ''}
                        ${entry.dish_category ? `<small class="badge bg-secondary ms-2">${entry.dish_category}</small>` : ''}
                    </button>
                `).join('');

                // Add click handlers to results
                document.querySelectorAll('.encyclopedia-result').forEach(item => {
                    item.addEventListener('click', function() {
                        linkDishToEncyclopedia(
                            currentDishId,
                            this.dataset.entryId,
                            this.dataset.entryName,
                            this.dataset.entrySlug
                        );
                    });
                });
            })
            .catch(error => {
                console.error('Search error:', error);
                searchStatus.style.display = 'block';
                searchStatus.innerHTML = '<em class="text-danger">Error performing search</em>';
            });
    }

    function linkDishToEncyclopedia(dishId, encyclopediaId, encyclopediaName, encyclopediaSlug) {
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                         getCookie('csrftoken');

        fetch(`/api/dishes/${dishId}/link/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                encyclopedia_id: encyclopediaId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update the UI
                const dishBtn = document.querySelector(`.link-dish-btn[data-dish-id="${dishId}"]`);
                if (dishBtn) {
                    const dishName = dishBtn.dataset.dishName;
                    const container = dishBtn.closest('.mb-2');

                    // Replace the link button with the encyclopedia link display
                    container.innerHTML = `
                        <small class="text-muted">
                            <i class="bi bi-book"></i> Linked to:
                            <a href="/encyclopedia/${encyclopediaSlug}/" class="text-decoration-none">
                                <strong>${encyclopediaName}</strong>
                            </a>
                            <button class="btn btn-link btn-sm p-0 ms-1 text-danger unlink-dish-btn"
                                    data-dish-id="${dishId}"
                                    style="font-size: 0.75rem; text-decoration: none;"
                                    title="Unlink encyclopedia entry">
                                <i class="bi bi-x-circle"></i>
                            </button>
                        </small>
                    `;

                    // Re-attach unlink handlers
                    attachUnlinkHandlers();
                }
                modal.hide();

                // Show success message
                showToast('Success', `Dish linked to ${encyclopediaName}`, 'success');
            } else {
                showToast('Error', data.error || 'Failed to link dish', 'danger');
            }
        })
        .catch(error => {
            console.error('Link error:', error);
            showToast('Error', 'Failed to link dish', 'danger');
        });
    }

    function unlinkDishFromEncyclopedia(dishId) {
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                         getCookie('csrftoken');

        fetch(`/api/dishes/${dishId}/link/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Find the unlink button and get the dish name from the h5
                const unlinkBtn = document.querySelector(`.unlink-dish-btn[data-dish-id="${dishId}"]`);
                if (unlinkBtn) {
                    const listItem = unlinkBtn.closest('.list-group-item');
                    const h5 = listItem.querySelector('h5');
                    const dishName = h5.textContent.trim();
                    const container = unlinkBtn.closest('.mb-2');

                    // Replace the encyclopedia link with the "Link to Encyclopedia" button
                    container.innerHTML = `
                        <button class="badge bg-secondary border-0 link-dish-btn"
                                data-dish-id="${dishId}"
                                data-dish-name="${dishName}"
                                style="cursor: pointer;">
                            <i class="bi bi-link-45deg"></i> Link to Encyclopedia
                        </button>
                    `;

                    // Re-attach link handlers
                    attachLinkHandlers();
                }

                // Show success message
                showToast('Success', 'Encyclopedia entry unlinked', 'success');
            } else {
                showToast('Error', data.error || 'Failed to unlink dish', 'danger');
            }
        })
        .catch(error => {
            console.error('Unlink error:', error);
            showToast('Error', 'Failed to unlink dish', 'danger');
        });
    }

    // Parent search autocomplete
    entryParentSearchInput.addEventListener('input', function() {
        clearTimeout(parentSearchTimeout);
        const query = this.value.trim();

        if (query.length < 2) {
            parentSearchResults.style.display = 'none';
            parentSearchResults.innerHTML = '';
            return;
        }

        parentSearchTimeout = setTimeout(() => {
            const apiUrl = document.getElementById('encyclopediaLinkModal').dataset.searchUrl;

            fetch(`${apiUrl}?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.results.length === 0) {
                        parentSearchResults.style.display = 'none';
                        return;
                    }

                    parentSearchResults.style.display = 'block';
                    parentSearchResults.innerHTML = data.results.map(entry => `
                        <button type="button" class="list-group-item list-group-item-action parent-result"
                                data-parent-id="${entry.id}"
                                data-parent-name="${entry.name}">
                            <div class="d-flex w-100 justify-content-between">
                                <span>${entry.name}</span>
                                ${entry.cuisine_type ? `<small class="badge bg-info">${entry.cuisine_type}</small>` : ''}
                            </div>
                            ${entry.hierarchy ? `<small class="text-muted">${entry.hierarchy}</small>` : ''}
                        </button>
                    `).join('');

                    // Add click handlers to parent results
                    document.querySelectorAll('.parent-result').forEach(item => {
                        item.addEventListener('click', function() {
                            selectedParentId = this.dataset.parentId;
                            selectedParentNameSpan.textContent = this.dataset.parentName;
                            selectedParentDiv.style.display = 'block';
                            parentSearchResults.style.display = 'none';
                            entryParentSearchInput.value = '';
                        });
                    });
                })
                .catch(error => {
                    console.error('Parent search error:', error);
                    parentSearchResults.style.display = 'none';
                });
        }, 300);
    });

    // Clear parent selection
    clearParentBtn.addEventListener('click', function() {
        selectedParentId = null;
        selectedParentDiv.style.display = 'none';
        entryParentSearchInput.value = '';
    });

    // Similar dishes search autocomplete
    if (entrySimilarDishesSearchInput) entrySimilarDishesSearchInput.addEventListener('input', function() {
        clearTimeout(similarDishesSearchTimeout);
        similarDishesSelectedIndex = -1;
        const query = this.value.trim();

        if (query.length < 2) {
            similarDishesSearchResults.style.display = 'none';
            similarDishesSearchResults.innerHTML = '';
            return;
        }

        similarDishesSearchTimeout = setTimeout(() => {
            const apiUrl = document.getElementById('encyclopediaLinkModal').dataset.searchUrl;

            fetch(`${apiUrl}?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.results.length === 0) {
                        similarDishesSearchResults.style.display = 'none';
                        return;
                    }

                    similarDishesSearchResults.style.display = 'block';
                    similarDishesSearchResults.innerHTML = data.results.map(entry => `
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

                    document.querySelectorAll('.similar-dish-result').forEach(item => {
                        item.addEventListener('click', function() {
                            addSimilarDishRow({ id: this.dataset.similarId, name: this.dataset.similarName, linked: true });
                            similarDishesSearchResults.style.display = 'none';
                            similarDishesSelectedIndex = -1;
                            entrySimilarDishesSearchInput.value = '';
                        });
                    });
                })
                .catch(error => {
                    console.error('Similar dishes search error:', error);
                    similarDishesSearchResults.style.display = 'none';
                });
        }, 300);
    }); // end input listener

    function commitSimilarDishInput() {
        const items = similarDishesSearchResults.querySelectorAll('.similar-dish-result');
        if (similarDishesSelectedIndex >= 0 && items[similarDishesSelectedIndex]) {
            const item = items[similarDishesSelectedIndex];
            addSimilarDishRow({ id: item.dataset.similarId, name: item.dataset.similarName, linked: true });
        } else {
            const text = entrySimilarDishesSearchInput.value.trim().replace(/,+$/, '');
            if (text) addSimilarDishRow({ id: null, name: text, linked: false });
        }
        similarDishesSearchResults.style.display = 'none';
        similarDishesSelectedIndex = -1;
        entrySimilarDishesSearchInput.value = '';
    }

    modalElement.addEventListener('click', function(e) {
        if (e.target.id === 'addSimilarDishBtn') commitSimilarDishInput();
    });

    if (entrySimilarDishesSearchInput) entrySimilarDishesSearchInput.addEventListener('keydown', function(e) {
        const items = similarDishesSearchResults.querySelectorAll('.similar-dish-result');

        if (e.key === 'ArrowDown' || e.keyCode === 40) {
            e.preventDefault();
            similarDishesSelectedIndex = Math.min(similarDishesSelectedIndex + 1, items.length - 1);
            updateSimilarDishSelection(items);
            return;
        }
        if (e.key === 'ArrowUp' || e.keyCode === 38) {
            e.preventDefault();
            similarDishesSelectedIndex = Math.max(similarDishesSelectedIndex - 1, -1);
            updateSimilarDishSelection(items);
            return;
        }
        if (e.key === 'Enter' || e.keyCode === 13) {
            e.preventDefault();
            commitSimilarDishInput();
        }
        if (e.key === ',' || e.keyCode === 188) {
            e.preventDefault();
            commitSimilarDishInput();
        }
    });

    if (entrySimilarDishesSearchInput) entrySimilarDishesSearchInput.addEventListener('paste', function(e) {
        e.preventDefault();
        const text = (e.clipboardData || window.clipboardData).getData('text');
        const names = text.split(/[,\n]/).map(s => s.trim()).filter(Boolean);
        if (names.length === 0) return;

        const apiUrl = document.getElementById('encyclopediaLinkModal').dataset.searchUrl;
        Promise.all(names.map(name =>
            fetch(`${apiUrl}?q=${encodeURIComponent(name)}`)
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
            rows.forEach(row => addSimilarDishRow(row));
            this.value = '';
        });
    });

    function updateSimilarDishSelection(items) {
        items.forEach((item, index) => {
            if (index === similarDishesSelectedIndex) {
                item.classList.add('active');
                item.scrollIntoView({ block: 'nearest' });
            } else {
                item.classList.remove('active');
            }
        });
    }

    function addSimilarDishRow({ id, name, linked }) {
        if (linked && selectedSimilarDishes.find(d => d.linked && d.id === id)) return;
        selectedSimilarDishes.push({ rowId: similarDishRowCounter++, id, name, linked });
        renderSimilarDishRows();
    }

    function renderSimilarDishRows() {
        if (selectedSimilarDishes.length === 0) {
            selectedSimilarDishesDiv.style.display = 'none';
            return;
        }

        selectedSimilarDishesDiv.style.display = 'block';
        similarDishesChips.innerHTML = selectedSimilarDishes.map(dish => {
            const removeBtn = `<button type="button" class="btn-close btn-sm" data-remove-row-id="${dish.rowId}" aria-label="Remove" style="font-size:0.6rem;"></button>`;
            if (dish.linked) {
                return `
                    <div class="d-flex align-items-center gap-2 mb-1" data-row-id="${dish.rowId}">
                        <span class="badge bg-success d-flex align-items-center gap-1" style="font-size:0.85rem;padding:0.4rem 0.65rem;">
                            <i class="bi bi-book"></i> ${dish.name}
                        </span>
                        ${removeBtn}
                    </div>`;
            } else {
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
            }
        }).join('');

        document.querySelectorAll('[data-remove-row-id]').forEach(btn => {
            btn.addEventListener('click', function() {
                const rowId = parseInt(this.dataset.removeRowId, 10);
                selectedSimilarDishes = selectedSimilarDishes.filter(d => d.rowId !== rowId);
                renderSimilarDishRows();
            });
        });

        document.querySelectorAll('.link-similar-row-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const rowId = parseInt(this.dataset.rowId, 10);
                const searchDiv = similarDishesChips.querySelector(`.inline-similar-search[data-row-id="${rowId}"]`);
                if (searchDiv) {
                    searchDiv.style.display = searchDiv.style.display === 'none' ? 'block' : 'none';
                    const input = searchDiv.querySelector('.inline-similar-input');
                    if (input && searchDiv.style.display === 'block') input.focus();
                }
            });
        });

        document.querySelectorAll('.inline-similar-input').forEach(input => {
            let inlineTimeout = null;
            input.addEventListener('input', function() {
                clearTimeout(inlineTimeout);
                const query = this.value.trim();
                const resultsEl = this.closest('.inline-similar-search').querySelector('.inline-similar-results');
                const rowId = parseInt(this.closest('.inline-similar-search').dataset.rowId, 10);

                if (query.length < 2) {
                    resultsEl.style.display = 'none';
                    resultsEl.innerHTML = '';
                    return;
                }

                const apiUrl = document.getElementById('encyclopediaLinkModal').dataset.searchUrl;
                inlineTimeout = setTimeout(() => {
                    fetch(`${apiUrl}?q=${encodeURIComponent(query)}`)
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
                                item.addEventListener('click', function() {
                                    const targetRowId = parseInt(this.dataset.rowId, 10);
                                    const row = selectedSimilarDishes.find(d => d.rowId === targetRowId);
                                    if (row) {
                                        row.id = this.dataset.entryId;
                                        row.name = this.dataset.entryName;
                                        row.linked = true;
                                    }
                                    renderSimilarDishRows();
                                });
                            });
                        })
                        .catch(() => { resultsEl.style.display = 'none'; });
                }, 300);
            });
        });
    }

    // AI prefill button handler
    const aiPrefillBtn = document.getElementById('aiPrefillBtn');
    if (aiPrefillBtn) {
        aiPrefillBtn.addEventListener('click', async function() {
            if (!currentDishName) {
                createFormError.textContent = 'No dish name set — please close and reopen the modal.';
                createFormError.style.display = 'block';
                return;
            }

            aiPrefillBtn.disabled = true;
            aiPrefillBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Asking Claude...';
            createFormError.style.display = 'none';

            // Show an in-form notice so the user knows to wait
            const waitNotice = document.createElement('div');
            waitNotice.id = 'aiWaitNotice';
            waitNotice.className = 'alert alert-info py-2 mt-2';
            waitNotice.innerHTML = '<i class="bi bi-hourglass-split me-1"></i> Claude is writing the entry — this usually takes 15–30 seconds.';
            aiPrefillBtn.closest('.d-flex').after(waitNotice);

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken');

            try {
                const resp = await fetch('/api/encyclopedia/ai-prefill/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                    body: JSON.stringify({ dish_name: entryNameInput.value.trim() || currentDishName })
                });
                const data = await resp.json();

                if (!resp.ok || !data.success) {
                    createFormError.textContent = data.error || 'AI prefill failed. Please try again.';
                    createFormError.style.display = 'block';
                    return;
                }

                const f = data.fields;
                if (f.name) entryNameInput.value = f.name;
                if (f.description) entryDescriptionInput.value = f.description;
                if (f.cuisine_type) entryCuisineTypeInput.value = f.cuisine_type;
                if (f.dish_category) entryDishCategoryInput.value = f.dish_category;
                if (f.region) entryRegionInput.value = f.region;
                if (f.cultural_significance) entryCulturalSignificanceInput.value = f.cultural_significance;
                if (f.popular_examples) entryPopularExamplesInput.value = f.popular_examples;
                if (f.history) entryHistoryInput.value = f.history;

                if (f.similar_dishes_globally) {
                    const names = f.similar_dishes_globally.split(',').map(s => s.trim()).filter(Boolean);
                    selectedSimilarDishes = [];
                    similarDishRowCounter = 0;
                    names.forEach(name => addSimilarDishRow({ id: null, name, linked: false }));
                }
            } catch (err) {
                console.error('AI prefill error:', err);
                createFormError.textContent = 'AI prefill failed. Please try again.';
                createFormError.style.display = 'block';
            } finally {
                aiPrefillBtn.disabled = false;
                aiPrefillBtn.innerHTML = '<i class="bi bi-stars"></i> Fill with Claude';
                document.getElementById('aiWaitNotice')?.remove();
            }
        });
    }

    // Save & Link button handler
    saveAndLinkBtn.addEventListener('click', async function() {
        // Validate form
        const name = entryNameInput.value.trim();
        const description = entryDescriptionInput.value.trim();

        if (!name || !description) {
            createFormError.textContent = 'Name and Description are required';
            createFormError.style.display = 'block';
            return;
        }

        createFormError.style.display = 'none';

        // Disable button to prevent double submission
        saveAndLinkBtn.disabled = true;
        saveAndLinkBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Creating...';

        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                         getCookie('csrftoken');

        // Resolve similar dishes: create placeholders for unlinked rows
        let resolvedSimilarIds = [];
        if (selectedSimilarDishes.length > 0) {
            try {
                resolvedSimilarIds = await Promise.all(selectedSimilarDishes.map(async dish => {
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
            } catch (err) {
                console.error('Placeholder creation error:', err);
                createFormError.textContent = 'Failed to create placeholder entries for unlinked dishes';
                createFormError.style.display = 'block';
                saveAndLinkBtn.disabled = false;
                saveAndLinkBtn.innerHTML = '<i class="bi bi-check-circle"></i> Save & Link';
                return;
            }
        }

        // Prepare data
        const data = {
            name: name,
            description: description,
            cuisine_type: entryCuisineTypeInput.value.trim() || '',
            dish_category: entryDishCategoryInput.value.trim() || '',
            region: entryRegionInput.value.trim() || '',
            cultural_significance: entryCulturalSignificanceInput.value.trim() || '',
            popular_examples: entryPopularExamplesInput.value.trim() || '',
            history: entryHistoryInput.value.trim() || '',
            dish_id: currentDishId
        };

        if (selectedParentId) {
            data.parent_id = selectedParentId;
        }

        if (resolvedSimilarIds.length > 0) {
            data.similar_dishes_ids = resolvedSimilarIds;
        }

        // Call create API
        fetch('/api/encyclopedia/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            saveAndLinkBtn.disabled = false;
            saveAndLinkBtn.innerHTML = '<i class="bi bi-check-circle"></i> Save & Link';

            if (data.success) {
                // Update the UI
                const dishBtn = document.querySelector(`.link-dish-btn[data-dish-id="${currentDishId}"]`);
                if (dishBtn) {
                    const container = dishBtn.closest('.mb-2');

                    // Replace the link button with the encyclopedia link display
                    container.innerHTML = `
                        <small class="text-muted">
                            <i class="bi bi-book"></i> Linked to:
                            <a href="/encyclopedia/${data.encyclopedia.slug}/" class="text-decoration-none">
                                <strong>${data.encyclopedia.name}</strong>
                            </a>
                            <button class="btn btn-link btn-sm p-0 ms-1 text-danger unlink-dish-btn"
                                    data-dish-id="${currentDishId}"
                                    style="font-size: 0.75rem; text-decoration: none;"
                                    title="Unlink encyclopedia entry">
                                <i class="bi bi-x-circle"></i>
                            </button>
                        </small>
                    `;

                    // Re-attach unlink handlers
                    attachUnlinkHandlers();
                }
                modal.hide();

                // Show success message
                showToast('Success', `Created and linked ${data.encyclopedia.name}`, 'success');
            } else {
                createFormError.textContent = data.error || 'Failed to create entry';
                createFormError.style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Create error:', error);
            saveAndLinkBtn.disabled = false;
            saveAndLinkBtn.innerHTML = '<i class="bi bi-check-circle"></i> Save & Link';
            createFormError.textContent = 'Failed to create entry';
            createFormError.style.display = 'block';
        });
    });

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function showToast(title, message, type) {
        // Simple toast notification
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
        alertDiv.style.zIndex = '9999';
        alertDiv.innerHTML = `
            <strong>${title}:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);
        setTimeout(() => alertDiv.remove(), 5000);
    }
});
