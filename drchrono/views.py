from datetime import date, datetime
import hashlib
import hmac
import json
import time

from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from rest_framework.response import Response
from rest_framework.views import APIView
from social_django.models import UserSocialAuth
from social_django.utils import load_strategy

from drchrono.endpoints import AppointmentEndpoint, DoctorEndpoint, PatientEndpoint
from drchrono.forms import CheckInForm, ConfirmForm
from drchrono.models import AppointmentTransition
from drchrono.settings import WEBHOOK_SECRET_TOKEN


def get_token():
    """
    Social Auth module is configured to store our access tokens. This dark magic will fetch it for us if we've
    already signed in.
    """
    provider = UserSocialAuth.objects.get(provider='drchrono')
    if (provider.extra_data['auth_time'] + provider.extra_data['expires_in']) <= int(time.time()):
        strategy = load_strategy()
        provider.refresh_token(strategy)

    return provider.extra_data['access_token']


class SetupView(TemplateView):
    """
    The beginning of the OAuth sign-in flow. Logs a user into the kiosk, and saves the token.
    """
    template_name = 'kiosk_setup.html'


class DoctorWelcome(TemplateView):
    """
    The doctor can see what appointments they have today.
    """
    template_name = 'doctor_welcome.html'

    def make_api_request(self):
        """
        Use the token we have stored in the DB to make an API request and get doctor details. If this succeeds, we've
        proved that the OAuth setup is working
        """
        # We can create an instance of an endpoint resource class, and use it to fetch details
        access_token = get_token()
        api = DoctorEndpoint(access_token)
        # Grab the first doctor from the list; normally this would be the whole practice group, but your hackathon
        # account probably only has one doctor in it.
        return next(api.list())

    def get_context_data(self, **kwargs):
        kwargs = super(DoctorWelcome, self).get_context_data(**kwargs)
        # Hit the API using one of the endpoints just to prove that we can
        # If this works, then your oAuth setup is working correctly.
        doctor_details = self.make_api_request()
        kwargs['doctor'] = doctor_details
        kwargs['avg_wait'] = AppointmentTransition.avg_wait()

        return kwargs


class AppointmentListAPI(APIView):

    def get(self, request):
        appt_map = {}
        result = []

        params = {'doctor': request.GET.get('doctor')}
        date = request.GET.get('date', datetime.now().strftime('%Y-%m-%d'))

        access_token = get_token()
        api = AppointmentEndpoint(access_token)
        appointments = api.list(params=params, date=date)
        for appt in appointments:
            result.append(appt)
            appt_map[int(appt['id'])] = {'arrived_at': None, 'seen_at': None}

        transitions = AppointmentTransition.objects. \
            filter(appointment__in=list(appt_map.keys())). \
            order_by('appointment', 'updated_at')

        for transition in transitions:
            if transition.status == 'Arrived':
                appt_map[transition.appointment]['arrived_at'] = transition.updated_at
            elif transition.status == 'In Session':
                appt_map[transition.appointment]['seen_at'] = transition.updated_at

        for appt in result:
            appt.update(appt_map[int(appt['id'])])

        return Response({'data': result})


class AppointmentAPI(APIView):

    def patch(self, request, appointment_id):
        """
        Partially update Appointment
        """
        token = get_token()
        api = AppointmentEndpoint(token)
        api.update(appointment_id, json.loads(request.body))

        return HttpResponse(status=204)


