from django_filters import rest_framework as filters

from .models import Summary


class SummaryFilter(filters.FilterSet):
	class Meta:
		model = Summary
		fields = {
			'type': ['exact', 'lt', ],
		}


