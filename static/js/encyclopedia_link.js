// Encyclopedia Link Modal JavaScript
// Handles linking/unlinking dishes to encyclopedia entries

document.addEventListener('DOMContentLoaded', function() {
    const modalElement = document.getElementById('encyclopediaLinkModal');
    if (!modalElement) return; // Modal not present (user not authenticated)

    const modal = new bootstrap.Modal(modalElement);
    const searchInput = document.getElementById('encyclopediaSearch');
    const searchResults = document.getElementById('searchResults');
    const searchStatus = document.getElementById('searchStatus');
    const currentDishNameEl = document.getElementById('currentDishName');
    let currentDishId = null;
    let currentDishName = null;
    let searchTimeout = null;
    let selectedIndex = -1;

    // Open modal when "Link to Encyclopedia" button is clicked
    function attachLinkHandlers() {
        document.querySelectorAll('.link-dish-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                currentDishId = this.dataset.dishId;
                currentDishName = this.dataset.dishName;
                currentDishNameEl.textContent = currentDishName;
                searchInput.value = '';
                selectedIndex = -1;
                modal.show();
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
        currentDishId = null;
        currentDishName = null;
        selectedIndex = -1;
    });

    // Debounced search
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();

        if (query.length < 2) {
            searchResults.innerHTML = '';
            searchStatus.style.display = 'block';
            searchStatus.innerHTML = '<em>Type at least 2 characters to search</em>';
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
                    return;
                }

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
