// Google Places address autocomplete for the restaurant creation form.
// Parses address_components from the selected place and populates the five
// structured address fields. Uses session tokens so the entire type-and-select
// sequence counts as a single billable event.

(function () {
  function initAutocomplete() {
    const searchInput = document.getElementById('id-address-search');
    if (!searchInput || typeof google === 'undefined') return;

    let sessionToken = new google.maps.places.AutocompleteSessionToken();

    const autocomplete = new google.maps.places.Autocomplete(searchInput, {
      types: ['establishment'],
      componentRestrictions: { country: ['ca', 'us'] },
      fields: ['address_components', 'name', 'place_id'],
      sessionToken: sessionToken,
    });

    autocomplete.addListener('place_changed', function () {
      const place = autocomplete.getPlace();
      console.log('Places place_changed:', place);
      if (!place.address_components) return;

      const get = (types, nameType) => {
        const component = place.address_components.find(c =>
          types.some(t => c.types.includes(t))
        );
        return component ? component[nameType] : '';
      };

      const streetNumber = get(['street_number'], 'long_name');
      const route = get(['route'], 'long_name');
      const streetAddress = [streetNumber, route].filter(Boolean).join(' ');

      if (place.name) {
        const nameField = document.getElementById('id_name');
        if (nameField && !nameField.value) nameField.value = place.name;
      }

      document.getElementById('id_street_address').value = streetAddress;
      document.getElementById('id_city').value =
        get(['locality', 'sublocality_level_1'], 'long_name');
      document.getElementById('id_province').value =
        get(['administrative_area_level_1'], 'short_name');
      document.getElementById('id_country').value =
        get(['country'], 'long_name');
      document.getElementById('id_postal_code').value =
        get(['postal_code'], 'long_name');

      if (place.place_id) {
        const placeIdField = document.getElementById('id_google_place_id');
        if (placeIdField) placeIdField.value = place.place_id;
      }

      document.getElementById('id-places-session-used').value = '1';

      // Rotate token so the next search starts a new billable session.
      sessionToken = new google.maps.places.AutocompleteSessionToken();
    });
  }

  // The Places library calls window.initAutocomplete when it loads (via callback= param).
  window.initAutocomplete = initAutocomplete;
})();
