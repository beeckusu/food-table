// Review Dish List - Encyclopedia Badge Linking JavaScript
// Handles clicking on badges to link/unlink dishes in the list view

document.addEventListener('DOMContentLoaded', function() {
    const modalElement = document.getElementById('encyclopediaLinkModal');
    if (!modalElement) return; // Modal not present (user not staff)

    const modal = new bootstrap.Modal(modalElement);
    const searchInput = document.getElementById('encyclopediaSearch');
    const searchResults = document.getElementById('searchResults');
    const searchStatus = document.getElementById('searchStatus');
    const currentDishNameEl = document.getElementById('currentDishName');
    const suggestedMatchesSection = document.getElementById('suggestedMatchesSection');
    const suggestedMatches = document.getElementById('suggestedMatches');
    const showCreateFormBtn = document.getElementById('showCreateFormBtn');

    // Create form elements
    const searchSection = document.getElementById('searchSection');
    const createEntrySection = document.getElementById('createEntrySection');
    const searchFooter = document.getElementById('searchFooter');
    const createFooter = document.getElementById('createFooter');
    const backToSearchBtn = document.getElementById('backToSearch');
    const cancelCreateBtn = document.getElementById('cancelCreate');
    const saveAndLinkBtn = document.getElementById('saveAndLinkBtn');
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

    let currentDishId = null;
    let currentDishName = null;
    let currentBadgeElement = null;
    let searchTimeout = null;
    let parentSearchTimeout = null;
    let selectedIndex = -1;
    let selectedParentId = null;

    // Attach click handlers to unlinked badges (link)
    function attachUnlinkedHandlers() {
        document.querySelectorAll('.encyclopedia-badge-unlinked').forEach(badge => {
            badge.addEventListener('click', function() {
                currentDishId = this.dataset.dishId;
                currentDishName = this.dataset.dishName;
                currentBadgeElement = this;

                currentDishNameEl.textContent = currentDishName;
                searchInput.value = '';
                selectedIndex = -1;
                showCreateFormBtn.style.display = 'inline-block';

                // Reset search results
                searchResults.innerHTML = '';
                searchStatus.style.display = 'none';
                suggestedMatchesSection.style.display = 'none';

                // Reset to search view
                resetToSearchView();

                modal.show();

                // Load suggestions based on dish name
                loadSuggestions(currentDishName);

                // Focus on search input
                setTimeout(() => searchInput.focus(), 100);
            });
        });
    }

    // Attach click handlers to linked badges (unlink)
    function attachLinkedHandlers() {
        document.querySelectorAll('.encyclopedia-badge-linked').forEach(badge => {
            badge.addEventListener('click', function() {
                const dishId = this.dataset.dishId;
                const encyclopediaName = this.dataset.encyclopediaName;

                if (confirm(`Unlink "${encyclopediaName}"?`)) {
                    unlinkDish(dishId, this);
                }
            });
        });
    }

    // Initial attachment
    attachUnlinkedHandlers();
    attachLinkedHandlers();

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
                            data-entry-name="${entry.name}">
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
                        linkDish(currentDishId, this.dataset.entryId, this.dataset.entryName);
                    });
                });
            })
            .catch(error => {
                console.error('Suggestion loading error:', error);
                suggestedMatchesSection.style.display = 'none';
            });
    }

    function performSearch(query) {
        const apiUrl = modalElement.dataset.searchUrl;

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

                showCreateFormBtn.style.display = 'inline-block';
                selectedIndex = -1;
                searchResults.innerHTML = data.results.map(entry => `
                    <button type="button" class="list-group-item list-group-item-action encyclopedia-result"
                            data-entry-id="${entry.id}"
                            data-entry-name="${entry.name}">
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
                        linkDish(currentDishId, this.dataset.entryId, this.dataset.entryName);
                    });
                });
            })
            .catch(error => {
                console.error('Search error:', error);
                searchStatus.style.display = 'block';
                searchStatus.innerHTML = '<em class="text-danger">Error performing search</em>';
            });
    }

    function linkDish(dishId, encyclopediaId, encyclopediaName) {
        const csrfToken = getCookie('csrftoken');
        const badge = currentBadgeElement;

        // Show loading state
        badge.disabled = true;
        badge.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>';

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
                // Update badge to linked state
                badge.className = 'badge bg-success border-0 encyclopedia-badge-linked';
                badge.title = `Linked to: ${encyclopediaName}. Click to unlink.`;
                badge.dataset.encyclopediaId = encyclopediaId;
                badge.dataset.encyclopediaName = encyclopediaName;
                badge.innerHTML = `<i class="bi bi-check-circle-fill"></i><span class="d-none d-xl-inline"> ${encyclopediaName.substring(0, 12)}${encyclopediaName.length > 12 ? '...' : ''}</span>`;
                badge.disabled = false;

                // Re-attach handlers
                attachLinkedHandlers();

                modal.hide();
                showToast('Success', `Linked to ${encyclopediaName}`, 'success');
            } else {
                badge.disabled = false;
                badge.innerHTML = '<i class="bi bi-exclamation-circle-fill"></i><span class="d-none d-xl-inline"> Unlinked</span>';
                showToast('Error', data.error || 'Failed to link dish', 'danger');
            }
        })
        .catch(error => {
            console.error('Link error:', error);
            badge.disabled = false;
            badge.innerHTML = '<i class="bi bi-exclamation-circle-fill"></i><span class="d-none d-xl-inline"> Unlinked</span>';
            showToast('Error', 'Failed to link dish', 'danger');
        });
    }

    function unlinkDish(dishId, badge) {
        const csrfToken = getCookie('csrftoken');

        // Show loading state
        badge.disabled = true;
        badge.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>';

        fetch(`/api/dishes/${dishId}/link/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Get the dish name from the row
                const row = badge.closest('tr');
                const dishNameLink = row.querySelector('.review-link');
                const dishName = dishNameLink ? dishNameLink.textContent.trim() : 'Unnamed Dish';

                // Update badge to unlinked state
                badge.className = 'badge bg-warning text-dark border-0 encyclopedia-badge-unlinked';
                badge.title = 'Click to link to encyclopedia';
                badge.dataset.dishName = dishName;
                delete badge.dataset.encyclopediaId;
                delete badge.dataset.encyclopediaName;
                badge.innerHTML = '<i class="bi bi-exclamation-circle-fill"></i><span class="d-none d-xl-inline"> Unlinked</span>';
                badge.disabled = false;

                // Re-attach handlers
                attachUnlinkedHandlers();

                showToast('Success', 'Encyclopedia entry unlinked', 'success');
            } else {
                badge.disabled = false;
                showToast('Error', data.error || 'Failed to unlink dish', 'danger');
            }
        })
        .catch(error => {
            console.error('Unlink error:', error);
            badge.disabled = false;
            showToast('Error', 'Failed to unlink dish', 'danger');
        });
    }

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
        createFormError.style.display = 'none';

        // Focus on description field since name is pre-filled
        setTimeout(() => entryDescriptionInput.focus(), 100);
    }

    function resetToSearchView() {
        searchSection.style.display = 'block';
        createEntrySection.style.display = 'none';
        searchFooter.style.display = 'block';
        createFooter.style.display = 'none';
        selectedParentId = null;
    }

    // Button handlers
    showCreateFormBtn.addEventListener('click', showCreateForm);
    backToSearchBtn.addEventListener('click', resetToSearchView);
    cancelCreateBtn.addEventListener('click', resetToSearchView);

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
            const apiUrl = modalElement.dataset.searchUrl;

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

    // Save & Link button handler
    saveAndLinkBtn.addEventListener('click', function() {
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
        const csrfToken = getCookie('csrftoken');

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
                // Update badge to linked state
                const badge = currentBadgeElement;
                const encyclopediaName = data.encyclopedia.name;
                const encyclopediaId = data.encyclopedia.id;

                badge.className = 'badge bg-success border-0 encyclopedia-badge-linked';
                badge.title = `Linked to: ${encyclopediaName}. Click to unlink.`;
                badge.dataset.encyclopediaId = encyclopediaId;
                badge.dataset.encyclopediaName = encyclopediaName;
                badge.innerHTML = `<i class="bi bi-check-circle-fill"></i><span class="d-none d-xl-inline"> ${encyclopediaName.substring(0, 12)}${encyclopediaName.length > 12 ? '...' : ''}</span>`;

                // Re-attach handlers
                attachLinkedHandlers();

                modal.hide();
                showToast('Success', `Created and linked ${encyclopediaName}`, 'success');
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
