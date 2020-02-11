from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
admin.autodiscover()

import views


urlpatterns = [
    url(r'^setup/$', views.SetupView.as_view(), name='setup'),
    url(r'^welcome/$', views.DoctorWelcome.as_view(), name='setup'),
    url(r'^appointments/$', views.AppointmentListAPI.as_view(), name='appointments_list_api'),
    url(r'^appointments/(?P<appointment_id>[0-9]+)/$', views.AppointmentAPI.as_view()),
    url(r'^webhook/$', views.webhook),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include('social.apps.django_app.urls', namespace='social')),
]

urlpatterns += i18n_patterns(
    url(r'^checkin/$', views.CheckinView.as_view(), name='checkin'),
    url(r'^confirm/(?P<appointment_id>[0-9]+)/$', views.ConfirmView.as_view(), name='confirm'),
    url(r'^thanks/$', views.ThanksView.as_view(), name='thanks'),
)
