from rest_framework.decorators import action
from rest_framework.viewsets import ReadOnlyModelViewSet

from .serializers import SummarySerializer
from .models import Summary
from logging import getLogger

log = getLogger('statistic')


class SummaryViewSet(ReadOnlyModelViewSet):
    serializer_class = SummarySerializer

    def get_queryset(self):
        handle = 'get_' + self.request.GET.get('category', '')
        if hasattr(Summary, handle):
            qs = getattr(Summary, handle)()
        else:
            qs = Summary.objects.all()

        return qs
