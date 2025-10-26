from django.views.generic import DetailView
from content.models import Review


class ReviewDetailView(DetailView):
    """
    Detail view for a single restaurant review.
    Displays full review details including dishes, images, tags, and related reviews.
    """
    model = Review
    template_name = 'review/detail.html'
    context_object_name = 'review'

    def get_queryset(self):
        """Only show public reviews."""
        return Review.objects.filter(is_private=False)

    def get_context_data(self, **kwargs):
        """Add additional context for dishes, images, tags, and related reviews."""
        context = super().get_context_data(**kwargs)
        review = self.object

        # Add dishes with encyclopedia entries and images
        context['dishes'] = review.review_dishes.select_related('encyclopedia_entry').prefetch_related('images').all()

        # Add images
        context['images'] = review.images.all()

        # Add tags
        context['tags'] = review.review_tags.all()

        # Add related reviews at the same restaurant (excluding current review)
        context['related_reviews'] = Review.objects.filter(
            restaurant_name__iexact=review.restaurant_name,
            is_private=False
        ).exclude(
            id=review.id
        ).prefetch_related(
            'images',
            'review_dishes__images'
        ).order_by('-visit_date', '-entry_time')[:5]

        return context
