from django import forms


ETHNICITY = [('not_hispanic', 'Not Hispanic'), ('hispanic', 'Hispanic')]

GENDER = [('Male', 'Male'), ('Female', 'Female')]

LANGUAGES = [
    ('eng', 'English'),
    ('spa', 'Spanish'),
    ('man', 'Mandarin'),
    ('ara', 'Arabic'),
    ('hin', 'Hindustani'),
]

RACE = [
    ('white', 'White'),
    ('black', 'Black or African A.'),
    ('indian', 'A. Indian/Alaska Nat.'),
    ('asian', 'Asian'),
    ('pacific Is.', 'Hawaiian N. & Pacific Is.'),
    ('other', 'Other')
]


class CheckInForm(forms.Form):
    first_name = forms.CharField(label='First Name', max_length=50)
    last_name = forms.CharField(label='Last Name', max_length=50)


class ConfirmForm(forms.Form):
    first_name = forms.CharField(label='First Name', max_length=50)
    last_name = forms.CharField(label='Last Name', max_length=50)
    email = forms.CharField(label='Email', max_length=50)
    gender = forms.CharField(
        label='Gender',
        widget=forms.Select(choices=GENDER)
    )
    race = forms.CharField(
        label='Race',
        widget=forms.Select(choices=RACE)
    )
    ethnicity = forms.CharField(
        label='Ethnicity',
        widget=forms.Select(choices=ETHNICITY)
    )
    preferred_language = forms.CharField(
        label='Preferred Language',
        widget=forms.Select(choices=LANGUAGES)
    )
