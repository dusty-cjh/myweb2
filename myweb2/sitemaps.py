from django.shortcuts import reverse
from django.contrib import sitemaps


class IndexViewSitemap(sitemaps.Sitemap):
	priority = 0.5
	changefreq = 'daily'

	def items(self):
		return ['post:index', 'shop:index']

	def location(self, item):
		return reverse(item)
