(function($) {
    'use strict';

    $(document).ready(function() {
        // Only run on encyclopedia admin change form
        // Django's filter_horizontal creates elements with specific class/id patterns
        var $similarDishesRow = $('.form-row.field-similar_dishes');

        if ($similarDishesRow.length === 0) {
            return; // Not on the encyclopedia admin page with similar_dishes field
        }

        // Add "Create Placeholder" button above the filter_horizontal widget
        var $createButton = $('<a>', {
            'href': '#',
            'class': 'quick-create-placeholder-btn',
            'text': '+ Create Placeholder'
        });

        // Insert button before the selector
        $similarDishesRow.prepend($createButton);

        // Get the current encyclopedia entry ID from the URL
        // URL format: /admin/content/encyclopedia/{id}/change/
        var currentEntryId = null;
        var urlMatch = window.location.pathname.match(/\/encyclopedia\/(\d+)\/change\//);
        if (urlMatch) {
            currentEntryId = parseInt(urlMatch[1]);
            console.log('Current encyclopedia entry ID:', currentEntryId);
        }

        // Find the encyclopedia form (NOT the logout form!)
        var $form = $('form#encyclopedia_form');
        if ($form.length === 0) {
            console.error('Could not find form#encyclopedia_form');
            return;
        }
        console.log('Attaching submit handler to form#encyclopedia_form');

        // Ensure all options in "to" select are selected on form submit
        // This is required for Django's filter_horizontal to work properly
        $form.on('submit', function(e) {
            console.log('=== FORM SUBMIT EVENT ===');

            // Check ALL select elements that might be related
            console.log('Checking for similar_dishes select elements:');
            var $mainSelect = $('#id_similar_dishes');
            var $fromSelect = $('#id_similar_dishes_from');
            var $toSelect = $('#id_similar_dishes_to');

            console.log('id_similar_dishes (main):', $mainSelect.length, $mainSelect.length > 0 ? 'exists, visible=' + $mainSelect.is(':visible') + ', options=' + $mainSelect[0].options.length : 'NOT FOUND');
            console.log('id_similar_dishes_from:', $fromSelect.length, 'visible=' + $fromSelect.is(':visible'), 'options=' + $fromSelect[0].options.length);
            console.log('id_similar_dishes_to:', $toSelect.length, 'visible=' + $toSelect.is(':visible'), 'options=' + $toSelect[0].options.length);

            // Select all in all of them
            if ($mainSelect.length > 0) {
                console.log('Selecting all in MAIN select');
                $mainSelect.find('option').prop('selected', true);
                console.log('  Main select selected:', $mainSelect.find('option:selected').length);
            }

            $toSelect.find('option').prop('selected', true);
            console.log('  To select selected:', $toSelect.find('option:selected').length);
        });

        // Also handle Save buttons directly - use mousedown to run BEFORE the submit
        $('input[name="_save"], input[name="_continue"], input[name="_addanother"]').on('mousedown', function() {
            console.log('=== Save button mousedown ===');

            // Log all similar_dishes selects
            $('select[id*="similar_dishes"]').each(function() {
                var $select = $(this);
                console.log('Select:', this.id);
                console.log('  Total options:', this.options.length);
                console.log('  Selected before:', $select.find('option:selected').length);

                // Select all options
                $select.find('option').prop('selected', true);

                console.log('  Selected after:', $select.find('option:selected').length);
                console.log('  Options:', Array.from(this.options).map(o => ({value: o.value, text: o.text, selected: o.selected})));
            });
        });

        // Create modal HTML
        var modalHtml = `
            <div id="quick-create-modal" class="quick-create-modal" style="display: none;">
                <div class="quick-create-modal-overlay"></div>
                <div class="quick-create-modal-content">
                    <h2>Create New Placeholders</h2>
                    <form id="quick-create-form">
                        <div class="form-group">
                            <label for="quick-create-names">Placeholder Names <span class="required">*</span></label>
                            <textarea id="quick-create-names" name="names" required rows="8" autocomplete="off" style="font-family: monospace;"></textarea>
                            <p class="help-text">Enter one placeholder name per line. All will be linked as similar dishes.</p>
                        </div>
                        <div class="error-message" style="display: none;"></div>
                        <div class="progress-bar" style="display: none;">
                            <div class="progress-fill"></div>
                            <div class="progress-text">0%</div>
                        </div>
                        <div class="button-group">
                            <button type="submit" class="button primary">Create Placeholders</button>
                            <button type="button" class="button cancel">Cancel</button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        $('body').append(modalHtml);

        var $modal = $('#quick-create-modal');
        var $form = $('#quick-create-form');
        var $namesInput = $('#quick-create-names');
        var $errorMessage = $modal.find('.error-message');
        var $progressBar = $modal.find('.progress-bar');
        var $progressFill = $modal.find('.progress-fill');
        var $progressText = $modal.find('.progress-text');

        // Show modal
        function showModal() {
            $modal.fadeIn(200);
            $namesInput.val('').focus();
            $errorMessage.hide().text('');
            $progressBar.hide();
        }

        // Hide modal
        function hideModal() {
            $modal.css('display', 'none');
            $namesInput.val('');
            $errorMessage.hide().text('');
            $progressBar.hide();
        }

        // Show error message
        function showError(message) {
            $errorMessage.text(message).fadeIn(200);
        }

        // Get CSRF token
        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }

        // Add new entry to filter_horizontal widget
        function addEntryToWidget(entry) {
            console.log('Adding entry to widget:', entry);

            // Django's filter_horizontal creates BOTH hidden selects AND visual selector boxes
            // We need to update both the hidden select AND the visible select in the selector-chosen div

            // Debug: Let's see ALL select elements for similar_dishes
            console.log('All selects with similar_dishes in ID:');
            $('select[id*="similar_dishes"]').each(function() {
                console.log('  -', this.id, 'options:', this.options.length, 'visible:', $(this).is(':visible'));
            });

            // First, find the visual selector boxes
            var $selectorChosen = $('.selector-chosen select');
            var $hiddenToSelect = $('#id_similar_dishes_to');

            console.log('Found selector-chosen select:', $selectorChosen.length, 'ID:', $selectorChosen.attr('id'));
            console.log('Found hidden to select:', $hiddenToSelect.length);

            if ($selectorChosen.length === 0 && $hiddenToSelect.length === 0) {
                console.error('Could not find any filter_horizontal select elements');
                return;
            }

            // Create new option element
            var displayText = entry.name;
            var $newOption = $('<option>', {
                value: entry.id,
                text: displayText,
                selected: true,
                title: displayText
            });

            // Add to the VISIBLE selector-chosen select (this is what users see)
            if ($selectorChosen.length > 0) {
                $selectorChosen.append($newOption.clone());
                sortSelectOptions($selectorChosen);
                console.log('Added to visual selector-chosen');
            }

            // Add to the HIDDEN "to" select (this is what gets submitted)
            if ($hiddenToSelect.length > 0) {
                $hiddenToSelect.append($newOption.clone());
                sortSelectOptions($hiddenToSelect);
                console.log('Added to hidden to select');
            }

            // Ensure it's selected in both
            $selectorChosen.find('option[value="' + entry.id + '"]').prop('selected', true);
            $hiddenToSelect.find('option[value="' + entry.id + '"]').prop('selected', true);

            console.log('Entry added successfully');
        }

        // Sort select options alphabetically
        function sortSelectOptions($select) {
            var options = $select.find('option').toArray();
            options.sort(function(a, b) {
                return a.text.localeCompare(b.text);
            });
            $select.empty().append(options);
        }

        // Handle form submission
        $form.on('submit', async function(e) {
            e.preventDefault();

            var input = $namesInput.val().trim();
            if (!input) {
                showError('Please enter at least one placeholder name');
                return;
            }

            // Parse lines (split by newline, filter empty lines, trim each)
            var names = input
                .split('\n')
                .map(function(line) { return line.trim(); })
                .filter(function(line) { return line.length > 0; });

            if (names.length === 0) {
                showError('Please enter at least one placeholder name');
                return;
            }

            // Hide error message
            $errorMessage.hide();

            // Show progress bar
            $progressBar.show();
            $progressFill.css('width', '0%');
            $progressText.text('0%');

            // Disable form during submission
            var $submitButton = $form.find('button[type="submit"]');
            $submitButton.prop('disabled', true).text('Creating...');

            var errors = [];
            var completed = 0;

            // Create placeholders one by one
            for (var i = 0; i < names.length; i++) {
                var name = names[i];
                var percent = Math.round(((i + 1) / names.length) * 100);

                var requestData = {
                    name: name
                };

                // If we're editing an existing entry, link it as a similar dish
                if (currentEntryId) {
                    requestData.source_entry_id = currentEntryId;
                }

                try {
                    var response = await $.ajax({
                        url: '/api/encyclopedia/create-placeholder/',
                        type: 'POST',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken'),
                            'Content-Type': 'application/json'
                        },
                        data: JSON.stringify(requestData)
                    });

                    if (response.success) {
                        completed++;
                    } else {
                        errors.push(name + ': ' + (response.error || 'Failed to create'));
                    }
                } catch (xhr) {
                    var errorMsg = 'Network error';
                    if (xhr.responseJSON && xhr.responseJSON.error) {
                        errorMsg = xhr.responseJSON.error;
                    }
                    errors.push(name + ': ' + errorMsg);
                }

                // Update progress
                $progressFill.css('width', percent + '%');
                $progressText.text(percent + '% (' + (i + 1) + '/' + names.length + ')');
            }

            // All done
            if (completed > 0) {
                // Reload the page to show the updated similar dishes
                window.location.reload();
            } else {
                // All failed
                showError('Failed to create placeholders: ' + errors.join(', '));
                $submitButton.prop('disabled', false).text('Create Placeholders');
                $progressBar.hide();
            }
        });

        // Button click handlers
        $createButton.on('click', function(e) {
            e.preventDefault();
            showModal();
        });

        $modal.find('.cancel').on('click', function() {
            hideModal();
        });

        // Close modal when clicking overlay
        $modal.find('.quick-create-modal-overlay').on('click', function() {
            hideModal();
        });

        // Close modal on Escape key
        $(document).on('keydown', function(e) {
            if (e.key === 'Escape' && $modal.is(':visible')) {
                hideModal();
            }
        });
    });
})(django.jQuery);
