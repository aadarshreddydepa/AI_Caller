from dataclasses import dataclass
from django.utils import timezone
from .tasks import notify_owner_task
from .models import Call, ConversationTurn, FAQ, Lead


ESCALATION_TERMS = ("owner", "human", "person", "urgent", "complaint", "emergency")


@dataclass
class AgentReply:
    text: str
    should_capture_lead: bool = False
    escalation_requested: bool = False


class Receptionist:
    """Deterministic v1. It only speaks from approved business content."""

    def reply(self, call: Call, caller_text: str) -> AgentReply:
        normalized = caller_text.lower().strip()
        ConversationTurn.objects.create(call=call, speaker="caller", text=caller_text)

        if any(term in normalized for term in ESCALATION_TERMS):
            call.status = Call.Status.ESCALATED
            call.save(update_fields=["status"])
            answer = ("I can arrange for the owner to call you. Please share your name, "
                      "phone number, and a convenient time to call.")
            return self._record(call, AgentReply(answer, True, True))

        faq = self._find_faq(call, normalized)
        if faq:
            return self._record(call, AgentReply(faq.answer, True))

        services = call.business.services.filter(active=True)
        service = next((item for item in services if item.name.lower() in normalized), None)
        if service:
            price = ""
            if service.price_from is not None:
                price = f" Prices start from {service.price_from}; {service.price_note}".strip()
            answer = f"{service.name}: {service.description}{price} Would you like the owner to call you about this?"
            return self._record(call, AgentReply(answer, True))

        answer = ("I want to make sure you receive the correct information. I can ask the owner "
                  "to call you back. Please share your name, phone number, and what you need help with.")
        return self._record(call, AgentReply(answer, True))

    def _find_faq(self, call: Call, text: str):
        for faq in FAQ.objects.filter(business=call.business, active=True):
            keywords = [word.strip().lower() for word in faq.keywords.split(",") if word.strip()]
            if any(keyword in text for keyword in keywords):
                return faq
        return None

    def _record(self, call: Call, response: AgentReply) -> AgentReply:
        ConversationTurn.objects.create(call=call, speaker="agent", text=response.text)
        return response


def create_or_update_lead(call: Call, payload: dict) -> Lead:
    lead, _ = Lead.objects.update_or_create(
        call=call,
        defaults={
            "requirement": payload.get("requirement", ""),
            "location": payload.get("location", ""),
            "preferred_callback_time": payload.get("preferred_callback_time", ""),
            "urgency": payload.get("urgency", Lead.Urgency.NORMAL),
            "owner_callback_requested": payload.get("owner_callback_requested", True),
        },
    )
    return lead


def complete_call(call: Call) -> Lead:
    lead, _ = Lead.objects.get_or_create(call=call)
    caller_text = " ".join(call.turns.filter(speaker="caller").values_list("text", flat=True))
    lead.summary = (
        f"Caller: {call.caller_name or 'not provided'} ({call.caller_phone or 'not provided'}). "
        f"Requirement: {lead.requirement or caller_text or 'not provided'}. "
        f"Location: {lead.location or 'not provided'}. "
        f"Callback: {lead.preferred_callback_time or 'not provided'}. Urgency: {lead.urgency}."
    )
    lead.save(update_fields=["summary"])
    if call.status == Call.Status.ACTIVE:
        call.status = Call.Status.COMPLETED
    call.ended_at = timezone.now()
    call.save(update_fields=["status", "ended_at"])
    notify_owner_task.delay(lead.id)
    return lead
