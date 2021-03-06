from __future__ import unicode_literals

import pytz
from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseBadRequest
from users.models import Profile
from booking.models import Appointment


def index(request):
    if request.method != 'GET':
        return HttpResponseBadRequest()

    response = Profile.objects.index(request)

    return render(request, 'users/index.html', response)


def login(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    valid, response = Profile.objects.login_register(request, 'login')

    if not valid:
        for error in response:
            messages.error(request, error)
        return redirect('users:index')

    profile = Profile.objects.get(pk=response)
    messages.success(request, 'Welcome back, %s!' % profile.user.first_name)
    request.session['id'] = response
    return redirect('users:index')


def register(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    valid, response = Profile.objects.login_register(request, 'register')

    if not valid:
        for error in response:
            messages.error(request, error)
        return redirect('users:index')

    messages.success(request, 'You have successfully created an account.')
    request.session['id'] = response

    return redirect('users:index')


def logout(request):
    if request.method != 'GET':
        return HttpResponseBadRequest()

    del request.session['id']
    messages.success(request, 'You have successfully signed out.')

    return redirect('users:index')


def login_redirect(request):
    if request.method != 'GET':
        return HttpResponseBadRequest()

    messages.info(
        request,
        'You must sign in or register to select an appointment slot.',
    )
    return redirect('users:index')


def edit_profile(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    valid, response = Profile.objects.edit_profile(request)

    if valid:
        messages.success(request, response)
    else:
        for error in response:
            messages.error(request, error)

    return redirect('users:index')


def edit_password(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    valid, response = Profile.objects.edit_password(request)

    if valid:
        messages.success(
            request,
            'You have successfully updated your password.',
        )
    else:
        for error in response:
            messages.error(request, error)

    return redirect('users:index')


def edit_massage_type(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    valid, response = Profile.objects.edit_massage_type(request)

    if valid:
        messages.success(request, response)
    else:
        for error in response:
            messages.error(request, error)

    return HttpResponse(response)


def search_by_name(request):
    if request.method != 'GET':
        return HttpResponseBadRequest()

    valid, response = Profile.objects.search_by_name(request)

    if not valid:
        return HttpResponseBadRequest()
    elif not response['profiles']:
        return HttpResponse(status=204)

    return render(request, 'users/dropdown.html', response)


def delete_profile(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    valid, response = Profile.objects.delete_profile(request)

    if not valid:
        return HttpResponse(response, status=500)

    return HttpResponse(response, status=200)


######################
# FOR DEBUG USE ONLY #
######################

from django.http import HttpResponse
from django.contrib.sessions.models import Session

def clear_all_sessions(request):
    if request.method != 'GET':
        return HttpResponseBadRequest()

    Session.objects.all().delete()

    return HttpResponse('All sessions cleared.')
