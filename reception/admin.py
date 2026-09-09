from django.contrib import admin
from .models import Business, Call, ConversationTurn, FAQ, Lead, Service

admin.site.register([Business, Service, FAQ, Call, ConversationTurn, Lead])
