from django.urls import path
from .views import (
    BusinessCallDetail, BusinessCalls, BusinessDetail, BusinessLeads, CallComplete,
    CallLead, CallStart, CallTurn, DashboardSummary, SessionInfo, SessionLogin, SessionLogout, SessionSignup,
)

urlpatterns = [
    path("auth/session/", SessionInfo.as_view()),
    path("auth/login/", SessionLogin.as_view()),
    path("auth/signup/", SessionSignup.as_view()),
    path("auth/logout/", SessionLogout.as_view()),
    path("businesses/<slug:slug>/", BusinessDetail.as_view()),
    path("businesses/<uuid:business_id>/dashboard/", DashboardSummary.as_view()),
    path("businesses/<uuid:business_id>/calls/", BusinessCalls.as_view()),
    path("businesses/<uuid:business_id>/calls/<uuid:call_id>/", BusinessCallDetail.as_view()),
    path("businesses/<uuid:business_id>/leads/", BusinessLeads.as_view()),
    path("calls/", CallStart.as_view()),
    path("calls/<uuid:call_id>/turns/", CallTurn.as_view()),
    path("calls/<uuid:call_id>/lead/", CallLead.as_view()),
    path("calls/<uuid:call_id>/complete/", CallComplete.as_view()),
]
