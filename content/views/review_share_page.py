from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.utils.html import strip_tags
from django.views import View

from content.models import Review


def _is_staff(user):
    return user.is_staff


@method_decorator([login_required, user_passes_test(_is_staff)], name='dispatch')
class ReviewSharePageView(View):
    """
    Compose-and-share page for a review: source panel, shared main_text box,
    per-platform lens tabs, and an autosaved draft (FT-171 / FT-157).
    """
    template_name = 'review/share.html'

    def get(self, request, pk, *args, **kwargs):
        review = get_object_or_404(
            Review.objects.select_related('restaurant'),
            pk=pk,
        )
        dishes = review.review_dishes.select_related('encyclopedia_entry').prefetch_related('images').all()
        images = review.images.all()
        share_draft = review.metadata.get('share_draft')

        page_data = {
            'review_id': review.pk,
            'seed_text': strip_tags(review.notes or ''),
            'share_draft': share_draft,
        }

        return render(request, self.template_name, {
            'review': review,
            'dishes': dishes,
            'images': images,
            'page_data': page_data,
        })
