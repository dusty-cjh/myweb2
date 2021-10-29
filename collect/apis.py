from rest_framework.viewsets import ModelViewSet

from .serializers import StudyCollectSerializer
from .models import StudyCollect


class StudyCollectViewSet(ModelViewSet):
	serializer_class = StudyCollectSerializer
	queryset = StudyCollect.objects.all()

	def create(self, request, *args, **kwargs):

		res = super().create(request, *args, **kwargs)
		return res