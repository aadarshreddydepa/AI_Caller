import json
from urllib import error, request

from django.conf import settings
from rest_framework.exceptions import APIException

from .models import ConversationTurn


class VoiceModelUnavailable(APIException):
    status_code = 503
    default_detail = "The local voice model is not ready. Start Ollama and download the configured model."
    default_code = "voice_model_unavailable"


def ollama_status():
    try:
        with request.urlopen(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=2) as response:
            models = json.loads(response.read()).get("models", [])
        names = {item.get("name", "") for item in models}
        return {"available": settings.OLLAMA_MODEL in names, "model": settings.OLLAMA_MODEL}
    except (error.URLError, TimeoutError, json.JSONDecodeError):
        return {"available": False, "model": settings.OLLAMA_MODEL}


class VoiceAgent:
    def greeting(self, business):
        return f"Hello, thank you for calling {business.name}. How can I help you today?"

    def reply(self, call, caller_text):
        self._create_turn(call, ConversationTurn.Speaker.CALLER, caller_text)
        payload = {
            "model": settings.OLLAMA_MODEL,
            "stream": False,
            "options": {"temperature": 0.25, "num_predict": 180},
            "messages": self._messages(call),
        }
        try:
            body = json.dumps(payload).encode("utf-8")
            http_request = request.Request(
                f"{settings.OLLAMA_BASE_URL}/api/chat", data=body,
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with request.urlopen(http_request, timeout=settings.VOICE_AGENT_TIMEOUT_SECONDS) as response:
                answer = json.loads(response.read()).get("message", {}).get("content", "").strip()
        except (error.URLError, error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            raise VoiceModelUnavailable() from exc
        if not answer:
            raise VoiceModelUnavailable()
        self._create_turn(call, ConversationTurn.Speaker.AGENT, answer)
        return answer

    def _messages(self, call):
        services = "\n".join(
            f"- {service.name}: {service.description}" for service in call.business.services.filter(active=True)
        ) or "No services are configured."
        faqs = "\n".join(
            f"- Q: {faq.question}\n  A: {faq.answer}" for faq in call.business.faqs.filter(active=True)
        ) or "No FAQ answers are configured."
        system = f"""You are the friendly phone receptionist for {call.business.name}.
Only use the approved information below. Do not invent prices, availability, policies, or promises.
Keep each response concise and natural for speech: no markdown, no bullet lists, and usually under 55 words.
If the caller asks for the owner, needs something not covered, or asks to book, politely collect their name, phone number, requirement, and preferred callback time.

Business description: {call.business.description or 'Not provided.'}
Approved services:\n{services}
Approved FAQs:\n{faqs}"""
        history = [{"role": "system", "content": system}]
        for turn in call.turns.order_by("sequence_number").all()[:16]:
            if turn.speaker == ConversationTurn.Speaker.SYSTEM:
                continue
            history.append({"role": "assistant" if turn.speaker == ConversationTurn.Speaker.AGENT else "user", "content": turn.text})
        return history

    @staticmethod
    def _create_turn(call, speaker, text):
        next_sequence = (call.turns.order_by("-sequence_number").values_list("sequence_number", flat=True).first() or 0) + 1
        return ConversationTurn.objects.create(
            business=call.business, call=call, sequence_number=next_sequence,
            speaker=speaker, text=text,
        )
