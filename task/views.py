from django.core.exceptions import ImproperlyConfigured, TooManyFieldsSent
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .forms import TaskForm
from .models import Task
import requests

# Authentication stuffs

def signupuser(request):
    if request.method == 'GET':
        return render(request, 'task/signupuser.html', {'form':UserCreationForm()})
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(request.POST['username'], password=request.POST['password1'])
                user.save()
                login(request, user)
                return redirect('currenttasks')
            except IntegrityError:
                return render(request, 'task/signupuser.html', {'form':UserCreationForm(), 'passerror':'Username has already been taken!'})
        else:
            return render(request, 'task/signupuser.html', {'form':UserCreationForm(), 'passerror':'Hey! Your password did not matched'})

def loginuser(request):
    if request.method == 'GET':
        return render(request, 'task/login.html', {'form':AuthenticationForm()})
    else:
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'task/login.html', {'form':AuthenticationForm(), 'passerror':'Please check your username and password!'})
        else:
            login(request, user)
            return redirect('currenttasks')

@login_required
def logoutuser(request):
    if request.method == 'POST':
        logout(request)
        return redirect('home')

# Reporting Issue

@login_required 
def report_issue(request):
    session_user = str(request.user)
    if request.method == 'GET':
        return render(request, 'task/report_issue.html', {'form': TaskForm(), 'user': session_user})
    else:
        try:
            url = 'https://dev62107.service-now.com/api/now/table/incident'

            user = 'rest.user'
            pwd = 'Rest@1234'

            short_description = request.POST.get('title')
            description = request.POST.get('memo')
            urgency = '3'
            if(request.POST.get('important') == 'on'):
                urgency = '1'

            headers = {"Content-Type":"application/json","Accept":"application/json"}
            response = requests.post(url, auth=(user, pwd), headers=headers ,data="{\"caller_id\":\""+ session_user +"\",\"short_description\":\""+ short_description +"\",\"description\":\""+ description +"\",\"urgency\":\""+ urgency +"\"}")

            # Check for HTTP codes other than 200
            # if response.status_code != 200: 
            #     print('Status:', response.status_code, 'Headers:', response.headers, 'Error Response:',response.json())
            #     exit()

            # Decode the JSON response into a dictionary and use the data
            # data = response.json()
            # print(data)

            return render(request, 'task/report_issue.html', {'form': TaskForm(), 'success': 'Incident Created Successfully !!'})
        except ValueError:
            return render(request, 'task/report_issue.html', {'form': TaskForm(), 'passerror': 'Bad value entered. Please try again!'})

# Tasks

def home(request):
    return render(request, 'task/home.html')

@login_required 
def createtask(request):
    if request.method == 'GET':
        return render(request, 'task/createtask.html', {'form': TaskForm()})
    else:
        try:
            form = TaskForm(request.POST)
            newtask = form.save(commit=False)
            newtask.user = request.user
            newtask.save()
            return redirect('currenttasks')
        except ValueError:
            return render(request, 'task/createtask.html', {'form': TaskForm(), 'passerror': 'Bad value entered. Please try again!'})

@login_required 
def currenttasks(request):
    tasks = Task.objects.filter(user=request.user, datecompleted__isnull=True)
    return render(request, 'task/currenttasks.html', {'tasks': tasks})

@login_required
def viewtask(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk, user=request.user)
    if request.method == 'GET':
        form = TaskForm(instance=task)
        return render(request, 'task/viewtask.html', {'task': task, 'form': form})
    else:
        try:
            form = TaskForm(request.POST, instance=task)
            form.save()
            return redirect('currenttasks')
        except ValueError:
            return render(request, 'task/viewtask.html', {'task': task, 'form': form, 'passerror': 'Bad value entered. Please try again!'})

@login_required
def completetask(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk, user=request.user)
    if request.method == 'POST':
        task.datecompleted = timezone.now()
        task.save()
        return redirect('currenttasks')

@login_required
def deletetask(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk, user=request.user)
    if request.method == 'POST':
        task.delete()
        return redirect('currenttasks')

@login_required
def completedtasks(request):
    tasks = Task.objects.filter(user=request.user, datecompleted__isnull=False).order_by('-datecompleted')
    return render(request, 'task/completedtasks.html', {'tasks': tasks})
