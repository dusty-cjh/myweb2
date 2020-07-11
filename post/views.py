from django.shortcuts import render
from django.views.generic import ListView, TemplateView, DetailView

from .models import Post, Summary


class IndexView(ListView):
    queryset = Summary.get_mainpage()
    template_name = 'post/index.html'


class ShopView(TemplateView):
    template_name = 'post/shop.html'


class AboutView(TemplateView):
    template_name = 'post/about.html'


class SupportView(TemplateView):
    template_name = 'post/support.html'

