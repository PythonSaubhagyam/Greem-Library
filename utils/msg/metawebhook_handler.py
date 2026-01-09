from decouple import config
from django.http import HttpResponse
from rest_framework.response import Response
from utils.responses import HTTPCODE

def webhook_message(request):
  VERIFY_TOKEN = config('VERIFY_TOKEN')
  mode = request.GET.get("hub.mode")
  token = request.GET.get("hub.verify_token")
  challenge = request.GET.get("hub.challenge")
  if mode and token:
    # print(mode == "subscribe" and token == VERIFY_TOKEN)
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("=============== Webhook worked ===============")
        return HttpResponse(challenge, status=HTTPCODE.OK)
    else:
        print("Please check the webhook")
        return HttpResponse({"status": "error", "message": "Check the webhook"}, status = 403), 
    
  else:
    print("Please check the application")
    return HttpResponse({"status": "error", "message": "Check the application"}, status = 404)