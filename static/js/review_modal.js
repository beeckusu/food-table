// Review Modal JavaScript
// Handles multi-step review creation workflow

document.addEventListener('DOMContentLoaded', function() {
    const modalElement = document.getElementById('reviewModal');
    if (!modalElement) return; // Modal not present (user not authenticated)

    const modal = new bootstrap.Modal(modalElement);

    // UI Elements
    const stepIndicator = document.getElementById('reviewStepIndicator');
    const progressBar = document.getElementById('reviewProgressBar');
    const backBtn = document.getElementById('reviewBackBtn');
    const skipBtn = document.getElementById('reviewSkipBtn');
    const nextBtn = document.getElementById('reviewNextBtn');
    const cancelBtn = document.getElementById('reviewCancelBtn');
    const submitBtn = document.getElementById('reviewSubmitBtn');
    const errorDiv = document.getElementById('reviewFormError');

    // Step configuration
    const REVIEW_STEPS = [
        { id: 'basic-info', title: 'Basic Information', required: true },
        { id: 'location', title: 'Location', required: false },
        { id: 'rating', title: 'Rating & Notes', required: true },
        { id: 'dishes', title: 'Dishes', required: true },
        { id: 'confirm', title: 'Review & Confirm', required: true }
    ];

    // State management
    let currentStep = 0;
    let formData = {
        basicInfo: {},
        location: {},
        rating: {},
        dishes: []
    };
    let hasUnsavedChanges = false;

    // Initialize modal trigger
    const openModalBtn = document.getElementById('openReviewModal');
    if (openModalBtn) {
        openModalBtn.addEventListener('click', function() {
            openModal();
        });
    }

    // Open modal
    function openModal() {
        currentStep = 0;
        formData = {
            basicInfo: {},
            location: {},
            rating: {},
            dishes: []
        };
        hasUnsavedChanges = false;
        showStep(currentStep);
        modal.show();
    }

    // Show specific step
    function showStep(stepIndex) {
        // Hide all steps
        document.querySelectorAll('.review-step').forEach(step => {
            step.style.display = 'none';
        });

        // Show current step
        const stepElement = document.getElementById(`step-${REVIEW_STEPS[stepIndex].id}`);
        if (stepElement) {
            stepElement.style.display = 'block';
        }

        // Update progress indicator
        const stepNumber = stepIndex + 1;
        const totalSteps = REVIEW_STEPS.length;
        const progressPercent = (stepNumber / totalSteps) * 100;

        stepIndicator.textContent = `Step ${stepNumber} of ${totalSteps}`;
        progressBar.style.width = `${progressPercent}%`;
        progressBar.setAttribute('aria-valuenow', progressPercent);

        // Update navigation buttons
        updateNavigationButtons();

        // Focus management
        setTimeout(() => {
            const firstInput = stepElement.querySelector('input, textarea, select');
            if (firstInput) {
                firstInput.focus();
            }
        }, 100);
    }

    // Update navigation button visibility and state
    function updateNavigationButtons() {
        const step = REVIEW_STEPS[currentStep];
        const isFirstStep = currentStep === 0;
        const isLastStep = currentStep === REVIEW_STEPS.length - 1;
        const isOptionalStep = !step.required;

        // Back button
        backBtn.style.display = isFirstStep ? 'none' : 'inline-block';

        // Skip button
        skipBtn.style.display = isOptionalStep && !isLastStep ? 'inline-block' : 'none';

        // Next button
        nextBtn.style.display = isLastStep ? 'none' : 'inline-block';

        // Submit button
        submitBtn.style.display = isLastStep ? 'inline-block' : 'none';

        // Validate current step and enable/disable next button
        validateCurrentStep();
    }

    // Validate current step
    function validateCurrentStep() {
        const step = REVIEW_STEPS[currentStep];
        let isValid = true;

        if (step.required) {
            switch (step.id) {
                case 'basic-info':
                    const restaurantName = document.getElementById('reviewRestaurantName').value.trim();
                    const visitDate = document.getElementById('reviewVisitDate').value.trim();
                    isValid = restaurantName !== '' && visitDate !== '';
                    break;

                case 'rating':
                    // Rating always has a value (slider defaults to 50)
                    isValid = true;
                    break;

                case 'dishes':
                    // At least one dish is required
                    isValid = formData.dishes.length > 0;
                    break;

                case 'confirm':
                    isValid = true;
                    break;
            }
        }

        // Update next button state
        if (nextBtn.style.display !== 'none') {
            nextBtn.disabled = !isValid && step.required;
        }

        return isValid;
    }

    // Save current step data
    function saveCurrentStepData() {
        const step = REVIEW_STEPS[currentStep];
        hasUnsavedChanges = true;

        switch (step.id) {
            case 'basic-info':
                formData.basicInfo = {
                    restaurantName: document.getElementById('reviewRestaurantName').value.trim(),
                    visitDate: document.getElementById('reviewVisitDate').value.trim(),
                    mealType: document.getElementById('reviewMealType').value
                };
                break;

            case 'location':
                formData.location = {
                    address: document.getElementById('reviewAddress').value.trim(),
                    city: document.getElementById('reviewCity').value.trim(),
                    country: document.getElementById('reviewCountry').value.trim(),
                    neighborhood: document.getElementById('reviewNeighborhood').value.trim()
                };
                break;

            case 'rating':
                formData.rating = {
                    overall: document.getElementById('reviewOverallRating').value,
                    notes: document.getElementById('reviewNotes').value.trim(),
                    ambiance: document.getElementById('reviewAmbiance').value,
                    service: document.getElementById('reviewService').value
                };
                break;

            case 'dishes':
                // Dishes are saved in real-time via dish card handlers
                break;
        }
    }

    // Go to next step
    function goToNextStep() {
        if (currentStep >= REVIEW_STEPS.length - 1) return;

        const step = REVIEW_STEPS[currentStep];

        // Validate if required
        if (step.required && !validateCurrentStep()) {
            showError('Please fill in all required fields before continuing.');
            return;
        }

        // Save current step data
        saveCurrentStepData();

        // Clear any errors
        hideError();

        // Move to next step
        currentStep++;

        // If we're moving to the confirm step, populate the summary
        if (REVIEW_STEPS[currentStep].id === 'confirm') {
            populateReviewSummary();
        }

        showStep(currentStep);
    }

    // Go to previous step
    function goToPreviousStep() {
        if (currentStep <= 0) return;

        // Save current step data (don't validate)
        saveCurrentStepData();

        // Clear any errors
        hideError();

        // Move to previous step
        currentStep--;
        showStep(currentStep);
    }

    // Skip step (only for optional steps)
    function skipStep() {
        const step = REVIEW_STEPS[currentStep];
        if (step.required) return;

        // Don't save data for skipped steps
        currentStep++;

        // If we're moving to the confirm step, populate the summary
        if (REVIEW_STEPS[currentStep].id === 'confirm') {
            populateReviewSummary();
        }

        showStep(currentStep);
    }

    // Close modal with confirmation
    function closeModal() {
        if (hasUnsavedChanges) {
            if (confirm('You have unsaved changes. Are you sure you want to close?')) {
                modal.hide();
                resetModal();
            }
        } else {
            modal.hide();
            resetModal();
        }
    }

    // Reset modal to initial state
    function resetModal() {
        currentStep = 0;
        formData = {
            basicInfo: {},
            location: {},
            rating: {},
            dishes: []
        };
        hasUnsavedChanges = false;

        // Clear all form fields
        document.getElementById('basicInfoForm').reset();
        document.getElementById('locationForm').reset();
        document.getElementById('ratingForm').reset();
        document.getElementById('dishesContainer').innerHTML = '';

        // Reset rating displays
        document.getElementById('ratingValue').textContent = '50';
        document.getElementById('ambianceValue').textContent = '50';
        document.getElementById('serviceValue').textContent = '50';

        hideError();
    }

    // Populate review summary
    function populateReviewSummary() {
        const summaryDiv = document.getElementById('reviewSummary');

        let summaryHtml = '<div class="card">';
        summaryHtml += '<div class="card-body">';

        // Basic Info
        summaryHtml += '<h6 class="border-bottom pb-2 mb-3">Basic Information</h6>';
        summaryHtml += `<p><strong>Restaurant:</strong> ${formData.basicInfo.restaurantName || 'N/A'}</p>`;
        summaryHtml += `<p><strong>Visit Date:</strong> ${formData.basicInfo.visitDate || 'N/A'}</p>`;
        summaryHtml += `<p><strong>Meal Type:</strong> ${formData.basicInfo.mealType || 'Not specified'}</p>`;

        // Location (if provided)
        if (formData.location.address || formData.location.city || formData.location.country) {
            summaryHtml += '<h6 class="border-bottom pb-2 mb-3 mt-4">Location</h6>';
            if (formData.location.address) summaryHtml += `<p><strong>Address:</strong> ${formData.location.address}</p>`;
            if (formData.location.city) summaryHtml += `<p><strong>City:</strong> ${formData.location.city}</p>`;
            if (formData.location.country) summaryHtml += `<p><strong>Country:</strong> ${formData.location.country}</p>`;
            if (formData.location.neighborhood) summaryHtml += `<p><strong>Neighborhood:</strong> ${formData.location.neighborhood}</p>`;
        }

        // Rating
        summaryHtml += '<h6 class="border-bottom pb-2 mb-3 mt-4">Rating & Notes</h6>';
        summaryHtml += `<p><strong>Overall Rating:</strong> <span class="badge bg-primary">${formData.rating.overall}</span></p>`;
        summaryHtml += `<p><strong>Ambiance:</strong> <span class="badge bg-secondary">${formData.rating.ambiance}</span></p>`;
        summaryHtml += `<p><strong>Service:</strong> <span class="badge bg-secondary">${formData.rating.service}</span></p>`;
        if (formData.rating.notes) {
            summaryHtml += `<p><strong>Notes:</strong><br>${formData.rating.notes}</p>`;
        }

        // Dishes
        summaryHtml += '<h6 class="border-bottom pb-2 mb-3 mt-4">Dishes</h6>';
        if (formData.dishes.length > 0) {
            formData.dishes.forEach((dish, index) => {
                summaryHtml += `<div class="mb-3 dish-summary-item">`;
                if (dish.image) {
                    summaryHtml += `<img src="${dish.image}" alt="${dish.name}" class="dish-summary-image mb-2">`;
                }
                summaryHtml += `<div><strong>${index + 1}. ${dish.name}</strong> - <span class="badge bg-primary">${dish.rating}</span></div>`;
                if (dish.notes) {
                    summaryHtml += `<small class="text-muted">${dish.notes}</small>`;
                }
                summaryHtml += `</div>`;
            });
        } else {
            summaryHtml += '<p class="text-muted">No dishes added</p>';
        }

        summaryHtml += '</div>';
        summaryHtml += '</div>';

        summaryDiv.innerHTML = summaryHtml;
    }

    // Submit review
    function submitReview() {
        // Save final step data
        saveCurrentStepData();

        // Disable submit button
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Submitting...';

        // In a real implementation, this would send data to the server
        // For now, we'll just simulate a submission
        console.log('Submitting review:', formData);

        // Simulate API call
        setTimeout(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-check-circle"></i> Submit Review';

            // Show success and close modal
            alert('Review submitted successfully! (This is a placeholder - actual implementation will save to server)');
            modal.hide();
            resetModal();
        }, 1500);
    }

    // Error handling
    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function hideError() {
        errorDiv.style.display = 'none';
        errorDiv.textContent = '';
    }

    // Event listeners - Navigation buttons
    nextBtn.addEventListener('click', goToNextStep);
    backBtn.addEventListener('click', goToPreviousStep);
    skipBtn.addEventListener('click', skipStep);
    cancelBtn.addEventListener('click', closeModal);
    submitBtn.addEventListener('click', submitReview);

    // Modal close event
    modalElement.addEventListener('hidden.bs.modal', function() {
        resetModal();
    });

    // Keyboard shortcuts
    modalElement.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        } else if (e.key === 'Enter' && e.ctrlKey) {
            // Ctrl+Enter to advance
            if (nextBtn.style.display !== 'none' && !nextBtn.disabled) {
                goToNextStep();
            } else if (submitBtn.style.display !== 'none' && !submitBtn.disabled) {
                submitReview();
            }
        }
    });

    // Rating sliders - Update display values
    document.getElementById('reviewOverallRating').addEventListener('input', function() {
        document.getElementById('ratingValue').textContent = this.value;
        validateCurrentStep();
    });

    document.getElementById('reviewAmbiance').addEventListener('input', function() {
        document.getElementById('ambianceValue').textContent = this.value;
    });

    document.getElementById('reviewService').addEventListener('input', function() {
        document.getElementById('serviceValue').textContent = this.value;
    });

    // Form input validation listeners
    document.getElementById('reviewRestaurantName').addEventListener('input', validateCurrentStep);
    document.getElementById('reviewVisitDate').addEventListener('input', validateCurrentStep);

    // Dish management
    let dishCounter = 0;

    document.getElementById('addDishBtn').addEventListener('click', function() {
        addDish();
    });

    function addDish(dishData = null) {
        dishCounter++;

        const template = document.getElementById('dishFormTemplate');
        const dishCard = template.cloneNode(true);
        dishCard.style.display = 'block';
        dishCard.id = `dish-${dishCounter}`;
        dishCard.dataset.dishId = dishCounter;

        // Update dish number
        dishCard.querySelector('.dish-number').textContent = dishCounter;

        // Pre-fill data if provided
        if (dishData) {
            dishCard.querySelector('.dish-name').value = dishData.name || '';
            dishCard.querySelector('.dish-rating').value = dishData.rating || 50;
            dishCard.querySelector('.dish-rating-value').textContent = dishData.rating || 50;
            dishCard.querySelector('.dish-notes').value = dishData.notes || '';
        }

        // Add to container
        document.getElementById('dishesContainer').appendChild(dishCard);

        // Attach event listeners
        const ratingSlider = dishCard.querySelector('.dish-rating');
        const ratingValue = dishCard.querySelector('.dish-rating-value');

        ratingSlider.addEventListener('input', function() {
            ratingValue.textContent = this.value;
            saveDishes();
        });

        dishCard.querySelector('.dish-name').addEventListener('input', function() {
            saveDishes();
            validateCurrentStep();
        });

        dishCard.querySelector('.dish-notes').addEventListener('input', function() {
            saveDishes();
        });

        dishCard.querySelector('.remove-dish-btn').addEventListener('click', function() {
            dishCard.remove();
            saveDishes();
            validateCurrentStep();
        });

        // Image upload handler
        const imageInput = dishCard.querySelector('.dish-image');
        const imagePreview = dishCard.querySelector('.dish-image-preview');
        const previewImg = dishCard.querySelector('.dish-preview-img');
        const removeImageBtn = dishCard.querySelector('.remove-image-btn');

        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImg.src = e.target.result;
                    imagePreview.style.display = 'block';
                    imageInput.style.display = 'none';
                    saveDishes();
                };
                reader.readAsDataURL(file);
            }
        });

        removeImageBtn.addEventListener('click', function() {
            imageInput.value = '';
            previewImg.src = '';
            imagePreview.style.display = 'none';
            imageInput.style.display = 'block';
            saveDishes();
        });

        // Save dishes
        saveDishes();
        validateCurrentStep();
    }

    function saveDishes() {
        formData.dishes = [];

        document.querySelectorAll('.dish-card').forEach(card => {
            if (card.id !== 'dishFormTemplate') {
                const name = card.querySelector('.dish-name').value.trim();
                const rating = card.querySelector('.dish-rating').value;
                const notes = card.querySelector('.dish-notes').value.trim();
                const imagePreview = card.querySelector('.dish-preview-img');
                const imageSrc = imagePreview && imagePreview.src ? imagePreview.src : null;

                if (name) { // Only save dishes with a name
                    formData.dishes.push({ name, rating, notes, image: imageSrc });
                }
            }
        });
    }
});
