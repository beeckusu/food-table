from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView
from content.models import Review, RestaurantDish


class ReviewDetailView(LoginRequiredMixin, DetailView):
    """
    Detail view for a single restaurant or food-festival review.
    Displays full review details including dishes, images, tags, and related reviews.
    """
    model = Review
    template_name = 'review/detail.html'
    context_object_name = 'review'

    def get_queryset(self):
        """Only show public reviews. Draft reviews are only visible to staff."""
        queryset = Review.objects.filter(is_private=False)
        if not self.request.user.is_staff:
            queryset = queryset.exclude(is_draft=True)
        return queryset

    def get_context_data(self, **kwargs):
        """Add additional context for dishes, images, tags, and related reviews."""
        context = super().get_context_data(**kwargs)
        review = self.object

        # Add dishes with encyclopedia entries and images
        dishes = list(review.review_dishes.select_related('encyclopedia_entry').prefetch_related('images').all())

        if review.food_festival_id:
            # A food-festival review's dishes can each come from a different vendor; look up
            # which restaurant each dish was tried at (matched by name, same as the edit-data API).
            dish_restaurants = {
                rd.dish_name: rd.restaurant
                for rd in RestaurantDish.objects.filter(review=review).select_related('restaurant')
            }
            for dish in dishes:
                dish.restaurant_for_display = dish_restaurants.get(dish.dish_name)

        context['dishes'] = dishes

        # Add images
        context['images'] = review.images.all()

        # Add tags
        context['tags'] = review.review_tags.all()

        # Add related reviews at the same target (excluding current review)
        if review.food_festival_id:
            related_qs = Review.objects.filter(food_festival=review.food_festival, is_private=False)
        else:
            related_qs = Review.objects.filter(restaurant=review.restaurant, is_private=False)
        if not self.request.user.is_staff:
            related_qs = related_qs.exclude(is_draft=True)
        context['related_reviews'] = related_qs.exclude(
            id=review.id
        ).prefetch_related(
            'images',
            'review_dishes__images'
        ).order_by('-visit_date', '-entry_time')[:5]

        return context
