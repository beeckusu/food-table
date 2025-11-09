// Encyclopedia Placeholder Conversion JavaScript
// Handles converting placeholder entries to full entries

document.addEventListener('DOMContentLoaded', function() {
    const modalElement = document.getElementById('placeholderConvertModal');
    if (!modalElement) return; // Modal not present (user not staff)

    const modal = new bootstrap.Modal(modalElement);
    const placeholderNameSpan = document.getElementById('placeholderName');
    const editInAdminBtn = document.getElementById('editInAdminBtn');

    // Section elements
    const choiceSection = document.getElementById('placeholderChoiceSection');
    const formSection = document.getElementById('placeholderConvertFormSection');
    const choiceFooter = document.getElementById('placeholderChoiceFooter');
    const convertFooter = document.getElementById('placeholderConvertFooter');

    // Button elements
    const showConvertFormBtn = document.getElementById('showConvertFormBtn');
    const backToChoiceBtn = document.getElementById('backToChoiceBtn');
    const cancelConvertBtn = document.getElementById('cancelConvertBtn');
    const saveConvertBtn = document.getElementById('saveConvertBtn');

    // Form elements
    const convertEntryName = document.getElementById('convertEntryName');
    const convertEntryDescription = document.getElementById('convertEntryDescription');
    const convertEntryCuisineType = document.getElementById('convertEntryCuisineType');
    const convertEntryDishCategory = document.getElementById('convertEntryDishCategory');
    const convertEntryRegion = document.getElementById('convertEntryRegion');
    const convertEntryCulturalSignificance = document.getElementById('convertEntryCulturalSignificance');
    const convertEntryPopularExamples = document.getElementById('convertEntryPopularExamples');
    const convertEntryHistory = document.getElementById('convertEntryHistory');
    const convertFormError = document.getElementById('convertFormError');
    const convertFormSuccess = document.getElementById('convertFormSuccess');

    let currentPlaceholderId = null;
    let currentPlaceholderName = null;

    // Get CSRF token for API calls
    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
               document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
    }

    // Reset to choice view
    function resetToChoiceView() {
        choiceSection.style.display = 'block';
        formSection.style.display = 'none';
        choiceFooter.style.display = 'block';
        convertFooter.style.display = 'none';

        // Clear form
        convertEntryDescription.value = '';
        convertEntryCuisineType.value = '';
        convertEntryDishCategory.value = '';
        convertEntryRegion.value = '';
        convertEntryCulturalSignificance.value = '';
        convertEntryPopularExamples.value = '';
        convertEntryHistory.value = '';
        convertFormError.style.display = 'none';
        convertFormSuccess.style.display = 'none';
    }

    // Show convert form
    function showConvertForm() {
        choiceSection.style.display = 'none';
        formSection.style.display = 'block';
        choiceFooter.style.display = 'none';
        convertFooter.style.display = 'block';

        // Populate name field (readonly)
        convertEntryName.value = currentPlaceholderName;

        // Focus on description
        setTimeout(() => convertEntryDescription.focus(), 100);
    }

    // Attach click handlers to placeholder entries in Similar Dishes section
    function attachPlaceholderHandlers() {
        document.querySelectorAll('.encyclopedia-placeholder').forEach(element => {
            element.style.cursor = 'pointer';
            element.addEventListener('click', function(e) {
                // Prevent default link behavior
                e.preventDefault();

                currentPlaceholderId = this.dataset.placeholderId;
                currentPlaceholderName = this.dataset.placeholderName;

                // Update modal content
                placeholderNameSpan.textContent = currentPlaceholderName;

                // Reset to choice view
                resetToChoiceView();

                // Show modal
                modal.show();
            });
        });
    }

    // Initial attachment
    attachPlaceholderHandlers();

    // Handle "Create Full Entry" button
    showConvertFormBtn.addEventListener('click', showConvertForm);

    // Handle "Back" button
    backToChoiceBtn.addEventListener('click', resetToChoiceView);
    cancelConvertBtn.addEventListener('click', resetToChoiceView);

    // Handle "Edit in Admin" button
    editInAdminBtn.addEventListener('click', function() {
        if (!currentPlaceholderId) return;

        // Redirect to standard Django admin edit page
        const adminUrl = `/admin/content/encyclopedia/${currentPlaceholderId}/change/`;
        window.location.href = adminUrl;
    });

    // Handle "Save & Convert" button
    saveConvertBtn.addEventListener('click', async function() {
        if (!currentPlaceholderId) return;

        // Validate required field
        const description = convertEntryDescription.value.trim();
        if (!description) {
            convertFormError.textContent = 'Description is required to convert placeholder';
            convertFormError.style.display = 'block';
            convertEntryDescription.focus();
            return;
        }

        // Hide previous errors/success
        convertFormError.style.display = 'none';
        convertFormSuccess.style.display = 'none';

        // Disable button during save
        saveConvertBtn.disabled = true;
        saveConvertBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving...';

        try {
            // Get convert URL from modal data attribute
            const baseUrl = modalElement.dataset.convertUrl;
            const convertUrl = baseUrl.replace('/0/', `/${currentPlaceholderId}/`);

            // Prepare data
            const data = {
                description: description,
                cuisine_type: convertEntryCuisineType.value.trim(),
                dish_category: convertEntryDishCategory.value.trim(),
                region: convertEntryRegion.value.trim(),
                cultural_significance: convertEntryCulturalSignificance.value.trim(),
                popular_examples: convertEntryPopularExamples.value.trim(),
                history: convertEntryHistory.value.trim()
            };

            // Make API call
            const response = await fetch(convertUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Show success message
                convertFormSuccess.textContent = result.message || 'Placeholder successfully converted!';
                convertFormSuccess.style.display = 'block';

                // Reload page after short delay to show updated entry
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                // Show error message
                convertFormError.textContent = result.error || 'Failed to convert placeholder';
                convertFormError.style.display = 'block';

                // Re-enable button
                saveConvertBtn.disabled = false;
                saveConvertBtn.innerHTML = '<i class="bi bi-check-circle"></i> Save & Convert';
            }
        } catch (error) {
            console.error('Error converting placeholder:', error);
            convertFormError.textContent = 'An error occurred. Please try again.';
            convertFormError.style.display = 'block';

            // Re-enable button
            saveConvertBtn.disabled = false;
            saveConvertBtn.innerHTML = '<i class="bi bi-check-circle"></i> Save & Convert';
        }
    });

    // Reset state when modal is hidden
    modalElement.addEventListener('hidden.bs.modal', function() {
        currentPlaceholderId = null;
        currentPlaceholderName = null;
        placeholderNameSpan.textContent = '';
        resetToChoiceView();
    });
});
