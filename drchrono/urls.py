from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib import admin
admin.autodiscover()

import views


urlpatterns = [
    url(r'^setup/$', views.SetupView.as_view(), name='setup'),
    url(r'^welcome/$', views.DoctorWelcome.as_view(), name='setup'),
    url(r'^appointments/$', views.AppointmentListAPI.as_view(), name='appointments_list_api'),
    url(r'^appointments/(?P<appointment_id>[0-9]+)/$', views.AppointmentAPI.as_view()),
    url(r'^webhook/$', views.webhook),
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include('social.apps.django_app.urls', namespace='social')),
]
