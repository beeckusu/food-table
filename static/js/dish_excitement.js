// Dish Excitement - clickable flame ratings for anticipated dishes
// (templates/components/excitement_flames.html). Clicking the current level clears it.

document.addEventListener('DOMContentLoaded', function() {
    function getCookie(name) {
        const match = document.cookie.split(';').map(c => c.trim()).find(c => c.startsWith(name + '='));
        return match ? decodeURIComponent(match.substring(name.length + 1)) : null;
    }

    function render(rating, value) {
        rating.dataset.value = value || '';
        const max = rating.querySelectorAll('.excitement-flame').length;
        rating.title = value ? `Excitement: ${value}/${max} (click the same flame to clear)` : 'Rate your excitement';
        rating.querySelectorAll('.excitement-flame').forEach(flame => {
            const icon = flame.querySelector('i');
            const lit = value && parseInt(flame.dataset.level, 10) <= value;
            icon.className = lit ? 'bi bi-fire text-danger' : 'bi bi-fire text-body-tertiary opacity-50';
        });
    }

    document.addEventListener('click', function(e) {
        const flame = e.target.closest('.excitement-flame');
        if (!flame) return;
        e.preventDefault();

        const rating = flame.closest('.excitement-rating');
        const previous = parseInt(rating.dataset.value, 10) || null;
        const level = parseInt(flame.dataset.level, 10);
        const value = level === previous ? null : level;

        render(rating, value);

        // Form-field mode: just record the value for the surrounding form
        const input = rating.querySelector('.excitement-value');
        if (input) {
            input.value = value || '';
            return;
        }

        // Saved-dish mode: persist via the API (render above was optimistic)
        fetch(rating.dataset.url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ excitement: value })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) throw new Error(data.error || 'Failed to save excitement');
        })
        .catch(error => {
            console.error('Excitement error:', error);
            render(rating, previous);
            alert('Could not save excitement. Please try again.');
        });
    });
});
