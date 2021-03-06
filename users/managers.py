from __future__ import unicode_literals

import re
import random
import pytz
from datetime import datetime, timedelta

from django.db.models import Manager
from django.contrib.auth.models import User, UserManager
from django.core.exceptions import MultipleObjectsReturned
from django.contrib.auth.hashers import make_password
from pharmasseuse.settings import TIME_ZONE
from users import models
from booking.models import Appointment

tz = pytz.timezone(TIME_ZONE)

EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9.!#$%&’*+\/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$')

class ProfileManager(Manager):
    def index(self, request):
        profile = models.Profile.objects.get(user__pk=request.session['id']) \
            if 'id' in request.session else None

        appts = []
        profiles = []
        next_scheduled = None

        if profile != None:
            try:
                next_scheduled = Appointment.objects.filter(
                    profile=profile,
                    date_end__gt=datetime.now(pytz.utc),
                ).first()
            except Appointment.DoesNotExist:
                next_scheduled = None

            profiles = models.Profile.objects.all()

            today = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)

            manage_appts = Appointment.objects \
                .filter(date_end__gt=datetime.now(pytz.utc)) \
                    .exclude(profile__user=None)

            appts = Appointment.objects.filter(
                date_start__gte=today.astimezone(pytz.utc) + timedelta(days=1),
                profile__isnull=True,
                black_out=False,
            ).order_by('date_start')

            try:
                date_begin = appts[0].date_start
                date_begin = date_begin.astimezone(tz)
                date_begin = date_begin.replace(hour=0, minute=0, second=0, microsecond=0)
            except IndexError:
                date_begin = today

            first_available = Appointment.objects.filter(
                date_start__gte=today.astimezone(pytz.utc) + timedelta(days=1),
                profile__isnull=True).first()

            prev_appt = Appointment.objects.filter(
                date_start__lt=date_begin.astimezone(pytz.utc),
                date_start__gte=today.astimezone(pytz.utc) + timedelta(days=1),
                profile__isnull=True,
            ).order_by('-date_start').first()

            next_appt = Appointment.objects \
                .filter(
                    date_start__gte=date_begin.astimezone(pytz.utc) + timedelta(days=1),
                    profile__isnull=True,
                ).filter(date_start__gte=today.astimezone(pytz.utc) + timedelta(days=1)) \
                .order_by('date_start').first()

            errors = []

            try:
                prev = prev_appt.date_start if prev_appt else None
            except IndexError:
                prev = date_begin - timedelta(days=1)

            try:
                next = next_appt.date_start if next_appt else None
            except IndexError:
                next = date_begin + timedelta(days=1)

            return {
                'profile': profile,
                'next_appt': next_scheduled,
                'appts': manage_appts,
                'TIME_ZONE': TIME_ZONE,
                'profiles': profiles,
                'date': first_available.date_start,
                'prev': prev,
                'next': next,
            }

        return {}


    def login_register(self, request, action):
        errors = []

        """
        Validate user input
        """
        # checks if user is registering
        if action == 'register':
            if len(request.POST['first-name']) == 0 or \
                len(request.POST['last-name']) == 0:
                errors.append('Please enter your first and last name.')
            if len(request.POST['email']) == 0:
                errors.append('Please enter your email.')
            elif not EMAIL_REGEX.match(request.POST['email']):
                errors.append('Please enter a valid email.')
            if len(request.POST['phone']) == 0:
                errors.append('Please enter your phone number.')
            if len(request.POST['password']) < 8:
                errors.append(
                    'Please enter a password that contains at least 8 characters.')
            if request.POST['confirm-password'] != request.POST['password']:
                errors.append('Passwords must match.')
        # checks if user is logging in
        elif action == 'login':
            if not EMAIL_REGEX.match(request.POST['email']):
                errors.append('Please enter a valid email.')

        """
        Login/Register
        """
        if not errors:
            # checks if email exists in database and
            # stores any User associated with it
            try:
                user_by_email = User.objects.get(email=request.POST['email'])
            except User.DoesNotExist:
                user_by_email = None
            email_exists = user_by_email != None

            # checks if user is registering
            if action == 'register':
                # checks if registering user email already exists
                if email_exists:
                    errors.append(
                        'A user account with this email already exists.')
                    return (False, errors)
                # otherwise bcrypt password and create user
                user = User.objects.create_user(
                    username=request.POST['email'],
                    email=request.POST['email'],
                    password=request.POST['password'],
                    first_name=request.POST['first-name'],
                    last_name=request.POST['last-name'],
                )
                models.Profile.objects.create(
                    user=user,
                    phone=request.POST['phone'],
                )
                return (True, user.id)
            elif action == 'login':
                # compares user password with posted password
                if email_exists:
                    correct_pw = user_by_email.check_password(
                        request.POST['password'])
                else:
                    correct_pw = False
                if not correct_pw or not email_exists:
                    errors.append(
                        'The email and password combination you entered does not exist in ' + \
                        'our database. Please register or try again.')
                    return (False, errors)
                # grabs user id to store in session in views
                if correct_pw:
                    return (True, user_by_email.id)
            else:
                errors.append('Invalid action.')

        return (False, errors)


    def edit_profile(self, request):
        errors = []

        if len(request.POST['first-name']) == 0 or \
            len(request.POST['last-name']) == 0:
            errors.append('Please enter your first and last name.')
        if len(request.POST['email']) == 0:
            errors.append('Please enter your email.')
        elif not EMAIL_REGEX.match(request.POST['email']):
            errors.append('Please enter a valid email.')
        if len(request.POST['phone']) == 0:
            errors.append('Please enter your phone number.')

        if not errors:
            profile_id = int(request.POST['profile-id'])
            profile = models.Profile.objects.get(pk=profile_id)
            user = profile.user

            user.first_name = request.POST['first-name']
            user.last_name = request.POST['last-name']
            user.email = request.POST['email']
            profile.phone = request.POST['phone']

            user.save()
            profile.save()

            name = 'your' if request.session['id'] == profile_id \
                else '%s %s\'s' % (user.first_name, user.last_name)
            message = 'You have successfully updated %s contact info.' % name

            return (True, message)

        return (False, errors)

    def edit_password(self, request):
        errors = []

        user = User.objects.get(pk=request.POST['user-id'])
        correct_pw = user.check_password(request.POST['current-password'])

        if not correct_pw:
            errors.append('The current password you entered was not correct.')
        if len(request.POST['new-password']) < 8:
            errors.append(
                'Please enter a password that contains at least 8 characters.')
        if request.POST['password-confirm'] != request.POST['new-password']:
            errors.append('Passwords must match.')

        if not errors:
            user.password = make_password(request.POST['new-password'])
            user.save()

            return (True, user)

        return (False, errors)

    def edit_massage_type(self, request):
        errors = []

        try:
            profile_id = int(request.POST['profile-id'])
            profile = models.Profile.objects.get(pk=profile_id)
            appt = Appointment.objects.get(
                profile=profile,
                date_end__gt=datetime.now(pytz.utc),
            )
            massage = request.POST['massage']
        except Exception as exception:
            errors.append('There was an error changing the massage type.')
            errors.append(exception)

        if not errors:
            first_name = profile.user.first_name
            last_name = profile.user.last_name

            appt.massage = massage
            appt.save()

            name = 'your' if request.session['id'] == profile_id \
                else '%s %s\'s' % (first_name, last_name)
            message = 'You have successfully updated %s massage type.' % name

            return (True, message)

        return (False, errors)

    def search_by_name(self, request):
        # get URL parameters
        first_name = request.GET.get('first-name', '')
        last_name = request.GET.get('last-name', '')

        # define variables
        profiles = []
        max_results = 5
        filters = {}

        # define filters
        if first_name:
            filters['user__first_name__icontains'] = first_name
        if last_name:
            filters['user__last_name__icontains'] = last_name

        # retrieve today's date as datetime object
        today = datetime.now(pytz.timezone(TIME_ZONE)).replace(
            hour=0, minute=0, second=0, microsecond=0)

        # delete empty slots today or earlier
        Appointment.objects.filter(
            date_start__lt=today + timedelta(days=1),
            profile__isnull=True,
        ).delete()

        # delete booked appointments before today
        Appointment.objects.filter(
            date_start__lt=today,
            profile__isnull=False,
        ).delete()

        # retrive Profile objects
        profiles = [] if not first_name and not last_name else \
            models.Profile.objects \
            .filter(appointment=None, **filters)[:max_results]

        return (True, {'profiles': profiles})


    def add_profile(self, request):
        # get POST data
        first_name = request.POST.get('first-name')
        last_name = request.POST.get('last-name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '000-000-0000')

        # validate input
        errors = []
        if not first_name:
            errors.append('Please enter a first name.')
        if not last_name:
            errors.append('Please enter a last name.')
        if not email:
            errors.append('Please enter an email.')
        if not phone:
            errors.append('Please enter a phone number.')
        if errors:
            return (False, errors)

        # create user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=''.join([random.SystemRandom().choice(
                'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') \
                for i in range(16)]),
            first_name=first_name,
            last_name=last_name,
        )

        # create profile
        profile = models.Profile.objects.create(
            user=user,
            phone=phone,
        )

        return (True, profile)


    def delete_profile(self, request):
        # track errors
        errors = []

        # get POST data
        profile_id = int(request.POST['profile-id'])

        # delete profile along with user associated with it
        try:
            profile = models.Profile.objects.get(pk=profile_id)
            appts = Appointment.objects.filter(profile__pk=profile_id)

            for appt in appts:
                appt.profile = None
                appt.massage = None
                appt.save()

            profile.user.delete()
            profile.delete()
        except:
            return (False, 'There was an error deleting the user\'s profile.')

        return (True, 'The user\'s profile has been deleted successfully. ' +
            'The page will now refresh in 5 seconds.')

