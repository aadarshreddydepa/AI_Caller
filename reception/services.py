from dataclasses import dataclass
from django.utils import timezone
from .tasks import notify_owner_task
from .models import CallSession, ConversationTurn, FAQ, Lead, NotificationDelivery


ESCALATION_TERMS = ("owner", "human", "person", "urgent", "complaint", "emergency")


@dataclass
class AgentReply:
    text: str
    should_capture_lead: bool = False
    escalation_requested: bool = False


class Receptionist:
    """Deterministic v1. It only speaks from approved business content."""

    def reply(self, call: CallSession, caller_text: str) -> AgentReply:
        normalized = caller_text.lower().strip()
        self._create_turn(call, ConversationTurn.Speaker.CALLER, caller_text)

        if any(term in normalized for term in ESCALATION_TERMS):
            call.escalated = True
            call.save(update_fields=["escalated"])
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

    def _find_faq(self, call: CallSession, text: str):
        for faq in FAQ.objects.filter(business=call.business, active=True):
            keywords = [word.strip().lower() for word in faq.keywords.split(",") if word.strip()]
            if any(keyword in text for keyword in keywords):
                return faq
        return None

    def _record(self, call: CallSession, response: AgentReply) -> AgentReply:
        self._create_turn(call, ConversationTurn.Speaker.AGENT, response.text)
        return response

    @staticmethod
    def _create_turn(call: CallSession, speaker: str, text: str) -> ConversationTurn:
        next_sequence = (call.turns.order_by("-sequence_number").values_list("sequence_number", flat=True).first() or 0) + 1
        return ConversationTurn.objects.create(
            business=call.business, call=call, sequence_number=next_sequence,
            speaker=speaker, text=text,
        )


def create_or_update_lead(call: CallSession, payload: dict) -> Lead:
    lead, _ = Lead.objects.update_or_create(
        call=call,
        defaults={
            "business": call.business,
            "caller_name": payload.get("caller_name", call.caller_name),
            "caller_phone": payload.get("caller_phone", call.caller_phone),
            "requirement": payload.get("requirement", ""),
            "location": payload.get("location", ""),
            "preferred_callback_time": payload.get("preferred_callback_time", ""),
            "urgency": payload.get("urgency", Lead.Urgency.NORMAL),
            "owner_callback_requested": payload.get("owner_callback_requested", True),
        },
    )
    return lead


def complete_call(call: CallSession) -> Lead:
    lead, _ = Lead.objects.get_or_create(
        call=call,
        defaults={"business": call.business, "caller_name": call.caller_name, "caller_phone": call.caller_phone},
    )
    caller_text = " ".join(call.turns.filter(speaker="caller").values_list("text", flat=True))
    lead.summary = (
        f"Caller: {call.caller_name or 'not provided'} ({call.caller_phone or 'not provided'}). "
        f"Requirement: {lead.requirement or caller_text or 'not provided'}. "
        f"Location: {lead.location or 'not provided'}. "
        f"Callback: {lead.preferred_callback_time or 'not provided'}. Urgency: {lead.urgency}."
    )
    lead.save(update_fields=["summary"])
    if call.status == CallSession.Status.ACTIVE:
        call.status = CallSession.Status.COMPLETED
    call.ended_at = timezone.now()
    call.save(update_fields=["status", "ended_at"])
    for endpoint in call.business.notification_endpoints.filter(enabled=True):
        delivery = NotificationDelivery.objects.create(
            business=call.business, call=call, lead=lead, endpoint=endpoint
        )
        notify_owner_task.delay(str(delivery.id))
    return lead
