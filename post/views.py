from django.shortcuts import render
from django.views.generic import ListView, TemplateView, DetailView
from django.http.response import HttpResponse

from .models import Post, Summary
from .models import Article


class IndexView(ListView):
    queryset = Summary.get_mainpage()
    template_name = 'post/index.html'


class ShopView(TemplateView):
    template_name = 'post/shop.html'


class AboutView(TemplateView):
    template_name = 'post/about.html'


class SupportView(TemplateView):
    template_name = 'post/support.html'


class PostDetailView(DetailView):
    queryset = Post.objects.all()
    template_name = 'post/post.html'


def wx_verify(request):
    return HttpResponse(b'cnuhJDCblRVDP7Vf', status=200)


class ArticleDetailView(DetailView):
    queryset = Article.objects.all()

