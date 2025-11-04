from django.views.generic import ListView
from django.db.models import Count, F
from content.models import ReviewDish


class ReviewDishListView(ListView):
    """
    List view for review dishes.
    Shows all dishes from public reviews with optimized queries.
    Includes annotations for computed fields and efficient prefetching.
    """
    model = ReviewDish
    template_name = 'review_dish/list.html'
    context_object_name = 'review_dishes'
    paginate_by = 50

    def get_queryset(self):
        """
        Return all dishes from public reviews with optimized queries.
        Uses select_related and prefetch_related to minimize database hits.
        Annotates computed fields for display efficiency.
        """
        queryset = ReviewDish.objects.filter(
            review__is_private=False
        ).select_related(
            'review',  # Parent review
            'encyclopedia_entry',  # Encyclopedia link (if present)
            'review__created_by'  # Review author
        ).prefetch_related(
            'images'  # Dish images
        ).annotate(
            has_images=Count('images'),  # Count of images for this dish
            review_date=F('review__visit_date'),  # Denormalized review date
            restaurant_name=F('review__restaurant_name')  # Denormalized restaurant name
        ).order_by('-review__visit_date', '-review__entry_time')

        return queryset

    def get_context_data(self, **kwargs):
        """
        Add additional context data to template.
        """
        context = super().get_context_data(**kwargs)

        # Add total count for display
        context['total_dishes'] = ReviewDish.objects.filter(
            review__is_private=False
        ).count()

        return context
