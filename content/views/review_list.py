from django.views.generic import ListView
from content.models import Review


class ReviewListView(ListView):
    """
    List view for restaurant reviews.
    Shows all public reviews ordered by visit date (newest first) with pagination.
    """
    model = Review
    template_name = 'review/list.html'
    context_object_name = 'reviews'
    paginate_by = 50

    def get_queryset(self):
        """
        Return all public reviews ordered by visit date (newest first).
        Optimizes queries with select_related and prefetch_related.
        """
        return Review.objects.filter(
            is_private=False
        ).select_related(
            'created_by'
        ).prefetch_related(
            'images'
        ).order_by('-visit_date', '-entry_time')
