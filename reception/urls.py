from django.urls import path
from .views import BusinessDetail, CallComplete, CallLead, CallStart, CallTurn

urlpatterns = [
    path("businesses/<slug:slug>/", BusinessDetail.as_view()),
    path("calls/", CallStart.as_view()),
    path("calls/<uuid:call_id>/turns/", CallTurn.as_view()),
    path("calls/<uuid:call_id>/lead/", CallLead.as_view()),
    path("calls/<uuid:call_id>/complete/", CallComplete.as_view()),
]
