from celery import shared_task
# from django.core.mail import send_mail
import requests
from django.contrib.auth.models import User

# @shared_task
# def send_task_notification(task_id):
#     task = Task.objects.get(id=task_id)
#     subject = f"New task assigned: {task.title}"
#     message = f"You have been assigned a new task: {task.title}\n\nDescription: {task.description}"
#     send_mail(subject, message, "from@example.com", [task.user.email])


@shared_task
def check_website_status():
    url = "http://127.0.0.1:8000/"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"{url} is online!")
        else:
            print(f"{url} is offline. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error checking {url}: {str(e)}")
