// Encyclopedia Parent Management JavaScript
// Drives the shared encyclopedia link modal (via window.EncyclopediaLinkModal, defined in
// encyclopedia_link.js) in "select parent" mode, rather than wiring up its own competing
// listeners on the modal's elements.

document.addEventListener('DOMContentLoaded', function() {
    const pageData = document.getElementById('encyclopediaPageData');
    if (!pageData) return; // Not on encyclopedia detail page or not staff

    const modalElement = document.getElementById('encyclopediaLinkModal');
    if (!modalElement) return; // Modal not present
    if (!window.EncyclopediaLinkModal) return; // encyclopedia_link.js not loaded

    const addParentBtn = document.getElementById('addParentBtn');
    const changeParentBtn = document.getElementById('changeParentBtn');
    const removeParentBtn = document.getElementById('removeParentBtn');

    // Get data
    const entryId = parseInt(pageData.dataset.entryId);
    const entryName = pageData.dataset.entryName;
    const setParentUrl = pageData.dataset.setParentUrl;

    // Exclude self (descendants are filtered server-side via the search results' hierarchy,
    // but self must always be excluded from candidate parents)
    const excludedIds = new Set([entryId]);

    function openParentSelectionModal() {
        window.EncyclopediaLinkModal.openForSelection({
            title: 'Select Parent Entry',
            searchLabelPrefix: 'Search for parent of:',
            nameForDisplay: entryName,
            saveButtonLabel: '<i class="bi bi-check-circle"></i> Create & Set as Parent',
            filterResults: (results) => results.filter(entry => !excludedIds.has(entry.id)),
            onResultSelected: (entry) => setParent(entry.id, entry.name),
            onEntryCreated: (entry) => setParent(entry.id, entry.name)
        });
    }

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
                bootstrap.Modal.getInstance(modalElement)?.hide();
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
