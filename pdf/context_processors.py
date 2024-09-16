from django.conf import settings
import json


def site_settings(request):
    with open(settings.BASE_DIR / "site.json", "r") as file:
        data =  json.load(file)
    return data
