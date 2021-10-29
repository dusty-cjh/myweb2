from django.urls import path

from .views import SignUpView, SignUpResultView, SignUpSourceView, PersonalListView, PresentView, PresentDownloadView


app_name = 'collect'
urlpatterns = [
	path('sign-up/<str:version>/', SignUpView.as_view(), name='sign-up'),
	path('signup-result/', SignUpResultView.as_view(), name='signup-result'),
	path('signup-source/<str:version>/', SignUpSourceView.as_view(), name='signup-source'),
	path('personal-list/', PersonalListView.as_view(), name='personal-list'),

	path('exhibit/', PresentView.as_view(), name='present'),
	path('present-download/', PresentDownloadView.as_view(), name='present-download'),
]