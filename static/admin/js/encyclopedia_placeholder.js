(function($) {
    'use strict';

    $(document).ready(function() {
        // Add row classes based on placeholder status for visual styling
        $('#result_list tbody tr').each(function() {
            var $row = $(this);
            var statusCell = $row.find('td').eq(1); // Status is second column after name
            var statusText = statusCell.text().trim();

            if (statusText.includes('Placeholder (has description)')) {
                $row.addClass('placeholder-row');
            } else if (statusText.includes('Placeholder')) {
                $row.addClass('placeholder-empty-row');
            }
        });

        // Toggle description field styling based on placeholder checkbox
        var $placeholderCheckbox = $('#id_is_placeholder');
        var $descriptionField = $('.field-description');

        if ($placeholderCheckbox.length && $descriptionField.length) {
            function toggleDescriptionStyling() {
                if ($placeholderCheckbox.is(':checked')) {
                    $descriptionField.addClass('placeholder-mode');

                    // Add or update help text
                    var $existingHelp = $descriptionField.find('.placeholder-help');
                    if ($existingHelp.length === 0) {
                        $descriptionField.find('textarea').after(
                            '<p class="help placeholder-help">Description is optional for placeholders.</p>'
                        );
                    }
                } else {
                    $descriptionField.removeClass('placeholder-mode');
                    $descriptionField.find('.placeholder-help').remove();
                }
            }

            // Initial state
            toggleDescriptionStyling();

            // Listen for changes
            $placeholderCheckbox.on('change', toggleDescriptionStyling);
        }
    });
})(django.jQuery);
