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
    let restaurantSearchTimeout = null;

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

        // Set default date to today
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('reviewVisitDate').value = today;

        // Set default party size to 1
        document.getElementById('reviewPartySize').value = 1;

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
                    const partySize = parseInt(document.getElementById('reviewPartySize').value);

                    // Validate required fields
                    isValid = restaurantName !== '' && visitDate !== '';

                    // Validate date is not in future
                    if (visitDate) {
                        const selectedDate = new Date(visitDate);
                        const today = new Date();
                        today.setHours(0, 0, 0, 0); // Reset time for date-only comparison
                        if (selectedDate > today) {
                            isValid = false;
                        }
                    }

                    // Validate party size is positive
                    if (partySize < 1 || isNaN(partySize)) {
                        isValid = false;
                    }
                    break;

                case 'rating':
                    // Rating always has a value (slider defaults to 50)
                    isValid = true;
                    break;

                case 'dishes':
                    // At least one dish is required
                    // Save dishes first to ensure formData is up to date
                    saveDishes();
                    isValid = formData.dishes.length > 0;
                    console.log('Dishes validation - count:', formData.dishes.length, 'valid:', isValid);
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
                    partySize: document.getElementById('reviewPartySize').value,
                    entryTime: document.getElementById('reviewEntryTime').value.trim(),
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
                    title: document.getElementById('reviewTitle').value.trim(),
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
        console.log('goToNextStep called, currentStep:', currentStep);
        if (currentStep >= REVIEW_STEPS.length - 1) return;

        const step = REVIEW_STEPS[currentStep];
        console.log('Current step:', step.id, 'required:', step.required);

        // Validate if required
        const isValid = validateCurrentStep();
        console.log('Step is valid:', isValid);

        if (step.required && !isValid) {
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

        // Reset dish counter
        dishCounter = 0;

        // Clear all form fields
        document.getElementById('basicInfoForm').reset();
        document.getElementById('locationForm').reset();
        document.getElementById('ratingForm').reset();
        document.getElementById('dishesContainer').innerHTML = '';

        // Reset rating displays
        document.getElementById('ratingValue').textContent = '50';
        document.getElementById('ambianceValue').textContent = '50';
        document.getElementById('serviceValue').textContent = '50';

        // Reset title character count
        document.getElementById('titleCharCount').textContent = '0';

        // Clear restaurant search results
        document.getElementById('restaurantSearchResults').style.display = 'none';
        document.getElementById('restaurantSearchResults').innerHTML = '';
        document.getElementById('restaurantSearchStatus').textContent = '';

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
        if (formData.basicInfo.entryTime) {
            summaryHtml += `<p><strong>Time:</strong> ${formData.basicInfo.entryTime}</p>`;
        }
        summaryHtml += `<p><strong>Party Size:</strong> ${formData.basicInfo.partySize || '1'}</p>`;
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
        if (formData.rating.title) {
            summaryHtml += `<p><strong>Title:</strong> ${formData.rating.title}</p>`;
        }
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
    document.getElementById('reviewPartySize').addEventListener('input', validateCurrentStep);

    // Title character counter
    document.getElementById('reviewTitle').addEventListener('input', function() {
        const charCount = this.value.length;
        document.getElementById('titleCharCount').textContent = charCount;
    });

    // Restaurant search with debounce (300ms)
    const restaurantInput = document.getElementById('reviewRestaurantName');
    const restaurantResults = document.getElementById('restaurantSearchResults');
    const restaurantStatus = document.getElementById('restaurantSearchStatus');

    restaurantInput.addEventListener('input', function() {
        clearTimeout(restaurantSearchTimeout);
        const query = this.value.trim();

        if (query.length < 2) {
            restaurantResults.style.display = 'none';
            restaurantResults.innerHTML = '';
            restaurantStatus.textContent = query.length === 1 ? 'Type at least 2 characters to search' : '';
            validateCurrentStep();
            return;
        }

        restaurantStatus.textContent = 'Searching...';

        // Debounce with 300ms delay
        restaurantSearchTimeout = setTimeout(() => {
            performRestaurantSearch(query);
        }, 300);
    });

    function performRestaurantSearch(query) {
        fetch(`/api/restaurants/search/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                restaurantResults.innerHTML = '';

                if (data.results && data.results.length > 0) {
                    restaurantStatus.textContent = `${data.results.length} restaurant(s) found`;
                    restaurantResults.style.display = 'block';

                    data.results.forEach(restaurant => {
                        const item = document.createElement('a');
                        item.className = 'list-group-item list-group-item-action';
                        item.href = '#';
                        item.innerHTML = `
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    <strong>${restaurant.name}</strong>
                                    ${restaurant.location ? `<br><small class="text-muted">${restaurant.location}</small>` : ''}
                                </div>
                                <span class="badge bg-secondary">${restaurant.visit_count} visit(s)</span>
                            </div>
                        `;
                        item.addEventListener('click', (e) => {
                            e.preventDefault();
                            selectRestaurant(restaurant);
                        });
                        restaurantResults.appendChild(item);
                    });

                    // Add "Create new" option if no exact match
                    const createNewItem = document.createElement('a');
                    createNewItem.className = 'list-group-item list-group-item-action list-group-item-light';
                    createNewItem.href = '#';
                    createNewItem.innerHTML = `<i class="bi bi-plus-circle"></i> Create new: "${query}"`;
                    createNewItem.addEventListener('click', (e) => {
                        e.preventDefault();
                        selectRestaurant({ name: query, location: '' });
                    });
                    restaurantResults.appendChild(createNewItem);
                } else {
                    restaurantStatus.textContent = 'No restaurants found';
                    restaurantResults.style.display = 'block';
                    const createNewItem = document.createElement('a');
                    createNewItem.className = 'list-group-item list-group-item-action';
                    createNewItem.href = '#';
                    createNewItem.innerHTML = `<i class="bi bi-plus-circle"></i> Create new: "${query}"`;
                    createNewItem.addEventListener('click', (e) => {
                        e.preventDefault();
                        selectRestaurant({ name: query, location: '' });
                    });
                    restaurantResults.appendChild(createNewItem);
                }
            })
            .catch(error => {
                console.error('Restaurant search error:', error);
                restaurantStatus.textContent = 'Error searching restaurants';
                restaurantResults.style.display = 'none';
            });
    }

    function selectRestaurant(restaurant) {
        restaurantInput.value = restaurant.name;
        restaurantResults.style.display = 'none';
        restaurantResults.innerHTML = '';
        restaurantStatus.textContent = '';

        // Pre-fill location if available
        if (restaurant.location) {
            // Split location into city/country if possible
            const locationParts = restaurant.location.split(',').map(p => p.trim());
            if (locationParts.length >= 2) {
                document.getElementById('reviewCity').value = locationParts[0];
                document.getElementById('reviewCountry').value = locationParts[1];
            }
        }

        validateCurrentStep();
    }

    // Hide restaurant search results when clicking outside
    document.addEventListener('click', function(e) {
        if (!restaurantInput.contains(e.target) && !restaurantResults.contains(e.target)) {
            restaurantResults.style.display = 'none';
        }
    });

    // Keyboard navigation for restaurant search
    restaurantInput.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            restaurantResults.style.display = 'none';
        }
    });

    // Encyclopedia Search Modal
    const encyclopediaSearchModal = new bootstrap.Modal(document.getElementById('reviewEncyclopediaSearchModal'));
    const encyclopediaSearchInput = document.getElementById('reviewEncyclopediaSearch');
    const encyclopediaSearchResults = document.getElementById('reviewEncyclopediaSearchResults');
    const encyclopediaSearchStatus = document.getElementById('reviewEncyclopediaSearchStatus');
    let encyclopediaSearchTimeout = null;
    let currentDishCard = null;
    let encyclopediaSelectedIndex = -1;

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
        dishCard.dataset.encyclopediaIds = '[]'; // Store encyclopedia IDs as JSON

        // Pre-fill data if provided
        if (dishData) {
            dishCard.querySelector('.dish-name').value = dishData.name || '';
            dishCard.querySelector('.dish-rating').value = dishData.rating || 50;
            dishCard.querySelector('.dish-rating-value').textContent = dishData.rating || 50;
            dishCard.querySelector('.dish-notes').value = dishData.notes || '';

            // Pre-fill encyclopedia links if provided
            if (dishData.encyclopedia_ids && dishData.encyclopedia_ids.length > 0) {
                dishCard.dataset.encyclopediaIds = JSON.stringify(dishData.encyclopedia_ids);
                // Note: chips would need to be rendered if we had the encyclopedia data
            }
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
            console.log('Remove button clicked for dish:', dishCard.id);
            const name = dishCard.querySelector('.dish-name').value.trim();
            const notes = dishCard.querySelector('.dish-notes').value.trim();
            const previewImg = dishCard.querySelector('.dish-preview-img');
            const hasImage = previewImg && previewImg.src && previewImg.src.startsWith('data:');
            const hasData = name !== '' || notes !== '' || hasImage;

            console.log('Dish has data:', hasData, '(name:', name, 'notes:', notes, 'image:', hasImage, ')');

            if (hasData && !confirm('Remove this dish? All data for this dish will be lost.')) {
                console.log('User cancelled removal');
                return;
            }

            console.log('Removing dish...');
            dishCard.remove();
            updateDishNumbers();
            saveDishes();
            validateCurrentStep();
        });

        // Encyclopedia link button
        dishCard.querySelector('.link-encyclopedia-btn').addEventListener('click', function() {
            openEncyclopediaSearch(dishCard);
        });

        // Reorder buttons
        dishCard.querySelector('.move-up-btn').addEventListener('click', function() {
            moveDishUp(dishCard);
        });

        dishCard.querySelector('.move-down-btn').addEventListener('click', function() {
            moveDishDown(dishCard);
        });

        // Image upload handler with validation
        const imageInput = dishCard.querySelector('.dish-image');
        const imageDropZone = dishCard.querySelector('.dish-image-drop-zone');
        const imagePreview = dishCard.querySelector('.dish-image-preview');
        const previewImg = dishCard.querySelector('.dish-preview-img');
        const removeImageBtn = dishCard.querySelector('.remove-image-btn');

        imageInput.addEventListener('change', function(e) {
            handleImageFile(e.target.files[0], dishCard);
        });

        // Drag & drop support
        imageDropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
            imageDropZone.classList.add('drag-over');
        });

        imageDropZone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            e.stopPropagation();
            imageDropZone.classList.remove('drag-over');
        });

        imageDropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            imageDropZone.classList.remove('drag-over');

            const file = e.dataTransfer.files[0];
            if (file) {
                handleImageFile(file, dishCard);
            }
        });

        removeImageBtn.addEventListener('click', function() {
            imageInput.value = '';
            previewImg.src = '';
            imagePreview.style.display = 'none';
            imageDropZone.style.display = 'block';
            saveDishes();
        });

        // Update dish numbers after adding to container
        updateDishNumbers();

        // Save dishes and focus on name field
        saveDishes();
        validateCurrentStep();

        setTimeout(() => {
            dishCard.querySelector('.dish-name').focus();
        }, 100);
    }

    function handleImageFile(file, dishCard) {
        if (!file) return;

        const imageInput = dishCard.querySelector('.dish-image');
        const imageDropZone = dishCard.querySelector('.dish-image-drop-zone');
        const imagePreview = dishCard.querySelector('.dish-image-preview');
        const previewImg = dishCard.querySelector('.dish-preview-img');

        // Validate file type
        const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            showError('Invalid file type. Please select a JPEG, PNG, or WebP image.');
            return;
        }

        // Validate file size (10MB max)
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            showError('File is too large. Maximum size is 10MB.');
            return;
        }

        // Clear any errors
        hideError();

        // Read and preview image
        const reader = new FileReader();
        reader.onload = function(e) {
            previewImg.src = e.target.result;
            imagePreview.style.display = 'block';
            imageDropZone.style.display = 'none';
            saveDishes();
        };
        reader.readAsDataURL(file);
    }

    function updateDishNumbers() {
        const dishCards = document.querySelectorAll('.dish-card:not(#dishFormTemplate)');
        dishCards.forEach((card, index) => {
            card.querySelector('.dish-number').textContent = index + 1;
        });
    }

    function moveDishUp(dishCard) {
        const prevCard = dishCard.previousElementSibling;
        if (prevCard && prevCard.id !== 'dishFormTemplate') {
            dishCard.parentNode.insertBefore(dishCard, prevCard);
            updateDishNumbers();
            saveDishes();
        }
    }

    function moveDishDown(dishCard) {
        const nextCard = dishCard.nextElementSibling;
        if (nextCard) {
            dishCard.parentNode.insertBefore(nextCard, dishCard);
            updateDishNumbers();
            saveDishes();
        }
    }

    function saveDishes() {
        formData.dishes = [];

        document.querySelectorAll('.dish-card').forEach(card => {
            if (card.id !== 'dishFormTemplate' && card.style.display !== 'none') {
                const name = card.querySelector('.dish-name').value.trim();
                const rating = card.querySelector('.dish-rating').value;
                const notes = card.querySelector('.dish-notes').value.trim();
                const imagePreview = card.querySelector('.dish-preview-img');
                const imageSrc = imagePreview && imagePreview.src && imagePreview.src.startsWith('data:') ? imagePreview.src : null;
                const encyclopediaIds = JSON.parse(card.dataset.encyclopediaIds || '[]');

                if (name) { // Only save dishes with a name
                    formData.dishes.push({
                        name,
                        rating,
                        notes,
                        image: imageSrc,
                        encyclopedia_ids: encyclopediaIds
                    });
                }
            }
        });

        console.log('Dishes saved:', formData.dishes.length);
    }

    // Encyclopedia Search Functions
    function openEncyclopediaSearch(dishCard) {
        currentDishCard = dishCard;
        encyclopediaSearchInput.value = '';
        encyclopediaSearchResults.innerHTML = '';
        encyclopediaSearchStatus.style.display = 'none';
        encyclopediaSelectedIndex = -1;

        // Show modal
        encyclopediaSearchModal.show();

        // Focus on search input
        setTimeout(() => encyclopediaSearchInput.focus(), 100);
    }

    // Debounced encyclopedia search
    encyclopediaSearchInput.addEventListener('input', function() {
        clearTimeout(encyclopediaSearchTimeout);
        const query = this.value.trim();

        if (query.length < 2) {
            encyclopediaSearchResults.innerHTML = '';
            encyclopediaSearchStatus.style.display = 'block';
            encyclopediaSearchStatus.innerHTML = '<em>Type at least 2 characters to search</em>';
            return;
        }

        encyclopediaSearchStatus.style.display = 'block';
        encyclopediaSearchStatus.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">Loading...</span></div> Searching...';

        encyclopediaSearchTimeout = setTimeout(() => performEncyclopediaSearch(query), 300);
    });

    // Keyboard navigation for encyclopedia search
    encyclopediaSearchInput.addEventListener('keydown', function(e) {
        const items = encyclopediaSearchResults.querySelectorAll('.list-group-item');

        if (e.key === 'Escape') {
            encyclopediaSearchModal.hide();
            return;
        }

        if (items.length === 0) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            encyclopediaSelectedIndex = Math.min(encyclopediaSelectedIndex + 1, items.length - 1);
            updateEncyclopediaSelection(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            encyclopediaSelectedIndex = Math.max(encyclopediaSelectedIndex - 1, -1);
            updateEncyclopediaSelection(items);
        } else if (e.key === 'Enter' && encyclopediaSelectedIndex >= 0) {
            e.preventDefault();
            items[encyclopediaSelectedIndex].click();
        }
    });

    function updateEncyclopediaSelection(items) {
        items.forEach((item, index) => {
            if (index === encyclopediaSelectedIndex) {
                item.classList.add('active');
                item.scrollIntoView({ block: 'nearest' });
            } else {
                item.classList.remove('active');
            }
        });
    }

    function performEncyclopediaSearch(query) {
        fetch(`/api/encyclopedia/search/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                encyclopediaSearchStatus.style.display = 'none';

                if (data.results.length === 0) {
                    encyclopediaSearchResults.innerHTML = '';
                    encyclopediaSearchStatus.style.display = 'block';
                    encyclopediaSearchStatus.innerHTML = '<em>No results found</em>';
                    return;
                }

                encyclopediaSelectedIndex = -1;
                encyclopediaSearchResults.innerHTML = data.results.map(entry => `
                    <button type="button" class="list-group-item list-group-item-action encyclopedia-search-result"
                            data-entry-id="${entry.id}"
                            data-entry-name="${entry.name}"
                            data-entry-slug="${entry.slug || ''}">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">${entry.name}</h6>
                            ${entry.cuisine_type ? `<small class="badge bg-info">${entry.cuisine_type}</small>` : ''}
                        </div>
                        ${entry.hierarchy ? `<small class="text-muted"><i class="bi bi-arrow-right-short"></i> ${entry.hierarchy}</small>` : ''}
                        ${entry.dish_category ? `<small class="badge bg-secondary ms-2">${entry.dish_category}</small>` : ''}
                    </button>
                `).join('');

                // Add click handlers to results
                document.querySelectorAll('.encyclopedia-search-result').forEach(item => {
                    item.addEventListener('click', function() {
                        addEncyclopediaLink(
                            currentDishCard,
                            this.dataset.entryId,
                            this.dataset.entryName,
                            this.dataset.entrySlug
                        );
                    });
                });
            })
            .catch(error => {
                console.error('Encyclopedia search error:', error);
                encyclopediaSearchStatus.style.display = 'block';
                encyclopediaSearchStatus.innerHTML = '<em class="text-danger">Error performing search</em>';
            });
    }

    function addEncyclopediaLink(dishCard, entryId, entryName, entrySlug) {
        // Get current encyclopedia IDs
        const currentIds = JSON.parse(dishCard.dataset.encyclopediaIds || '[]');

        // Check if already linked
        const existingLink = currentIds.find(link => link.id === entryId);
        if (existingLink) {
            // Already linked, just close modal
            encyclopediaSearchModal.hide();
            return;
        }

        // Add new link
        currentIds.push({
            id: entryId,
            name: entryName,
            slug: entrySlug
        });

        // Update dataset
        dishCard.dataset.encyclopediaIds = JSON.stringify(currentIds);

        // Render chips
        renderEncyclopediaChips(dishCard);

        // Save dishes
        saveDishes();

        // Clear search and close modal
        encyclopediaSearchInput.value = '';
        encyclopediaSearchModal.hide();
    }

    function removeEncyclopediaLink(dishCard, entryId) {
        // Get current encyclopedia IDs
        let currentIds = JSON.parse(dishCard.dataset.encyclopediaIds || '[]');

        // Remove the entry
        currentIds = currentIds.filter(link => link.id !== entryId);

        // Update dataset
        dishCard.dataset.encyclopediaIds = JSON.stringify(currentIds);

        // Render chips
        renderEncyclopediaChips(dishCard);

        // Save dishes
        saveDishes();
    }

    function renderEncyclopediaChips(dishCard) {
        const chipsContainer = dishCard.querySelector('.encyclopedia-chips');
        const chipsDiv = chipsContainer.querySelector('.d-flex');
        const encyclopediaIds = JSON.parse(dishCard.dataset.encyclopediaIds || '[]');

        if (encyclopediaIds.length === 0) {
            chipsContainer.style.display = 'none';
            return;
        }

        chipsContainer.style.display = 'block';
        chipsDiv.innerHTML = encyclopediaIds.map(link => `
            <span class="badge bg-primary d-flex align-items-center gap-1" style="font-size: 0.85rem; padding: 0.4rem 0.6rem;">
                <i class="bi bi-book"></i>
                ${link.name}
                <button type="button" class="btn-close btn-close-white"
                        data-remove-encyclopedia-id="${link.id}"
                        style="font-size: 0.5rem;"
                        aria-label="Remove"></button>
            </span>
        `).join('');

        // Add click handlers to remove buttons
        chipsDiv.querySelectorAll('[data-remove-encyclopedia-id]').forEach(btn => {
            btn.addEventListener('click', function() {
                const idToRemove = this.dataset.removeEncyclopediaId;
                removeEncyclopediaLink(dishCard, idToRemove);
            });
        });
    }

    // Reset encyclopedia search modal on close
    document.getElementById('reviewEncyclopediaSearchModal').addEventListener('hidden.bs.modal', function() {
        encyclopediaSearchInput.value = '';
        encyclopediaSearchResults.innerHTML = '';
        encyclopediaSearchStatus.style.display = 'none';
        currentDishCard = null;
        encyclopediaSelectedIndex = -1;
    });
});
