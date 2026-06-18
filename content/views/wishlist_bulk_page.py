from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.http import HttpResponseForbidden


class WishlistBulkPageView(LoginRequiredMixin, View):
    template_name = 'wishlist/bulk_add.html'

    def get(self, request):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        return render(request, self.template_name, {
            'google_maps_api_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
        })