@csrf_exempt
def webhook(request):
    """
    Save appointment transitions to database.
    """
    events = ('APPOINTMENT_CREATE', 'APPOINTMENT_DELETE', 'APPOINTMENT_MODIFY')

    if request.method == 'GET':
        if 'msg' not in request.GET:
            return HttpResponseBadRequest()

        secret_token = hmac.new(WEBHOOK_SECRET_TOKEN, request.GET['msg'], hashlib.sha256).hexdigest()
        return JsonResponse({
            'secret_token': secret_token
        })
    elif request.method == 'POST':
        # validation
        if request.META.get('HTTP_X_DRCHRONO_SIGNATURE') != WEBHOOK_SECRET_TOKEN:
            return HttpResponseBadRequest()

        if request.META.get('HTTP_X_DRCHRONO_EVENT').upper() not in events:
            return HttpResponseBadRequest()

        obj = json.loads(request.body)['object']

        # Save to database
        appt = AppointmentTransition(
            appointment=obj['id'],
            patient=obj['patient'],
            doctor=obj['doctor'],
            status=obj['status'],
            event=request.META.get('HTTP_X_DRCHRONO_EVENT').split('_')[1],
            scheduled_time=obj['scheduled_time'],
            updated_at=obj['updated_at']
        )
        appt.save()

        return HttpResponse(status=204)

    return HttpResponseBadRequest()


class CheckinView(FormView):
    template_name = 'checkin.html'
    form_class = CheckInForm
    appointment_id = None

    def get_success_url(self):
        return reverse_lazy('confirm', args=(self.appointment_id,))

    def form_valid(self, form):
        """
        Find patient's appointment
        """
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']

        token = get_token()

        # find patient
        patient_api = PatientEndpoint(token)
        patient = next(patient_api.list(params={'first_name': first_name, 'last_name': last_name}))

        if not patient:
            HttpResponseBadRequest('Patient not found.')

        # find appointment
        appt_api = AppointmentEndpoint(token)
        today = date.today().strftime('%Y-%m-%d')
        appt = next(appt_api.list(params={'patient': patient['id'], 'date': today}))

        if not appt:
            HttpResponseBadRequest('Appointment not found.')

        self.appointment_id = appt['id']

        return super(CheckinView, self).form_valid(form)


class ConfirmView(FormView):
    template_name = 'confirm.html'
    form_class = ConfirmForm
    success_url = reverse_lazy('thanks')
    appointment = None

    def get_context_data(self, **kwargs):
        """Use this to add extra context."""
        context = super(ConfirmView, self).get_context_data(**kwargs)
        context['appointment'] = self.kwargs['appointment_id']

        return context

    def get_initial(self):
        """
        Prepopulate form with patient's demographic data
        """
        initial = super(ConfirmView, self).get_initial()

        token = get_token()
        appt_api = AppointmentEndpoint(token)
        self.appointment = appt_api.fetch(self.kwargs['appointment_id'])
        if not self.appointment:
            raise Http404('Appointment %s does not exist.' % self.kwargs['appointment_id'])

        patient_api = PatientEndpoint(token)
        patient = patient_api.fetch(self.appointment['patient'])
        if not patient:
            raise Http404('Patient profile not found.')

        initial.update({
            'first_name': patient['first_name'],
            'last_name': patient['last_name'],
            'email': patient['email'],
            'gender': patient['gender'],
            'race': patient['race'],
            'ethnicity': patient['ethnicity'],
            'preferred_language': patient['preferred_language']
        })

        return initial

    def form_valid(self, form):
        """
        Update demographic info. Set appointment to Arrived.
        """
        token = get_token()

        # update demographic data
        patient_api = PatientEndpoint(token)
        patient_api.update(self.appointment['patient'], {
            'first_name': form.cleaned_data['first_name'],
            'last_name': form.cleaned_data['last_name'],
            'email': form.cleaned_data['email'],
            'gender': form.cleaned_data['gender'],
            'race': form.cleaned_data['race'],
            'ethnicity': form.cleaned_data['ethnicity'],
            'preferred_language': form.cleaned_data['preferred_language']
        })

        # Set appt to arrived
        appt_api = AppointmentEndpoint(token)
        appt_api.update(self.kwargs['appointment_id'], {'status': 'Arrived'})

        return super(ConfirmView, self).form_valid(form)


class ThanksView(TemplateView):
    template_name = 'thanks.html'
