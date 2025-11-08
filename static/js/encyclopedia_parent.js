// Encyclopedia Parent Management JavaScript
// Reuses the existing encyclopedia link modal for parent selection

document.addEventListener('DOMContentLoaded', function() {
    const pageData = document.getElementById('encyclopediaPageData');
    if (!pageData) return; // Not on encyclopedia detail page or not staff

    const modalElement = document.getElementById('encyclopediaLinkModal');
    if (!modalElement) return; // Modal not present

    const modal = new bootstrap.Modal(modalElement);
    const modalTitle = document.getElementById('encyclopediaLinkModalLabel');
    const searchLabel = modalElement.querySelector('label[for="encyclopediaSearch"]');
    const currentDishNameEl = document.getElementById('currentDishName');
    const searchInput = document.getElementById('encyclopediaSearch');
    const searchResults = document.getElementById('searchResults');
    const searchStatus = document.getElementById('searchStatus');
    const showCreateFormBtn = document.getElementById('showCreateFormBtn');
    const saveAndLinkBtn = document.getElementById('saveAndLinkBtn');
    const parentEntrySection = document.getElementById('parentEntrySection');

    const addParentBtn = document.getElementById('addParentBtn');
    const changeParentBtn = document.getElementById('changeParentBtn');
    const removeParentBtn = document.getElementById('removeParentBtn');

    // Get data
    const entryId = parseInt(pageData.dataset.entryId);
    const entryName = pageData.dataset.entryName;
    const entrySlug = pageData.dataset.entrySlug;
    const setParentUrl = pageData.dataset.setParentUrl;
    const searchUrl = modalElement.dataset.searchUrl;

    let isParentSelectionMode = false;
    let searchTimeout = null;

    // Track descendants (including self) to exclude from selection
    const excludedIds = new Set([entryId]);

    // Handle "Create New Entry" button click
    showCreateFormBtn.addEventListener('click', function() {
        if (!isParentSelectionMode) return; // Only handle in parent selection mode

        // Switch to create form
        document.getElementById('searchSection').style.display = 'none';
        document.getElementById('createEntrySection').style.display = 'block';
        document.getElementById('searchFooter').style.display = 'none';
        document.getElementById('createFooter').style.display = 'block';

        // Clear form
        document.getElementById('createEntryForm').reset();
        document.getElementById('createFormError').style.display = 'none';

        // Focus on name input
        setTimeout(() => document.getElementById('entryName').focus(), 100);
    });

    // Handle back to search button
    const backToSearchBtn = document.getElementById('backToSearch');
    const cancelCreateBtn = document.getElementById('cancelCreate');

    if (backToSearchBtn) {
        backToSearchBtn.addEventListener('click', function() {
            if (!isParentSelectionMode) return;
            resetToSearchView();
        });
    }

    if (cancelCreateBtn) {
        cancelCreateBtn.addEventListener('click', function() {
            if (!isParentSelectionMode) return;
            resetToSearchView();
        });
    }

    function resetToSearchView() {
        document.getElementById('searchSection').style.display = 'block';
        document.getElementById('createEntrySection').style.display = 'none';
        document.getElementById('searchFooter').style.display = 'block';
        document.getElementById('createFooter').style.display = 'none';
        document.getElementById('createEntryForm').reset();

        // Reset parent selection state
        selectedParentForNewEntry = null;
        document.getElementById('selectedParent').style.display = 'none';
        document.getElementById('parentSearchResults').style.display = 'none';
    }

    // Handle parent search within create form (for the new entry's parent)
    const entryParentSearchInput = document.getElementById('entryParentSearch');
    const parentSearchResultsDiv = document.getElementById('parentSearchResults');
    const selectedParentDiv = document.getElementById('selectedParent');
    const selectedParentNameSpan = document.getElementById('selectedParentName');
    const clearParentBtn = document.getElementById('clearParent');

    let parentSearchForNewEntryTimeout = null;
    let selectedParentForNewEntry = null;

    if (entryParentSearchInput) {
        entryParentSearchInput.addEventListener('input', function() {
            if (!isParentSelectionMode) return;

            clearTimeout(parentSearchForNewEntryTimeout);
            const query = this.value.trim();

            if (query.length < 2) {
                parentSearchResultsDiv.style.display = 'none';
                parentSearchResultsDiv.innerHTML = '';
                return;
            }

            parentSearchForNewEntryTimeout = setTimeout(() => {
                fetch(`${searchUrl}?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.results.length === 0) {
                            parentSearchResultsDiv.style.display = 'none';
                            return;
                        }

                        parentSearchResultsDiv.style.display = 'block';
                        parentSearchResultsDiv.innerHTML = data.results.map(entry => `
                            <button type="button" class="list-group-item list-group-item-action new-entry-parent-result"
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
                        document.querySelectorAll('.new-entry-parent-result').forEach(item => {
                            item.addEventListener('click', function() {
                                selectedParentForNewEntry = this.dataset.parentId;
                                selectedParentNameSpan.textContent = this.dataset.parentName;
                                selectedParentDiv.style.display = 'block';
                                parentSearchResultsDiv.style.display = 'none';
                                entryParentSearchInput.value = '';
                            });
                        });
                    })
                    .catch(error => {
                        console.error('Parent search error:', error);
                        parentSearchResultsDiv.style.display = 'none';
                    });
            }, 300);
        });
    }

    // Clear parent selection for new entry
    if (clearParentBtn) {
        clearParentBtn.addEventListener('click', function() {
            if (!isParentSelectionMode) return;
            selectedParentForNewEntry = null;
            selectedParentDiv.style.display = 'none';
            entryParentSearchInput.value = '';
        });
    }

    // Attach event handlers for parent management buttons
    if (addParentBtn) {
        addParentBtn.addEventListener('click', openParentSelectionModal);
    }

    if (changeParentBtn) {
        changeParentBtn.addEventListener('click', openParentSelectionModal);
    }

    if (removeParentBtn) {
        removeParentBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to remove the parent entry?')) {
                setParent(null);
            }
        });
    }

    function openParentSelectionModal() {
        isParentSelectionMode = true;

        // Update modal UI for parent selection
        modalTitle.textContent = 'Select Parent Entry';
        searchLabel.innerHTML = `Search for parent of: <strong>${entryName}</strong>`;
        currentDishNameEl.textContent = entryName;

        // Hide suggested matches section (not needed for parent selection)
        const suggestedMatchesSection = document.getElementById('suggestedMatchesSection');
        if (suggestedMatchesSection) {
            suggestedMatchesSection.style.display = 'none';
        }

        // Clear and reset
        searchInput.value = '';
        searchResults.innerHTML = '';
        searchStatus.style.display = 'block';
        searchStatus.innerHTML = '<em>Type at least 2 characters to search</em>';
        showCreateFormBtn.style.display = 'inline-block';

        // Update the "Save & Link" button text
        const originalText = saveAndLinkBtn.innerHTML;
        saveAndLinkBtn.dataset.originalText = originalText;
        saveAndLinkBtn.innerHTML = '<i class="bi bi-check-circle"></i> Create & Set as Parent';

        // Ensure search and create sections are in correct state
        document.getElementById('searchSection').style.display = 'block';
        document.getElementById('createEntrySection').style.display = 'none';
        document.getElementById('searchFooter').style.display = 'block';
        document.getElementById('createFooter').style.display = 'none';

        modal.show();
        setTimeout(() => searchInput.focus(), 100);
    }

    // Intercept the modal's search functionality
    searchInput.addEventListener('input', function(e) {
        if (!isParentSelectionMode) return; // Let original handler work for dish linking

        e.stopImmediatePropagation();
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

        searchTimeout = setTimeout(() => performParentSearch(query), 300);
    }, true); // Use capture phase to intercept early

    function performParentSearch(query) {
        fetch(`${searchUrl}?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                searchStatus.style.display = 'none';

                // Filter out excluded entries (self and descendants)
                const filteredResults = data.results.filter(entry => !excludedIds.has(entry.id));

                if (filteredResults.length === 0) {
                    searchResults.innerHTML = '';
                    searchStatus.style.display = 'block';
                    searchStatus.innerHTML = '<em>No valid parent entries found</em>';
                    showCreateFormBtn.style.display = 'inline-block';
                    return;
                }

                showCreateFormBtn.style.display = 'inline-block';

                searchResults.innerHTML = filteredResults.map(entry => `
                    <button type="button" class="list-group-item list-group-item-action parent-selection-result"
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

                // Add click handlers
                document.querySelectorAll('.parent-selection-result').forEach(item => {
                    item.addEventListener('click', function() {
                        const parentId = this.dataset.entryId;
                        const parentName = this.dataset.entryName;
                        setParent(parentId, parentName);
                    });
                });
            })
            .catch(error => {
                console.error('Search error:', error);
                searchStatus.style.display = 'block';
                searchStatus.innerHTML = '<em class="text-danger">Error performing search</em>';
            });
    }

    // Intercept the "Save & Link" button for parent creation
    saveAndLinkBtn.addEventListener('click', function(e) {
        if (!isParentSelectionMode) return; // Let original handler work

        e.stopImmediatePropagation();
        e.preventDefault();

        // Get form values
        const name = document.getElementById('entryName').value.trim();
        const description = document.getElementById('entryDescription').value.trim();
        const createFormError = document.getElementById('createFormError');

        if (!name || !description) {
            createFormError.textContent = 'Name and Description are required';
            createFormError.style.display = 'block';
            return;
        }

        createFormError.style.display = 'none';

        // Disable button
        this.disabled = true;
        this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Creating...';

        const csrfToken = getCookie('csrftoken');

        // Create the encyclopedia entry
        const data = {
            name: name,
            description: description,
            cuisine_type: document.getElementById('entryCuisineType').value.trim() || '',
            dish_category: document.getElementById('entryDishCategory').value.trim() || '',
            region: document.getElementById('entryRegion').value.trim() || '',
            cultural_significance: document.getElementById('entryCulturalSignificance').value.trim() || '',
            popular_examples: document.getElementById('entryPopularExamples').value.trim() || '',
            history: document.getElementById('entryHistory').value.trim() || '',
        };

        // Add parent for the new entry if one was selected
        if (selectedParentForNewEntry) {
            data.parent_id = selectedParentForNewEntry;
        }

        // Note: We're NOT passing dish_id since we're creating a parent, not linking a dish

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
            this.disabled = false;
            this.innerHTML = '<i class="bi bi-check-circle"></i> Create & Set as Parent';

            if (data.success) {
                // Now set the created entry as parent
                setParent(data.encyclopedia.id, data.encyclopedia.name);
            } else {
                createFormError.textContent = data.error || 'Failed to create entry';
                createFormError.style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Create error:', error);
            this.disabled = false;
            this.innerHTML = '<i class="bi bi-check-circle"></i> Create & Set as Parent';
            createFormError.textContent = 'Failed to create entry';
            createFormError.style.display = 'block';
        });
    }, true); // Use capture phase

    function setParent(parentId, parentName) {
        const csrfToken = getCookie('csrftoken');
        const body = parentId === null ? { parent_id: null } : { parent_id: parseInt(parentId) };

        fetch(setParentUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(body)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                modal.hide();
                const message = parentId === null ?
                    'Parent entry removed' :
                    `Parent set to ${parentName || data.entry.parent.name}`;
                showToast('Success', message, 'success');

                // Reload page to update breadcrumbs and UI
                setTimeout(() => window.location.reload(), 1000);
            } else {
                showToast('Error', data.error || 'Failed to update parent', 'danger');
            }
        })
        .catch(error => {
            console.error('Set parent error:', error);
            showToast('Error', 'Failed to update parent', 'danger');
        });
    }

    // Reset modal when closed
    modalElement.addEventListener('hidden.bs.modal', function() {
        if (isParentSelectionMode) {
            isParentSelectionMode = false;

            // Restore original modal state
            modalTitle.textContent = 'Link Dish to Encyclopedia Entry';
            if (saveAndLinkBtn.dataset.originalText) {
                saveAndLinkBtn.innerHTML = saveAndLinkBtn.dataset.originalText;
            }
        }
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
