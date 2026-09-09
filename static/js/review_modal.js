// Review Modal JavaScript
// Handles multi-step review creation and editing workflow

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
    const saveDraftBtn = document.getElementById('reviewSaveDraftBtn');
    const errorDiv = document.getElementById('reviewFormError');

    // Step configuration
    const REVIEW_STEPS = [
        { id: 'basic-info', title: 'Basic Information', required: true },
        { id: 'rating', title: 'Rating & Notes', required: true },
        { id: 'dishes', title: 'Dishes', required: true },
        { id: 'confirm', title: 'Review & Confirm', required: true }
    ];

    // State management
    let currentStep = 0;
    let formData = {
        basicInfo: {},
        restaurant: {},
        food_festival: {},
        rating: {},
        dishes: []
    };
    let hasUnsavedChanges = false;
    let restaurantSearchTimeout = null;
    let foodFestivalSearchTimeout = null;

    // Editing an existing review (set by openModalForEdit); null means create mode
    let editingReviewId = null;

    // What the review is about: 'restaurant' or 'food_festival'
    let targetType = 'restaurant';

    // Restaurant picker mode: 'search' (pick existing) or 'new' (create restaurant)
    let restaurantMode = 'search';

    // Food festival picker mode: 'search' (pick existing) or 'new' (create food festival)
    let foodFestivalMode = 'search';

    // Google Places autocomplete for "new restaurant" address fields (top-level and per-dish)
    const MAPS_API_KEY = window.REVIEW_MAPS_API_KEY || '';
    let mapsScriptLoaded = false;
    let pendingPlaceInits = []; // {el, onPlaceSelected} pairs queued while the Maps script loads
    const placesAutocompleteInstances = new WeakMap(); // el -> google.maps.places.Autocomplete
    let placesSessionUsed = false;

    // Quill editor for review notes — initialized lazily when Step 3 becomes visible
    let reviewNotesQuill = null;

    // Review-level images ({id, src} objects; id is null for newly-added images), populated on the rating step
    let reviewImages = [];
    let reviewImageHandlersInitialized = false;

    // Bulk dish-photo drop zone (Step 3) — initialized lazily, once, like the review image handlers
    let bulkDishHandlersInitialized = false;

    // AI rewrite — populated once the modal element is found
    let openAiRewriteModal = null;

    // Draft manager (only used in create mode — edits skip drafts entirely)
    const draftManager = new ReviewDraftManager();

    // Initialize modal trigger
    const openModalBtn = document.getElementById('openReviewModal');
    if (openModalBtn) {
        openModalBtn.addEventListener('click', function() {
            openModal();
        });
    }

    // Open modal for edit (triggered by elements with class "review-edit-trigger" and data-review-id)
    document.addEventListener('click', function(e) {
        const trigger = e.target.closest('.review-edit-trigger');
        if (trigger && trigger.dataset.reviewId) {
            e.preventDefault();
            openModalForEdit(trigger.dataset.reviewId);
        }
    });

    // Open modal (create mode)
    async function openModal() {
        editingReviewId = null;
        document.getElementById('reviewModalLabel').textContent = 'Create New Review';

        // Check for existing drafts
        const draft = await draftManager.init();

        if (draft) {
            populateFormFields(draft.data);
            currentStep = REVIEW_STEPS.findIndex(s => s.id === draft.step);
            if (currentStep === -1) currentStep = 0;
        } else {
            // Start fresh
            currentStep = 0;
            formData = {
                basicInfo: {},
                restaurant: {},
                food_festival: {},
                rating: {},
                dishes: []
            };
            hasUnsavedChanges = false;
            targetType = 'restaurant';
            restaurantMode = 'search';
            foodFestivalMode = 'search';
            placesSessionUsed = false;
            applyTargetTypeUI();

            // Set default date to today
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('reviewVisitDate').value = today;

            // Set default party size to 1
            document.getElementById('reviewPartySize').value = 1;
        }

        // Start autosave
        draftManager.startAutosave(
            () => REVIEW_STEPS[currentStep].id,
            () => formData
        );

        showStep(currentStep);
        modal.show();
    }

    // Open modal for editing an existing review
    async function openModalForEdit(reviewId) {
        editingReviewId = reviewId;
        currentStep = 0;
        formData = {
            basicInfo: {},
            restaurant: {},
            food_festival: {},
            rating: {},
            dishes: []
        };
        hasUnsavedChanges = false;
        targetType = 'restaurant';
        restaurantMode = 'search';
        foodFestivalMode = 'search';
        placesSessionUsed = false;
        dishCounter = 0;
        groupCounter = 0;
        applyTargetTypeUI();

        document.getElementById('reviewModalLabel').textContent = 'Edit Review';
        document.getElementById('dishesContainer').innerHTML = '';
        document.getElementById('festivalGroupsContainer').innerHTML = '';

        showStep(currentStep);
        modal.show();

        try {
            const response = await fetch(`/api/reviews/${reviewId}/edit-data/`);
            const data = await response.json();
            if (!data.success) {
                showError(data.error || 'Failed to load review data.');
                return;
            }
            populateFormFields(data.review);
            validateCurrentStep();
        } catch (error) {
            console.error('Error loading review for edit:', error);
            showError('Network error while loading review data.');
        }
    }

    // Populate all form fields from a formData-shaped object (draft restore or edit load)
    function populateFormFields(data) {
        formData = data;

        if (formData.basicInfo) {
            document.getElementById('reviewVisitDate').value = formData.basicInfo.visitDate || '';
            document.getElementById('reviewPartySize').value = formData.basicInfo.partySize || 1;
            document.getElementById('reviewEntryTime').value = formData.basicInfo.entryTime || '';
        }

        targetType = formData.targetType || 'restaurant';
        applyTargetTypeUI();

        if (targetType === 'food_festival' && formData.food_festival) {
            const f = formData.food_festival;
            if (f.mode === 'new') {
                switchToNewFoodFestivalMode();
                document.getElementById('reviewNewFoodFestivalName').value = f.name || '';
                document.getElementById('reviewNewFoodFestivalCity').value = f.city || '';
                document.getElementById('reviewNewFoodFestivalCountry').value = f.country || '';
                document.getElementById('reviewNewFoodFestivalStartDate').value = f.startDate || '';
                document.getElementById('reviewNewFoodFestivalEndDate').value = f.endDate || '';
                document.getElementById('reviewNewFoodFestivalWebsite').value = f.website || '';
            } else {
                switchToSearchFoodFestivalMode();
                document.getElementById('reviewFoodFestivalName').value = f.name || '';
                document.getElementById('reviewFoodFestivalId').value = f.id || '';
            }
        } else if (formData.restaurant) {
            const r = formData.restaurant;
            if (r.mode === 'new') {
                switchToNewRestaurantMode();
                document.getElementById('reviewNewRestaurantName').value = r.name || '';
                document.getElementById('reviewNewIsPopUp').checked = !!r.isPopUp;
                document.getElementById('reviewNewWebsite').value = r.website || '';
                document.getElementById('reviewAddress').value = r.address || '';
                document.getElementById('reviewCity').value = r.city || '';
                document.getElementById('reviewProvince').value = r.province || '';
                document.getElementById('reviewCountry').value = r.country || '';
                document.getElementById('reviewPostalCode').value = r.postalCode || '';
                document.getElementById('reviewNewPlaceId').value = r.googlePlaceId || '';
                document.getElementById('reviewNewWebsiteSection').style.display = r.isPopUp ? 'block' : 'none';
                document.getElementById('reviewNewAddressSection').style.display = r.isPopUp ? 'none' : 'block';
            } else {
                switchToSearchRestaurantMode();
                document.getElementById('reviewRestaurantName').value = r.name || '';
                document.getElementById('reviewRestaurantId').value = r.id || '';
            }
        }

        // Restore rating
        if (formData.rating) {
            document.getElementById('reviewOverallRating').value = formData.rating.overall ?? 50;
            document.getElementById('ratingValue').textContent = formData.rating.overall ?? 50;
            document.getElementById('reviewTitle').value = formData.rating.title || '';
            document.getElementById('reviewNotes').value = formData.rating.notes || '';
            document.getElementById('reviewAmbiance').value = formData.rating.ambiance ?? 50;
            document.getElementById('ambianceValue').textContent = formData.rating.ambiance ?? 50;
            document.getElementById('reviewService').value = formData.rating.service ?? 50;
            document.getElementById('serviceValue').textContent = formData.rating.service ?? 50;

            // Update character count
            const titleLength = (formData.rating.title || '').length;
            document.getElementById('titleCharCount').textContent = titleLength;

            // Restore review images
            reviewImages = (formData.rating.images || []).map(
                img => (typeof img === 'string' ? { id: null, src: img } : img)
            );
            renderReviewImagePreviews();
        }

        // Restore dishes
        if (formData.dishes && formData.dishes.length > 0) {
            if (targetType === 'food_festival') {
                groupDishesByRestaurant(formData.dishes).forEach(group => {
                    addRestaurantGroup(group.restaurant, group.dishes);
                });
            } else {
                formData.dishes.forEach(dishData => {
                    addDish(dishData);
                });
            }
        }

        hasUnsavedChanges = false;
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

        // Initialize Quill editors now that their container is visible
        if (REVIEW_STEPS[stepIndex].id === 'rating') {
            if (!reviewNotesQuill) {
                reviewNotesQuill = initQuillEditor(
                    document.getElementById('reviewNotesEditor'),
                    document.getElementById('reviewNotes'),
                    { placeholder: 'Share your thoughts about the experience...' }
                );
            } else {
                // Re-sync from hidden input (e.g., after draft restore + reset cycle)
                const saved = document.getElementById('reviewNotes').value;
                reviewNotesQuill.clipboard.dangerouslyPasteHTML(saved || '');
            }
            initReviewImageHandlers();
        }

        if (REVIEW_STEPS[stepIndex].id === 'dishes') {
            initBulkDishDropZone();
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
            const firstInput = stepElement.querySelector('input:not([type="hidden"]), textarea, select');
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

        // Submit / save-as-draft buttons
        submitBtn.style.display = isLastStep ? 'inline-block' : 'none';
        saveDraftBtn.style.display = isLastStep ? 'inline-block' : 'none';

        // Validate current step and enable/disable next button
        validateCurrentStep();
    }

    // Review target type (restaurant vs food festival) helpers
    function applyTargetTypeUI() {
        document.getElementById('reviewTargetTypeRestaurant').checked = targetType === 'restaurant';
        document.getElementById('reviewTargetTypeFoodFestival').checked = targetType === 'food_festival';
        document.getElementById('reviewRestaurantTargetContainer').style.display = targetType === 'restaurant' ? 'block' : 'none';
        document.getElementById('reviewFoodFestivalTargetContainer').style.display = targetType === 'food_festival' ? 'block' : 'none';

        document.getElementById('dishesContainer').style.display = targetType === 'food_festival' ? 'none' : 'block';
        document.getElementById('addDishBtn').style.display = targetType === 'food_festival' ? 'none' : 'inline-block';
        document.getElementById('bulkDishDropZoneWrapper').style.display = targetType === 'food_festival' ? 'none' : 'block';
        document.getElementById('festivalGroupsContainer').style.display = targetType === 'food_festival' ? 'block' : 'none';
        document.getElementById('addGroupBtn').style.display = targetType === 'food_festival' ? 'inline-block' : 'none';
    }

    document.getElementById('reviewTargetTypeRestaurant').addEventListener('change', function() {
        if (!this.checked) return;
        targetType = 'restaurant';
        applyTargetTypeUI();
        validateCurrentStep();
    });

    document.getElementById('reviewTargetTypeFoodFestival').addEventListener('change', function() {
        if (!this.checked) return;
        targetType = 'food_festival';
        applyTargetTypeUI();
        validateCurrentStep();
    });

    // Food festival picker helpers
    function switchToNewFoodFestivalMode() {
        foodFestivalMode = 'new';
        document.getElementById('reviewFoodFestivalSearchSection').style.display = 'none';
        document.getElementById('reviewNewFoodFestivalSection').style.display = 'block';
        const typedName = document.getElementById('reviewFoodFestivalName').value.trim();
        const newNameField = document.getElementById('reviewNewFoodFestivalName');
        if (!newNameField.value) newNameField.value = typedName;
        validateCurrentStep();
    }

    function switchToSearchFoodFestivalMode() {
        foodFestivalMode = 'search';
        document.getElementById('reviewNewFoodFestivalSection').style.display = 'none';
        document.getElementById('reviewFoodFestivalSearchSection').style.display = 'block';
        validateCurrentStep();
    }

    function isFoodFestivalSectionValid() {
        if (foodFestivalMode === 'new') {
            return !!document.getElementById('reviewNewFoodFestivalName').value.trim();
        }
        const id = document.getElementById('reviewFoodFestivalId').value;
        const name = document.getElementById('reviewFoodFestivalName').value.trim();
        return !!(id || name);
    }

    function collectFoodFestivalData() {
        if (foodFestivalMode === 'new') {
            return {
                mode: 'new',
                name: document.getElementById('reviewNewFoodFestivalName').value.trim(),
                city: document.getElementById('reviewNewFoodFestivalCity').value.trim(),
                country: document.getElementById('reviewNewFoodFestivalCountry').value.trim(),
                startDate: document.getElementById('reviewNewFoodFestivalStartDate').value,
                endDate: document.getElementById('reviewNewFoodFestivalEndDate').value,
                website: document.getElementById('reviewNewFoodFestivalWebsite').value.trim(),
            };
        }
        return {
            mode: 'search',
            id: document.getElementById('reviewFoodFestivalId').value || null,
            name: document.getElementById('reviewFoodFestivalName').value.trim(),
        };
    }

    document.getElementById('reviewNewFoodFestivalBtn').addEventListener('click', switchToNewFoodFestivalMode);
    document.getElementById('reviewBackToFoodFestivalSearchBtn').addEventListener('click', switchToSearchFoodFestivalMode);
    document.getElementById('reviewNewFoodFestivalName').addEventListener('input', validateCurrentStep);

    // Food festival search with debounce (300ms)
    const foodFestivalInput = document.getElementById('reviewFoodFestivalName');
    const foodFestivalResults = document.getElementById('foodFestivalSearchResults');
    const foodFestivalStatus = document.getElementById('foodFestivalSearchStatus');

    foodFestivalInput.addEventListener('input', function() {
        document.getElementById('reviewFoodFestivalId').value = '';
        clearTimeout(foodFestivalSearchTimeout);
        const query = this.value.trim();

        validateCurrentStep();

        if (query.length < 2) {
            foodFestivalResults.style.display = 'none';
            foodFestivalResults.innerHTML = '';
            foodFestivalStatus.textContent = query.length === 1 ? 'Type at least 2 characters to search' : '';
            return;
        }

        foodFestivalStatus.textContent = 'Searching...';

        foodFestivalSearchTimeout = setTimeout(() => {
            performFoodFestivalSearch(query);
        }, 300);
    });

    function performFoodFestivalSearch(query) {
        fetch(`/api/food-festivals/search/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                foodFestivalResults.innerHTML = '';
                validateCurrentStep();

                if (data.results && data.results.length > 0) {
                    foodFestivalStatus.textContent = `${data.results.length} food festival(s) found`;
                    foodFestivalResults.style.display = 'block';

                    data.results.forEach(festival => {
                        const location = [festival.city, festival.country].filter(Boolean).join(', ');
                        const item = document.createElement('a');
                        item.className = 'list-group-item list-group-item-action';
                        item.href = '#';
                        item.innerHTML = `
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    <strong>${festival.name}</strong>
                                    ${location ? `<br><small class="text-muted">${location}</small>` : ''}
                                </div>
                                <span class="badge bg-secondary">${festival.review_count} review(s)</span>
                            </div>
                        `;
                        item.addEventListener('click', (e) => {
                            e.preventDefault();
                            selectFoodFestival(festival);
                        });
                        foodFestivalResults.appendChild(item);
                    });
                } else {
                    foodFestivalStatus.textContent = 'No food festivals found. Use "New food festival" below to add one.';
                    foodFestivalResults.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Food festival search error:', error);
                foodFestivalStatus.textContent = 'Error searching food festivals';
                foodFestivalResults.style.display = 'none';
                validateCurrentStep();
            });
    }

    function selectFoodFestival(festival) {
        foodFestivalInput.value = festival.name;
        document.getElementById('reviewFoodFestivalId').value = festival.id;
        foodFestivalResults.style.display = 'none';
        foodFestivalResults.innerHTML = '';
        foodFestivalStatus.textContent = '';

        validateCurrentStep();
    }

    // Hide food festival search results when clicking outside
    document.addEventListener('click', function(e) {
        if (!foodFestivalInput.contains(e.target) && !foodFestivalResults.contains(e.target)) {
            foodFestivalResults.style.display = 'none';
        }
    });

    // Restaurant picker helpers
    function switchToNewRestaurantMode() {
        restaurantMode = 'new';
        document.getElementById('reviewRestaurantSearchSection').style.display = 'none';
        document.getElementById('reviewNewRestaurantSection').style.display = 'block';
        const typedName = document.getElementById('reviewRestaurantName').value.trim();
        const newNameField = document.getElementById('reviewNewRestaurantName');
        if (!newNameField.value) newNameField.value = typedName;
        initPlacesAutocomplete(document.getElementById('reviewPlacesSearch'), fillTopLevelRestaurantFromPlace);
        validateCurrentStep();
    }

    function switchToSearchRestaurantMode() {
        restaurantMode = 'search';
        document.getElementById('reviewNewRestaurantSection').style.display = 'none';
        document.getElementById('reviewRestaurantSearchSection').style.display = 'block';
        validateCurrentStep();
    }

    function isRestaurantSectionValid() {
        if (restaurantMode === 'new') {
            const name = document.getElementById('reviewNewRestaurantName').value.trim();
            if (!name) return false;
            const isPopUp = document.getElementById('reviewNewIsPopUp').checked;
            if (isPopUp && !document.getElementById('reviewNewWebsite').value.trim()) return false;
            return true;
        }
        const id = document.getElementById('reviewRestaurantId').value;
        const name = document.getElementById('reviewRestaurantName').value.trim();
        return !!(id || name);
    }

    // Validates a restaurant payload (top-level, or a food-festival dish group's), same rules throughout
    function isDishRestaurantValid(r) {
        if (!r) return false;
        if (r.mode === 'new') {
            if (!r.name) return false;
            if (r.isPopUp && !r.website) return false;
            return true;
        }
        return !!(r.id || r.name);
    }

    function collectRestaurantData() {
        if (restaurantMode === 'new') {
            return {
                mode: 'new',
                name: document.getElementById('reviewNewRestaurantName').value.trim(),
                isPopUp: document.getElementById('reviewNewIsPopUp').checked,
                website: document.getElementById('reviewNewWebsite').value.trim(),
                address: document.getElementById('reviewAddress').value.trim(),
                city: document.getElementById('reviewCity').value.trim(),
                province: document.getElementById('reviewProvince').value.trim(),
                country: document.getElementById('reviewCountry').value.trim(),
                postalCode: document.getElementById('reviewPostalCode').value.trim(),
                googlePlaceId: document.getElementById('reviewNewPlaceId').value,
                placesSessionUsed: placesSessionUsed,
            };
        }
        return {
            mode: 'search',
            id: document.getElementById('reviewRestaurantId').value || null,
            name: document.getElementById('reviewRestaurantName').value.trim(),
        };
    }

    document.getElementById('reviewNewRestaurantBtn').addEventListener('click', switchToNewRestaurantMode);
    document.getElementById('reviewBackToSearchBtn').addEventListener('click', switchToSearchRestaurantMode);

    document.getElementById('reviewNewIsPopUp').addEventListener('change', function() {
        document.getElementById('reviewNewWebsiteSection').style.display = this.checked ? 'block' : 'none';
        document.getElementById('reviewNewAddressSection').style.display = this.checked ? 'none' : 'block';
        validateCurrentStep();
    });

    document.getElementById('reviewNewRestaurantName').addEventListener('input', validateCurrentStep);
    document.getElementById('reviewNewWebsite').addEventListener('input', validateCurrentStep);

    // Google Places autocomplete for "new restaurant" address fields (lazy-loaded, reusable per input).
    // onPlaceSelected receives {name, address, city, province, country, postalCode, placeId}.
    function initPlacesAutocomplete(el, onPlaceSelected) {
        if (!MAPS_API_KEY || !el || placesAutocompleteInstances.has(el)) return;

        if (mapsScriptLoaded) {
            setupPlacesAutocomplete(el, onPlaceSelected);
        } else {
            pendingPlaceInits.push({ el, onPlaceSelected });
            if (pendingPlaceInits.length === 1) {
                window._reviewMapsLoaded = function() {
                    delete window._reviewMapsLoaded;
                    mapsScriptLoaded = true;
                    pendingPlaceInits.forEach(p => setupPlacesAutocomplete(p.el, p.onPlaceSelected));
                    pendingPlaceInits = [];
                };
                const script = document.createElement('script');
                script.src = 'https://maps.googleapis.com/maps/api/js?key=' + encodeURIComponent(MAPS_API_KEY)
                    + '&libraries=places&loading=async&callback=_reviewMapsLoaded';
                script.async = true;
                document.head.appendChild(script);
            }
        }
    }

    function setupPlacesAutocomplete(el, onPlaceSelected) {
        if (placesAutocompleteInstances.has(el)) return;
        let sessionToken = new google.maps.places.AutocompleteSessionToken();
        const autocomplete = new google.maps.places.Autocomplete(el, {
            types: ['establishment'],
            componentRestrictions: { country: ['ca', 'us'] },
            fields: ['address_components', 'name', 'place_id'],
            sessionToken: sessionToken,
        });
        placesAutocompleteInstances.set(el, autocomplete);
        autocomplete.addListener('place_changed', function() {
            const place = autocomplete.getPlace();
            if (!place.address_components) return;

            function getComponent(types, nameType) {
                const comp = place.address_components.find(c => types.some(t => c.types.includes(t)));
                return comp ? comp[nameType] : '';
            }

            const streetNumber = getComponent(['street_number'], 'long_name');
            const route = getComponent(['route'], 'long_name');

            onPlaceSelected({
                name: place.name || '',
                address: [streetNumber, route].filter(Boolean).join(' '),
                city: getComponent(['locality', 'sublocality_level_1'], 'long_name'),
                province: getComponent(['administrative_area_level_1'], 'short_name'),
                country: getComponent(['country'], 'long_name'),
                postalCode: getComponent(['postal_code'], 'long_name'),
                placeId: place.place_id || '',
            });

            placesSessionUsed = true;
            sessionToken = new google.maps.places.AutocompleteSessionToken();
            validateCurrentStep();
        });
    }

    function fillTopLevelRestaurantFromPlace(place) {
        if (place.name) document.getElementById('reviewNewRestaurantName').value = place.name;
        document.getElementById('reviewAddress').value = place.address;
        document.getElementById('reviewCity').value = place.city;
        document.getElementById('reviewProvince').value = place.province;
        document.getElementById('reviewCountry').value = place.country;
        document.getElementById('reviewPostalCode').value = place.postalCode;
        if (place.placeId) document.getElementById('reviewNewPlaceId').value = place.placeId;
    }

    // Validate current step
    function validateCurrentStep() {
        const step = REVIEW_STEPS[currentStep];
        let isValid = true;

        if (step.required) {
            switch (step.id) {
                case 'basic-info':
                    const visitDate = document.getElementById('reviewVisitDate').value.trim();
                    const partySize = parseInt(document.getElementById('reviewPartySize').value);
                    const dateValidationError = document.getElementById('dateValidationError');

                    const targetValid = targetType === 'food_festival' ? isFoodFestivalSectionValid() : isRestaurantSectionValid();
                    isValid = targetValid && visitDate !== '';

                    // Validate date is not in future
                    if (visitDate) {
                        const selectedDate = new Date(visitDate);
                        const today = new Date();
                        today.setHours(0, 0, 0, 0); // Reset time for date-only comparison
                        if (selectedDate > today) {
                            isValid = false;
                            dateValidationError.style.display = 'block';
                        } else {
                            dateValidationError.style.display = 'none';
                        }
                    } else {
                        dateValidationError.style.display = 'none';
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
                    // Save dishes first to ensure formData is up to date
                    saveDishes();
                    if (targetType === 'food_festival') {
                        const groups = Array.from(document.querySelectorAll('.restaurant-group-card')).filter(
                            g => g.parentElement.style.display !== 'none'
                        );
                        isValid = groups.length > 0 && groups.every(g => {
                            const restaurantValid = isDishRestaurantValid(collectGroupRestaurantData(g));
                            const hasDish = g.querySelectorAll('.group-dishes-container .dish-card').length > 0;
                            return restaurantValid && hasDish;
                        });
                    } else {
                        // At least one dish is required
                        isValid = formData.dishes.length > 0;
                    }
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
        draftManager.markUnsaved();

        switch (step.id) {
            case 'basic-info':
                formData.basicInfo = {
                    visitDate: document.getElementById('reviewVisitDate').value.trim(),
                    partySize: document.getElementById('reviewPartySize').value,
                    entryTime: document.getElementById('reviewEntryTime').value.trim()
                };
                formData.targetType = targetType;
                if (targetType === 'food_festival') {
                    formData.food_festival = collectFoodFestivalData();
                    formData.restaurant = {};
                } else {
                    formData.restaurant = collectRestaurantData();
                    formData.food_festival = {};
                }
                break;

            case 'rating':
                formData.rating = {
                    overall: document.getElementById('reviewOverallRating').value,
                    title: document.getElementById('reviewTitle').value.trim(),
                    notes: document.getElementById('reviewNotes').value.trim(),
                    ambiance: document.getElementById('reviewAmbiance').value,
                    service: document.getElementById('reviewService').value,
                    images: [...reviewImages]
                };
                break;

            case 'dishes':
                // Dishes are saved in real-time via dish card handlers
                break;
        }
    }

    // Go to next step
    async function goToNextStep() {
        if (currentStep >= REVIEW_STEPS.length - 1) return;

        const step = REVIEW_STEPS[currentStep];

        // Validate if required
        const isValid = validateCurrentStep();

        if (step.required && !isValid) {
            showError('Please fill in all required fields before continuing.');
            return;
        }

        // Save current step data
        saveCurrentStepData();

        // Save draft (create mode only)
        if (!editingReviewId) {
            await draftManager.saveNow(step.id, formData);
        }

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
    async function goToPreviousStep() {
        if (currentStep <= 0) return;

        // Save current step data (don't validate)
        saveCurrentStepData();

        // Save draft (create mode only)
        if (!editingReviewId) {
            await draftManager.saveNow(REVIEW_STEPS[currentStep].id, formData);
        }

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
    async function closeModal() {
        if (editingReviewId) {
            if (hasUnsavedChanges && !confirm('Discard your changes to this review?')) {
                return;
            }
            modal.hide();
            resetModal();
            return;
        }

        // Save draft before closing if there are changes
        if (hasUnsavedChanges || draftManager.hasUnsaved()) {
            saveCurrentStepData();
            await draftManager.saveNow(REVIEW_STEPS[currentStep].id, formData);
        }

        if (hasUnsavedChanges) {
            if (confirm('Your draft has been saved. Close the modal?')) {
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
            restaurant: {},
            food_festival: {},
            rating: {},
            dishes: []
        };
        hasUnsavedChanges = false;
        editingReviewId = null;
        targetType = 'restaurant';
        restaurantMode = 'search';
        foodFestivalMode = 'search';
        placesSessionUsed = false;
        applyTargetTypeUI();
        resetSubmitButtons();

        document.getElementById('reviewModalLabel').textContent = 'Create New Review';

        // Stop autosave
        draftManager.stopAutosave();

        // Reset dish/group counters
        dishCounter = 0;
        groupCounter = 0;

        // Clear all form fields
        document.getElementById('basicInfoForm').reset();
        document.getElementById('ratingForm').reset();
        document.getElementById('reviewNotes').value = '';
        if (reviewNotesQuill) {
            reviewNotesQuill.setContents([]);
        }
        document.getElementById('dishesContainer').innerHTML = '';
        document.getElementById('festivalGroupsContainer').innerHTML = '';

        // Reset rating displays
        document.getElementById('ratingValue').textContent = '50';
        document.getElementById('ambianceValue').textContent = '50';
        document.getElementById('serviceValue').textContent = '50';

        // Clear review images
        reviewImages = [];
        reviewImageHandlersInitialized = false;
        const previewsDiv = document.getElementById('reviewImagePreviews');
        if (previewsDiv) previewsDiv.innerHTML = '';

        // Reset title character count
        document.getElementById('titleCharCount').textContent = '0';

        // Reset restaurant picker to search mode
        document.getElementById('restaurantSearchResults').style.display = 'none';
        document.getElementById('restaurantSearchResults').innerHTML = '';
        document.getElementById('restaurantSearchStatus').textContent = '';
        document.getElementById('reviewNewRestaurantSection').style.display = 'none';
        document.getElementById('reviewRestaurantSearchSection').style.display = 'block';
        document.getElementById('reviewNewWebsiteSection').style.display = 'none';
        document.getElementById('reviewNewAddressSection').style.display = 'block';

        // Reset food festival picker to search mode
        document.getElementById('foodFestivalSearchResults').style.display = 'none';
        document.getElementById('foodFestivalSearchResults').innerHTML = '';
        document.getElementById('foodFestivalSearchStatus').textContent = '';
        document.getElementById('reviewNewFoodFestivalSection').style.display = 'none';
        document.getElementById('reviewFoodFestivalSearchSection').style.display = 'block';

        hideError();
    }

    // Populate review summary
    function populateReviewSummary() {
        const summaryDiv = document.getElementById('reviewSummary');
        const isFoodFestival = (formData.targetType || 'restaurant') === 'food_festival';
        const target = (isFoodFestival ? formData.food_festival : formData.restaurant) || {};

        let summaryHtml = '';

        // Basic Info Section
        summaryHtml += '<div class="card mb-3">';
        summaryHtml += '<div class="card-header d-flex justify-content-between align-items-center bg-light">';
        summaryHtml += '<h6 class="mb-0"><i class="bi bi-info-circle me-2"></i>Basic Information</h6>';
        summaryHtml += '<button type="button" class="btn btn-sm btn-outline-primary edit-section-btn" data-target-step="0">';
        summaryHtml += '<i class="bi bi-pencil"></i> Edit</button>';
        summaryHtml += '</div>';
        summaryHtml += '<div class="card-body">';
        summaryHtml += `<p class="mb-2"><strong>${isFoodFestival ? 'Food Festival' : 'Restaurant'}:</strong> ${target.name || 'N/A'}</p>`;
        summaryHtml += `<p class="mb-2"><strong>Visit Date:</strong> ${formData.basicInfo.visitDate || 'N/A'}</p>`;
        if (formData.basicInfo.entryTime) {
            summaryHtml += `<p class="mb-2"><strong>Time:</strong> ${formData.basicInfo.entryTime}</p>`;
        }
        summaryHtml += `<p class="mb-0"><strong>Party Size:</strong> ${formData.basicInfo.partySize || '1'} people</p>`;
        summaryHtml += '</div></div>';

        // New Restaurant Address Section (only shown when adding a brand new restaurant)
        if (!isFoodFestival && target.mode === 'new' && (target.address || target.city || target.province || target.country || target.postalCode)) {
            summaryHtml += '<div class="card mb-3">';
            summaryHtml += '<div class="card-header d-flex justify-content-between align-items-center bg-light">';
            summaryHtml += '<h6 class="mb-0"><i class="bi bi-geo-alt me-2"></i>New Restaurant Location</h6>';
            summaryHtml += '<button type="button" class="btn btn-sm btn-outline-primary edit-section-btn" data-target-step="0">';
            summaryHtml += '<i class="bi bi-pencil"></i> Edit</button>';
            summaryHtml += '</div>';
            summaryHtml += '<div class="card-body">';
            if (target.address) summaryHtml += `<p class="mb-2"><strong>Address:</strong> ${target.address}</p>`;
            if (target.city) summaryHtml += `<p class="mb-2"><strong>City:</strong> ${target.city}</p>`;
            if (target.province) summaryHtml += `<p class="mb-2"><strong>Province/State:</strong> ${target.province}</p>`;
            if (target.country) summaryHtml += `<p class="mb-2"><strong>Country:</strong> ${target.country}</p>`;
            if (target.postalCode) summaryHtml += `<p class="mb-0"><strong>Postal Code:</strong> ${target.postalCode}</p>`;
            summaryHtml += '</div></div>';
        } else if (isFoodFestival && target.mode === 'new' && (target.city || target.country || target.startDate || target.endDate)) {
            summaryHtml += '<div class="card mb-3">';
            summaryHtml += '<div class="card-header d-flex justify-content-between align-items-center bg-light">';
            summaryHtml += '<h6 class="mb-0"><i class="bi bi-geo-alt me-2"></i>New Food Festival Details</h6>';
            summaryHtml += '<button type="button" class="btn btn-sm btn-outline-primary edit-section-btn" data-target-step="0">';
            summaryHtml += '<i class="bi bi-pencil"></i> Edit</button>';
            summaryHtml += '</div>';
            summaryHtml += '<div class="card-body">';
            if (target.city) summaryHtml += `<p class="mb-2"><strong>City:</strong> ${target.city}</p>`;
            if (target.country) summaryHtml += `<p class="mb-2"><strong>Country:</strong> ${target.country}</p>`;
            if (target.startDate) summaryHtml += `<p class="mb-2"><strong>Start Date:</strong> ${target.startDate}</p>`;
            if (target.endDate) summaryHtml += `<p class="mb-0"><strong>End Date:</strong> ${target.endDate}</p>`;
            summaryHtml += '</div></div>';
        }

        // Rating Section
        summaryHtml += '<div class="card mb-3">';
        summaryHtml += '<div class="card-header d-flex justify-content-between align-items-center bg-light">';
        summaryHtml += '<h6 class="mb-0"><i class="bi bi-star me-2"></i>Rating & Notes</h6>';
        summaryHtml += '<button type="button" class="btn btn-sm btn-outline-primary edit-section-btn" data-target-step="1">';
        summaryHtml += '<i class="bi bi-pencil"></i> Edit</button>';
        summaryHtml += '</div>';
        summaryHtml += '<div class="card-body">';
        summaryHtml += '<div class="mb-3">';
        summaryHtml += `<strong>Overall Rating:</strong> <span class="badge bg-primary fs-6 ms-2">${formData.rating.overall}/100</span>`;
        summaryHtml += '</div>';
        if (formData.rating.title) {
            summaryHtml += `<div class="mb-2"><strong>Title:</strong> "${formData.rating.title}"</div>`;
        }
        summaryHtml += '<div class="row mb-2">';
        summaryHtml += '<div class="col-md-6">';
        summaryHtml += `<strong>Ambiance:</strong> <span class="badge bg-secondary">${formData.rating.ambiance}/100</span>`;
        summaryHtml += '</div>';
        summaryHtml += '<div class="col-md-6">';
        summaryHtml += `<strong>Service:</strong> <span class="badge bg-secondary">${formData.rating.service}/100</span>`;
        summaryHtml += '</div></div>';
        if (formData.rating.notes) {
            summaryHtml += `<div class="mt-3"><strong>Notes:</strong><div class="border-start border-3 border-primary ps-3 mt-2">${formData.rating.notes}</div></div>`;
        }
        summaryHtml += '</div></div>';

        // Dishes Section
        summaryHtml += '<div class="card mb-3">';
        summaryHtml += '<div class="card-header d-flex justify-content-between align-items-center bg-light">';
        summaryHtml += '<h6 class="mb-0"><i class="bi bi-egg-fried me-2"></i>Dishes</h6>';
        summaryHtml += '<button type="button" class="btn btn-sm btn-outline-primary edit-section-btn" data-target-step="2">';
        summaryHtml += '<i class="bi bi-pencil"></i> Edit</button>';
        summaryHtml += '</div>';
        summaryHtml += '<div class="card-body">';
        if (formData.dishes.length > 0) {
            formData.dishes.forEach((dish, index) => {
                summaryHtml += '<div class="dish-summary-item mb-3 pb-3 border-bottom">';
                summaryHtml += '<div class="row">';
                if (dish.images && dish.images.length > 0) {
                    summaryHtml += '<div class="col-md-3 mb-2 mb-md-0">';
                    summaryHtml += '<div class="d-flex flex-wrap gap-1">';
                    dish.images.forEach(img => {
                        const src = typeof img === 'string' ? img : img.src;
                        summaryHtml += `<img src="${src}" alt="${dish.name}" class="dish-summary-image" style="max-height: 80px; width: 80px;">`;
                    });
                    summaryHtml += '</div></div>';
                    summaryHtml += '<div class="col-md-9">';
                } else {
                    summaryHtml += '<div class="col-12">';
                }
                const costBadge = dish.cost ? ` <span class="badge bg-success">$${parseFloat(dish.cost).toFixed(2)}</span>` : '';
                summaryHtml += `<h6 class="mb-1">${index + 1}. ${dish.name} <span class="badge bg-primary">${dish.rating}/100</span>${costBadge}</h6>`;
                if (isFoodFestival && dish.restaurant && dish.restaurant.name) {
                    summaryHtml += `<div class="mb-2"><span class="badge bg-light text-dark border"><i class="bi bi-shop"></i> ${dish.restaurant.name}</span></div>`;
                }
                // Show encyclopedia link if any (only one allowed per dish)
                if (dish.encyclopedia_ids && dish.encyclopedia_ids.length > 0) {
                    const entry = dish.encyclopedia_ids[0];
                    summaryHtml += `<div class="mb-2"><span class="badge bg-info"><i class="bi bi-book"></i> ${entry.name}</span></div>`;
                }
                if (dish.notes) {
                    summaryHtml += `<p class="text-muted mb-0 small">${dish.notes}</p>`;
                }
                summaryHtml += '</div></div></div>';
            });
        } else {
            summaryHtml += '<p class="text-muted mb-0">No dishes added</p>';
        }
        summaryHtml += '</div></div>';

        summaryDiv.innerHTML = summaryHtml;

        // Add event listeners to edit buttons
        document.querySelectorAll('.edit-section-btn').forEach(btn => {
            btn.addEventListener('click', async function() {
                const targetStep = parseInt(this.dataset.targetStep);
                await goToStep(targetStep);
            });
        });
    }

    // Navigate to a specific step
    async function goToStep(stepIndex) {
        if (stepIndex < 0 || stepIndex >= REVIEW_STEPS.length) return;

        // Save current step data
        saveCurrentStepData();

        // Save draft (create mode only)
        if (!editingReviewId) {
            await draftManager.saveNow(REVIEW_STEPS[currentStep].id, formData);
        }

        // Update current step
        currentStep = stepIndex;

        // Show the step
        showStep(currentStep);
    }

    // Reset the submit / save-as-draft buttons back to their default enabled labels
    function resetSubmitButtons() {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="bi bi-check-circle"></i> Submit Review';
        saveDraftBtn.disabled = false;
        saveDraftBtn.innerHTML = '<i class="bi bi-file-earmark"></i> Save as Draft';
    }

    // Submit review. When saveAsDraft is true, the review is persisted with is_draft=true
    // instead of being finalized.
    async function submitReview(saveAsDraft = false) {
        // Save final step data
        saveCurrentStepData();

        // IMPORTANT: Re-save dishes to ensure encyclopedia links are captured
        saveDishes();

        const isEdit = !!editingReviewId;
        const clickedBtn = saveAsDraft ? saveDraftBtn : submitBtn;

        // Disable both buttons while the request is in flight
        submitBtn.disabled = true;
        saveDraftBtn.disabled = true;
        clickedBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>${isEdit ? 'Saving...' : 'Submitting...'}`;

        try {
            // Prepare data for submission
            const submissionData = {
                basicInfo: formData.basicInfo,
                targetType: formData.targetType || 'restaurant',
                restaurant: formData.restaurant,
                food_festival: formData.food_festival,
                rating: formData.rating,
                dishes: formData.dishes,
                is_draft: saveAsDraft
            };
            if (!isEdit) {
                submissionData.draft_id = draftManager.getDraftId();
            }

            const url = isEdit ? `/api/reviews/${editingReviewId}/update/` : '/api/reviews/create/';
            const method = isEdit ? 'PATCH' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': draftManager.getCsrfToken()
                },
                body: JSON.stringify(submissionData)
            });

            const result = await response.json();

            if (result.success) {
                // Success! Reset draft manager (create mode only)
                if (!isEdit) draftManager.reset();

                const actionWord = saveAsDraft ? 'saved as draft' : (isEdit ? 'updated' : 'submitted');
                const toastMsg = result.image_warnings
                    ? `Review ${actionWord}, but some images failed to upload: ${result.image_warnings.join('; ')}`
                    : `Review ${actionWord} successfully!`;
                showSuccessToast(toastMsg);

                // Close modal
                modal.hide();
                resetModal();

                // Redirect to review detail page
                if (result.review_url) {
                    setTimeout(() => {
                        window.location.href = result.review_url;
                    }, 500);
                } else {
                    // Reload page to show new review
                    setTimeout(() => {
                        window.location.reload();
                    }, 500);
                }
            } else {
                // Handle errors
                if (result.errors) {
                    // Validation errors - show them
                    let errorMessages = [];
                    for (const [field, message] of Object.entries(result.errors)) {
                        errorMessages.push(message);
                    }
                    showError(errorMessages.join('<br>'));
                } else {
                    showError(result.error || `Failed to ${isEdit ? 'update' : 'submit'} review. Please try again.`);
                }

                // Re-enable buttons
                resetSubmitButtons();
            }
        } catch (error) {
            console.error('Error submitting review:', error);
            showError('Network error. Please check your connection and try again.');

            // Re-enable buttons
            resetSubmitButtons();
        }
    }

    // Show success toast notification
    function showSuccessToast(message) {
        // Simple toast implementation
        // In a real app, you might use Bootstrap toast or a library
        const toast = document.createElement('div');
        toast.className = 'alert alert-success position-fixed top-0 start-50 translate-middle-x mt-3';
        toast.style.zIndex = '9999';
        toast.innerHTML = `<i class="bi bi-check-circle me-2"></i>${message}`;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    // Error handling
    function showError(message) {
        errorDiv.innerHTML = message; // Changed to innerHTML to support HTML content
        errorDiv.style.display = 'block';
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function hideError() {
        errorDiv.style.display = 'none';
        errorDiv.innerHTML = '';
    }

    // Event listeners - Navigation buttons
    nextBtn.addEventListener('click', goToNextStep);
    backBtn.addEventListener('click', goToPreviousStep);
    skipBtn.addEventListener('click', skipStep);
    cancelBtn.addEventListener('click', closeModal);
    submitBtn.addEventListener('click', () => submitReview(false));
    saveDraftBtn.addEventListener('click', () => submitReview(true));

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
        document.getElementById('reviewRestaurantId').value = '';
        clearTimeout(restaurantSearchTimeout);
        const query = this.value.trim();

        // Always validate on input
        validateCurrentStep();

        if (query.length < 2) {
            restaurantResults.style.display = 'none';
            restaurantResults.innerHTML = '';
            restaurantStatus.textContent = query.length === 1 ? 'Type at least 2 characters to search' : '';
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

                // Validate after search results are ready
                validateCurrentStep();

                if (data.results && data.results.length > 0) {
                    restaurantStatus.textContent = `${data.results.length} restaurant(s) found`;
                    restaurantResults.style.display = 'block';

                    data.results.forEach(restaurant => {
                        const location = [restaurant.city, restaurant.province].filter(Boolean).join(', ');
                        const item = document.createElement('a');
                        item.className = 'list-group-item list-group-item-action';
                        item.href = '#';
                        item.innerHTML = `
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    <strong>${restaurant.name}</strong>
                                    ${location ? `<br><small class="text-muted">${location}</small>` : ''}
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
                } else {
                    restaurantStatus.textContent = 'No restaurants found. Use "New restaurant" below to add one.';
                    restaurantResults.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Restaurant search error:', error);
                restaurantStatus.textContent = 'Error searching restaurants';
                restaurantResults.style.display = 'none';
                validateCurrentStep();
            });
    }

    function selectRestaurant(restaurant) {
        restaurantInput.value = restaurant.name;
        document.getElementById('reviewRestaurantId').value = restaurant.id;
        restaurantResults.style.display = 'none';
        restaurantResults.innerHTML = '';
        restaurantStatus.textContent = '';

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
    let groupCounter = 0;

    document.getElementById('addDishBtn').addEventListener('click', function() {
        addDish();
    });

    document.getElementById('addGroupBtn').addEventListener('click', function() {
        addRestaurantGroup();
    });

    function addDish(dishData = null, containerEl = null) {
        containerEl = containerEl || document.getElementById('dishesContainer');
        dishCounter++;

        const template = document.getElementById('dishFormTemplate');
        const dishCard = template.cloneNode(true);
        dishCard.style.display = 'block';
        dishCard.id = `dish-${dishCounter}`;
        dishCard.dataset.dishId = dishCounter;
        dishCard.dataset.encyclopediaIds = '[]'; // Store encyclopedia IDs as JSON
        dishCard._dishImages = []; // {id, src, filename} entries; id is null for newly-added images

        // Pre-fill data if provided
        if (dishData) {
            dishCard.querySelector('.dish-name').value = dishData.name || '';
            dishCard.querySelector('.dish-rating').value = dishData.rating || 50;
            dishCard.querySelector('.dish-rating-value').textContent = dishData.rating || 50;
            dishCard.querySelector('.dish-notes').value = dishData.notes || '';
            if (dishData.cost) dishCard.querySelector('.dish-cost').value = dishData.cost;

            // Track the server-side ReviewDish id (edit mode only) so saves reconcile in place
            if (dishData.id) {
                dishCard.dataset.reviewDishId = dishData.id;
            }

            // Pre-fill encyclopedia links if provided
            if (dishData.encyclopedia_ids && dishData.encyclopedia_ids.length > 0) {
                dishCard.dataset.encyclopediaIds = JSON.stringify(dishData.encyclopedia_ids);
            }

            // Pre-fill images if provided (edit mode sends [{id, src}, ...]; drafts never include dish images)
            const providedImages = dishData.images || (dishData.image ? [dishData.image] : []);
            dishCard._dishImages = providedImages.map(
                img => (typeof img === 'string' ? { id: null, src: img } : img)
            );
        }

        // Add to container
        containerEl.appendChild(dishCard);

        // Initialize Quill for dish notes after appending to DOM
        const dishNotesQuill = initQuillEditor(
            dishCard.querySelector('.dish-notes-editor'),
            dishCard.querySelector('.dish-notes'),
            { placeholder: 'Optional notes about this dish...', onChange: saveDishes }
        );

        // Wire AI rewrite button for this dish's notes
        const dishRewriteBtn = dishCard.querySelector('.dish-ai-rewrite-btn');
        if (dishRewriteBtn) {
            dishRewriteBtn.addEventListener('click', function() {
                if (openAiRewriteModal) openAiRewriteModal(dishNotesQuill, dishRewriteBtn);
            });
        }

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

        dishCard.querySelector('.dish-cost').addEventListener('input', function() {
            saveDishes();
        });

        dishCard.querySelector('.remove-dish-btn').addEventListener('click', function() {
            const name = dishCard.querySelector('.dish-name').value.trim();
            const notes = dishCard.querySelector('.dish-notes').value.trim();
            const hasImage = dishCard._dishImages && dishCard._dishImages.length > 0;
            const hasData = name !== '' || notes !== '' || hasImage;

            if (hasData && !confirm('Remove this dish? All data for this dish will be lost.')) {
                return;
            }

            const parentContainer = dishCard.parentElement;
            dishCard.remove();
            updateDishNumbers(parentContainer);
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

        imageInput.addEventListener('change', function(e) {
            Array.from(e.target.files).forEach(file => handleImageFile(file, dishCard));
            e.target.value = '';
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

            Array.from(e.dataTransfer.files).forEach(file => handleImageFile(file, dishCard));
        });

        // Update dish numbers after adding to container
        updateDishNumbers(containerEl);

        // Render pre-filled images and encyclopedia chips
        renderDishImagePreviews(dishCard);
        renderEncyclopediaChips(dishCard);

        // Save dishes and validate
        saveDishes();
        validateCurrentStep();

        // Focus on name field only if this is a new dish (not being restored)
        if (!dishData) {
            setTimeout(() => {
                dishCard.querySelector('.dish-name').focus();
            }, 100);
        }

        return dishCard;
    }

    function handleImageFile(file, dishCard) {
        if (!file) return;

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
            dishCard._dishImages.push({ id: null, src: e.target.result, filename: file.name });
            renderDishImagePreviews(dishCard);
            saveDishes();
        };
        reader.readAsDataURL(file);
    }

    function renderDishImagePreviews(dishCard) {
        renderImagePreviews(dishCard.querySelector('.dish-image-previews'), dishCard._dishImages, function(idx) {
            dishCard._dishImages.splice(idx, 1);
            renderDishImagePreviews(dishCard);
            saveDishes();
        });
    }

    // Bulk dish-photo drop zone (Step 3): each dropped/selected image becomes its own new
    // dish, with that image pre-attached via the existing per-dish image attach flow.
    function initBulkDishDropZone() {
        if (bulkDishHandlersInitialized) return;
        bulkDishHandlersInitialized = true;

        const dropZone = document.getElementById('bulkDishDropZone');
        const fileInput = document.getElementById('bulkDishImageInput');
        if (!dropZone || !fileInput) return;

        dropZone.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', function() {
            handleBulkDishFiles(Array.from(this.files));
            this.value = '';
        });

        dropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', function() {
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            handleBulkDishFiles(Array.from(e.dataTransfer.files));
        });
    }

    function handleBulkDishFiles(files) {
        const statusDiv = document.getElementById('bulkDishDropStatus');
        const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
        const maxSize = 10 * 1024 * 1024; // 10MB
        const skipped = [];
        const containerEl = document.getElementById('dishesContainer');
        let addedCount = 0;

        files.forEach(file => {
            if (!allowedTypes.includes(file.type)) {
                skipped.push(`${file.name} (unsupported file type)`);
                return;
            }
            if (file.size > maxSize) {
                skipped.push(`${file.name} (too large, max 10MB)`);
                return;
            }
            const dishCard = addDish(null, containerEl);
            handleImageFile(file, dishCard);
            addedCount++;
        });

        if (!statusDiv) return;

        if (addedCount === 0 && skipped.length === 0) {
            statusDiv.style.display = 'none';
            return;
        }

        statusDiv.style.display = 'block';
        if (skipped.length > 0) {
            statusDiv.className = 'form-text mt-1 text-danger';
            const addedMsg = addedCount > 0 ? `Added ${addedCount} dish(es). ` : '';
            statusDiv.textContent = `${addedMsg}Skipped: ${skipped.join(', ')}`;
        } else {
            statusDiv.className = 'form-text mt-1 text-success';
            statusDiv.textContent = `Added ${addedCount} dish(es) from photos.`;
        }
    }

    function initReviewImageHandlers() {
        if (reviewImageHandlersInitialized) return;
        reviewImageHandlersInitialized = true;

        const dropZone = document.getElementById('reviewImageDropZone');
        const fileInput = document.getElementById('reviewImageInput');

        dropZone.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', function() {
            Array.from(this.files).forEach(file => addReviewImage(file));
            this.value = '';
        });

        dropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            dropZone.style.borderColor = '#0d6efd';
        });

        dropZone.addEventListener('dragleave', function() {
            dropZone.style.borderColor = '#dee2e6';
        });

        dropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            dropZone.style.borderColor = '#dee2e6';
            Array.from(e.dataTransfer.files).forEach(file => addReviewImage(file));
        });
    }

    function addReviewImage(file) {
        const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            showError('Invalid file type. Please select a JPEG, PNG, or WebP image.');
            return;
        }
        const maxSize = 10 * 1024 * 1024;
        if (file.size > maxSize) {
            showError('File is too large. Maximum size is 10MB.');
            return;
        }
        hideError();

        const reader = new FileReader();
        reader.onload = function(e) {
            reviewImages.push({ id: null, src: e.target.result, filename: file.name });
            renderReviewImagePreviews();
            saveCurrentStepData();
        };
        reader.readAsDataURL(file);
    }

    // Renders a row of removable image thumbnails into container from a list of
    // {id, src} objects (or plain data-URL strings). onRemove(idx) is called when
    // a thumbnail's remove button is clicked. Shared by review-level and dish-level photos.
    function renderImagePreviews(container, images, onRemove) {
        if (!container) return;
        container.innerHTML = '';
        images.forEach((item, idx) => {
            const src = typeof item === 'string' ? item : item.src;

            const wrapper = document.createElement('div');
            wrapper.className = 'position-relative';
            wrapper.style.cssText = 'width: 80px; height: 80px;';

            const img = document.createElement('img');
            img.src = src;
            img.className = 'img-thumbnail';
            img.style.cssText = 'width: 80px; height: 80px; object-fit: cover;';

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'btn btn-danger btn-sm position-absolute top-0 end-0 p-0';
            removeBtn.style.cssText = 'width: 20px; height: 20px; font-size: 10px; line-height: 1;';
            removeBtn.innerHTML = '&times;';
            removeBtn.addEventListener('click', function() {
                onRemove(idx);
            });

            wrapper.appendChild(img);
            wrapper.appendChild(removeBtn);
            container.appendChild(wrapper);
        });
    }

    function renderReviewImagePreviews() {
        renderImagePreviews(document.getElementById('reviewImagePreviews'), reviewImages, function(idx) {
            reviewImages.splice(idx, 1);
            renderReviewImagePreviews();
            saveCurrentStepData();
        });
    }

    function updateDishNumbers(containerEl) {
        const dishCards = containerEl.querySelectorAll('.dish-card');
        dishCards.forEach((card, index) => {
            card.querySelector('.dish-number').textContent = index + 1;
        });
    }

    function moveDishUp(dishCard) {
        const prevCard = dishCard.previousElementSibling;
        if (prevCard && prevCard.id !== 'dishFormTemplate') {
            dishCard.parentNode.insertBefore(dishCard, prevCard);
            updateDishNumbers(dishCard.parentNode);
            saveDishes();
        }
    }

    function moveDishDown(dishCard) {
        const nextCard = dishCard.nextElementSibling;
        if (nextCard) {
            dishCard.parentNode.insertBefore(nextCard, dishCard);
            updateDishNumbers(dishCard.parentNode);
            saveDishes();
        }
    }

    function updateGroupNumbers() {
        document.querySelectorAll('.restaurant-group-card').forEach((card, index) => {
            card.querySelector('.group-number').textContent = index + 1;
        });
    }

    // Groups the flat formData.dishes array (each dish carries its own restaurant payload)
    // into restaurant groups for restoring the grouped UI from a draft or an edit load.
    function groupDishesByRestaurant(dishes) {
        const groups = [];
        const indexByKey = new Map();
        dishes.forEach(dish => {
            const r = dish.restaurant || { mode: 'search', id: null, name: '' };
            const key = r.mode === 'new'
                ? `new:${r.name}|${r.address}|${r.city}`
                : `search:${r.id || r.name}`;
            if (!indexByKey.has(key)) {
                indexByKey.set(key, groups.length);
                groups.push({ restaurant: r, dishes: [] });
            }
            groups[indexByKey.get(key)].dishes.push(dish);
        });
        return groups;
    }

    // Reads the restaurant payload currently set on a restaurant group card (the inner
    // .restaurant-group-card element; its mode/session state live on the outer wrapper).
    function collectGroupRestaurantData(group) {
        const wrapper = group.parentElement;
        const mode = wrapper.dataset.restaurantMode || 'search';
        if (mode === 'new') {
            return {
                mode: 'new',
                name: group.querySelector('.group-new-restaurant-name').value.trim(),
                isPopUp: group.querySelector('.group-new-restaurant-is-pop-up').checked,
                website: group.querySelector('.group-new-restaurant-website').value.trim(),
                address: group.querySelector('.group-new-restaurant-address').value.trim(),
                city: group.querySelector('.group-new-restaurant-city').value.trim(),
                province: group.querySelector('.group-new-restaurant-province').value.trim(),
                country: group.querySelector('.group-new-restaurant-country').value.trim(),
                postalCode: group.querySelector('.group-new-restaurant-postal-code').value.trim(),
                googlePlaceId: group.querySelector('.group-new-restaurant-place-id').value,
                placesSessionUsed: wrapper.dataset.placesSessionUsed === 'true',
            };
        }
        return {
            mode: 'search',
            id: group.querySelector('.group-restaurant-id').value || null,
            name: group.querySelector('.group-restaurant-name').value.trim(),
        };
    }

    // Wires a restaurant group card's own restaurant picker: search existing restaurants, or
    // switch to a "new restaurant" sub-form with Google Places autocomplete. One restaurant
    // selection here applies to every dish added under this group.
    function wireGroupRestaurantPicker(groupCard, restaurantData) {
        const group = groupCard.querySelector('.restaurant-group-card');
        groupCard.dataset.restaurantMode = 'search';
        let searchTimeout = null;
        const nameInput = group.querySelector('.group-restaurant-name');
        const idInput = group.querySelector('.group-restaurant-id');
        const results = group.querySelector('.group-restaurant-results');
        const status = group.querySelector('.group-restaurant-status');
        const searchSection = group.querySelector('.group-restaurant-search-section');
        const newSection = group.querySelector('.group-new-restaurant-section');
        const newName = group.querySelector('.group-new-restaurant-name');
        const newIsPopUp = group.querySelector('.group-new-restaurant-is-pop-up');
        const newWebsite = group.querySelector('.group-new-restaurant-website');
        const newWebsiteSection = group.querySelector('.group-new-restaurant-website-section');
        const newAddressSection = group.querySelector('.group-new-restaurant-address-section');
        const newAddress = group.querySelector('.group-new-restaurant-address');
        const newCity = group.querySelector('.group-new-restaurant-city');
        const newProvince = group.querySelector('.group-new-restaurant-province');
        const newCountry = group.querySelector('.group-new-restaurant-country');
        const newPostalCode = group.querySelector('.group-new-restaurant-postal-code');
        const newPlaceId = group.querySelector('.group-new-restaurant-place-id');
        const placesSearch = group.querySelector('.group-places-search');

        function switchToNew() {
            groupCard.dataset.restaurantMode = 'new';
            searchSection.style.display = 'none';
            newSection.style.display = 'block';
            const typedName = nameInput.value.trim();
            if (!newName.value) newName.value = typedName;
            if (placesSearch) {
                initPlacesAutocomplete(placesSearch, function(place) {
                    if (place.name) newName.value = place.name;
                    newAddress.value = place.address;
                    newCity.value = place.city;
                    newProvince.value = place.province;
                    newCountry.value = place.country;
                    newPostalCode.value = place.postalCode;
                    if (place.placeId) newPlaceId.value = place.placeId;
                    groupCard.dataset.placesSessionUsed = 'true';
                    saveDishes();
                });
            }
            saveDishes();
            validateCurrentStep();
        }

        function switchToSearch() {
            groupCard.dataset.restaurantMode = 'search';
            newSection.style.display = 'none';
            searchSection.style.display = 'block';
            saveDishes();
            validateCurrentStep();
        }

        group.querySelector('.group-new-restaurant-btn').addEventListener('click', switchToNew);
        group.querySelector('.group-back-to-restaurant-search-btn').addEventListener('click', switchToSearch);

        newIsPopUp.addEventListener('change', function() {
            newWebsiteSection.style.display = this.checked ? 'block' : 'none';
            newAddressSection.style.display = this.checked ? 'none' : 'block';
            saveDishes();
            validateCurrentStep();
        });

        newName.addEventListener('input', function() {
            saveDishes();
            validateCurrentStep();
        });
        newWebsite.addEventListener('input', function() {
            saveDishes();
            validateCurrentStep();
        });
        [newAddress, newCity, newProvince, newCountry, newPostalCode].forEach(el => {
            el.addEventListener('input', saveDishes);
        });

        nameInput.addEventListener('input', function() {
            idInput.value = '';
            clearTimeout(searchTimeout);
            const query = this.value.trim();

            saveDishes();
            validateCurrentStep();

            if (query.length < 2) {
                results.style.display = 'none';
                results.innerHTML = '';
                status.textContent = query.length === 1 ? 'Type at least 2 characters to search' : '';
                return;
            }

            status.textContent = 'Searching...';

            searchTimeout = setTimeout(() => {
                fetch(`/api/restaurants/search/?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        results.innerHTML = '';

                        if (data.results && data.results.length > 0) {
                            status.textContent = `${data.results.length} restaurant(s) found`;
                            results.style.display = 'block';

                            data.results.forEach(restaurant => {
                                const item = document.createElement('a');
                                item.className = 'list-group-item list-group-item-action';
                                item.href = '#';
                                item.innerHTML = `<strong>${restaurant.name}</strong>`;
                                item.addEventListener('click', (e) => {
                                    e.preventDefault();
                                    nameInput.value = restaurant.name;
                                    idInput.value = restaurant.id;
                                    results.style.display = 'none';
                                    results.innerHTML = '';
                                    status.textContent = '';
                                    saveDishes();
                                    validateCurrentStep();
                                });
                                results.appendChild(item);
                            });
                        } else {
                            status.textContent = 'No restaurants found. Use "New restaurant" below to add one.';
                            results.style.display = 'none';
                        }
                    })
                    .catch(() => {
                        status.textContent = 'Error searching restaurants';
                        results.style.display = 'none';
                    });
            }, 300);
        });

        document.addEventListener('click', function(e) {
            if (!nameInput.contains(e.target) && !results.contains(e.target)) {
                results.style.display = 'none';
            }
        });

        if (restaurantData) {
            if (restaurantData.mode === 'new') {
                switchToNew();
                newName.value = restaurantData.name || '';
                newIsPopUp.checked = !!restaurantData.isPopUp;
                newWebsite.value = restaurantData.website || '';
                newAddress.value = restaurantData.address || '';
                newCity.value = restaurantData.city || '';
                newProvince.value = restaurantData.province || '';
                newCountry.value = restaurantData.country || '';
                newPostalCode.value = restaurantData.postalCode || '';
                newPlaceId.value = restaurantData.googlePlaceId || '';
                newWebsiteSection.style.display = restaurantData.isPopUp ? 'block' : 'none';
                newAddressSection.style.display = restaurantData.isPopUp ? 'none' : 'block';
            } else {
                switchToSearch();
                nameInput.value = restaurantData.name || '';
                idInput.value = restaurantData.id || '';
            }
        }
    }

    function addRestaurantGroup(restaurantData = null, dishesData = []) {
        groupCounter++;

        const template = document.getElementById('restaurantGroupTemplate');
        const groupCard = template.cloneNode(true);
        groupCard.style.display = 'block';
        groupCard.id = `group-${groupCounter}`;
        groupCard.dataset.groupId = groupCounter;

        document.getElementById('festivalGroupsContainer').appendChild(groupCard);

        wireGroupRestaurantPicker(groupCard, restaurantData);

        const groupDishesContainer = groupCard.querySelector('.group-dishes-container');
        groupCard.querySelector('.add-group-dish-btn').addEventListener('click', function() {
            addDish(null, groupDishesContainer);
        });

        groupCard.querySelector('.remove-group-btn').addEventListener('click', function() {
            const hasDishes = groupDishesContainer.querySelectorAll('.dish-card').length > 0;
            if (hasDishes && !confirm('Remove this restaurant and all its dishes from the review?')) {
                return;
            }
            groupCard.remove();
            updateGroupNumbers();
            saveDishes();
            validateCurrentStep();
        });

        dishesData.forEach(d => addDish(d, groupDishesContainer));

        updateGroupNumbers();
        saveDishes();
        validateCurrentStep();

        return groupCard;
    }

    // Reads one dish card's own fields (name, rating, notes, cost, image, encyclopedia links).
    // Restaurant is not part of a dish card anymore for food-festival reviews — it lives on
    // the dish's parent restaurant group and is attached by the caller. Returns null if unnamed.
    function extractDishFields(card) {
        const name = card.querySelector('.dish-name').value.trim();
        if (!name) return null;

        const rating = card.querySelector('.dish-rating').value;
        const notes = card.querySelector('.dish-notes').value.trim();
        const cost = card.querySelector('.dish-cost').value.trim() || null;
        // Read tracking data from the parent element (the wrapper div where it's actually stored)
        const wrapper = card.parentElement;
        const encyclopediaIds = JSON.parse(wrapper.dataset.encyclopediaIds || '[]');
        const reviewDishId = wrapper.dataset.reviewDishId
            ? parseInt(wrapper.dataset.reviewDishId, 10)
            : undefined;

        return {
            id: reviewDishId,
            name,
            rating,
            notes,
            cost,
            images: [...(wrapper._dishImages || [])],
            encyclopedia_ids: encyclopediaIds
        };
    }

    function saveDishes() {
        formData.dishes = [];

        if (targetType === 'food_festival') {
            document.querySelectorAll('.restaurant-group-card').forEach(group => {
                if (group.parentElement.style.display === 'none') return;
                const restaurantData = collectGroupRestaurantData(group);
                group.querySelectorAll('.group-dishes-container .dish-card').forEach(card => {
                    const dish = extractDishFields(card);
                    if (dish) {
                        dish.restaurant = restaurantData;
                        formData.dishes.push(dish);
                    }
                });
            });
        } else {
            document.querySelectorAll('#dishesContainer .dish-card').forEach(card => {
                const dish = extractDishFields(card);
                if (dish) formData.dishes.push(dish);
            });
        }

        // Mark unsaved changes
        hasUnsavedChanges = true;
        draftManager.markUnsaved();
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
        // Only allow one encyclopedia link per dish - replace existing if any
        const newLink = {
            id: entryId,
            name: entryName,
            slug: entrySlug
        };

        // Update dataset with single entry (replaces any existing)
        dishCard.dataset.encyclopediaIds = JSON.stringify([newLink]);

        // Render chips
        renderEncyclopediaChips(dishCard);

        // Save dishes
        saveDishes();

        // Clear search and close modal
        encyclopediaSearchInput.value = '';
        encyclopediaSearchModal.hide();
    }

    function removeEncyclopediaLink(dishCard, entryId) {
        // Clear the encyclopedia link
        dishCard.dataset.encyclopediaIds = JSON.stringify([]);

        // Render chips (will update button text too)
        renderEncyclopediaChips(dishCard);

        // Save dishes
        saveDishes();
    }

    function renderEncyclopediaChips(dishCard) {
        const chipsContainer = dishCard.querySelector('.encyclopedia-chips');
        const chipsDiv = chipsContainer.querySelector('.d-flex');
        const linkButton = dishCard.querySelector('.link-encyclopedia-btn');
        const encyclopediaIds = JSON.parse(dishCard.dataset.encyclopediaIds || '[]');

        if (encyclopediaIds.length === 0) {
            chipsContainer.style.display = 'none';
            linkButton.innerHTML = '<i class="bi bi-book"></i> Link to Encyclopedia';
            return;
        }

        // Show the linked entry
        chipsContainer.style.display = 'block';
        const link = encyclopediaIds[0]; // Only one link allowed
        chipsDiv.innerHTML = `
            <span class="badge bg-primary d-flex align-items-center gap-1" style="font-size: 0.85rem; padding: 0.4rem 0.6rem;">
                <i class="bi bi-book"></i>
                ${link.name}
                <button type="button" class="btn-close btn-close-white"
                        data-remove-encyclopedia-id="${link.id}"
                        style="font-size: 0.5rem;"
                        aria-label="Remove"></button>
            </span>
        `;

        // Update button text to indicate a link exists
        linkButton.innerHTML = '<i class="bi bi-arrow-repeat"></i> Change Encyclopedia Link';

        // Add click handler to remove button
        const removeBtn = chipsDiv.querySelector('[data-remove-encyclopedia-id]');
        if (removeBtn) {
            removeBtn.addEventListener('click', function() {
                const idToRemove = this.dataset.removeEncyclopediaId;
                removeEncyclopediaLink(dishCard, idToRemove);
            });
        }
    }

    // Reset encyclopedia search modal on close
    document.getElementById('reviewEncyclopediaSearchModal').addEventListener('hidden.bs.modal', function() {
        encyclopediaSearchInput.value = '';
        encyclopediaSearchResults.innerHTML = '';
        encyclopediaSearchStatus.style.display = 'none';
        currentDishCard = null;
        encyclopediaSelectedIndex = -1;
    });

    // AI Rewrite — shared between review notes and all dish notes
    const aiRewriteModalEl = document.getElementById('aiRewriteModal');
    if (aiRewriteModalEl) {
        const aiRewriteModal = new bootstrap.Modal(aiRewriteModalEl);
        const originalPanel = document.getElementById('aiRewriteOriginal');
        const resultPanel = document.getElementById('aiRewriteResult');
        const editablePanel = document.getElementById('aiRewriteEditable');
        const copyOriginalBtn = document.getElementById('aiCopyOriginalBtn');
        const copyResultBtn = document.getElementById('aiCopyResultBtn');
        const aiErrorDiv = document.getElementById('aiRewriteError');
        const acceptBtn = document.getElementById('aiRewriteAcceptBtn');
        const rejectBtn = document.getElementById('aiRewriteRejectBtn');
        let pendingRewrite = '';
        let activeRewriteQuill = null;
        let activeTriggerBtn = null;

        openAiRewriteModal = async function(quill, triggerBtn) {
            if (!quill) return;
            const text = quill.getText().trim();
            if (!text) return;

            activeRewriteQuill = quill;
            activeTriggerBtn = triggerBtn;

            originalPanel.textContent = text;
            resultPanel.innerHTML = '<div class="d-flex align-items-center gap-2 text-muted"><div class="spinner-border spinner-border-sm"></div> Rewriting…</div>';
            aiErrorDiv.style.display = 'none';
            acceptBtn.disabled = true;
            pendingRewrite = '';

            triggerBtn.disabled = true;
            triggerBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Rewriting…';

            aiRewriteModal.show();

            try {
                const response = await fetch('/api/review/ai-rewrite/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': draftManager.getCsrfToken(),
                    },
                    body: JSON.stringify({ text }),
                });
                const data = await response.json();
                if (!response.ok || data.error) throw new Error(data.error || 'Unexpected error');
                pendingRewrite = data.rewritten;
                resultPanel.textContent = pendingRewrite;
                copyResultBtn.disabled = false;
                editablePanel.value = pendingRewrite;
                acceptBtn.disabled = false;
            } catch (err) {
                resultPanel.textContent = '';
                aiErrorDiv.textContent = err.message === 'AI service unavailable'
                    ? 'AI rewrite is currently unavailable. Please try again later.'
                    : 'Rewrite failed. Please try again.';
                aiErrorDiv.style.display = 'block';
            } finally {
                if (activeTriggerBtn) {
                    activeTriggerBtn.disabled = false;
                    activeTriggerBtn.innerHTML = '<i class="bi bi-stars"></i> Rewrite with AI';
                }
            }
        };

        // Wire review-level rewrite button
        const aiRewriteBtn = document.getElementById('aiRewriteBtn');
        if (aiRewriteBtn) {
            aiRewriteBtn.addEventListener('click', function() {
                openAiRewriteModal(reviewNotesQuill, aiRewriteBtn);
            });
        }

        copyOriginalBtn.addEventListener('click', function () {
            editablePanel.value = originalPanel.textContent;
        });

        copyResultBtn.addEventListener('click', function () {
            editablePanel.value = resultPanel.textContent;
        });

        acceptBtn.addEventListener('click', function () {
            const text = editablePanel.value.trim() || pendingRewrite;
            if (text && activeRewriteQuill) {
                activeRewriteQuill.clipboard.dangerouslyPasteHTML(
                    text.replace(/\n/g, '<br>')
                );
                draftManager.markUnsaved();
            }
            aiRewriteModal.hide();
        });

        rejectBtn.addEventListener('click', function () {
            aiRewriteModal.hide();
        });

        aiRewriteModalEl.addEventListener('hidden.bs.modal', function () {
            pendingRewrite = '';
            resultPanel.textContent = '';
            editablePanel.value = '';
            copyResultBtn.disabled = true;
            aiErrorDiv.style.display = 'none';
            acceptBtn.disabled = true;
            activeRewriteQuill = null;
            activeTriggerBtn = null;
        });
    }
});
