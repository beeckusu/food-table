from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from content.forms import FoodFestivalForm


class FoodFestivalCreateView(LoginRequiredMixin, View):
    template_name = 'food_festival/create.html'

    def get(self, request):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        return render(request, self.template_name, {'food_festival_form': FoodFestivalForm()})

    def post(self, request):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        form = FoodFestivalForm(request.POST)
        if form.is_valid():
            festival = form.save(commit=False)
            festival.created_by = request.user
            festival.save()
            return redirect('content:food_festival_detail', pk=festival.pk)
        return render(request, self.template_name, {'food_festival_form': form})
