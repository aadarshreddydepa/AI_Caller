"use client";

import { Mic, PhoneOff, Play, RotateCcw, Volume2, Waves } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { PageHeader } from "@/components/layout/page-header";
import { PageError, PageLoading } from "@/components/ui/states";
import { useApi } from "@/hooks/use-api";
import { apiRequest } from "@/lib/api";
import { useWorkspace } from "@/providers/workspace-provider";

type VoiceStatus = { available:boolean; model:string };
type TranscriptItem = { speaker:"agent"|"caller"; text:string };
type RecognitionInstance = {
  continuous:boolean; interimResults:boolean; lang:string;
  start:()=>void; stop:()=>void;
  onresult:((event:{ results:ArrayLike<ArrayLike<{ transcript:string }>> })=>void)|null;
  onend:(()=>void)|null; onerror:((event:{ error:string })=>void)|null;
};
type RecognitionConstructor = new () => RecognitionInstance;

export function VoiceTestPage() {
  const { businessId } = useWorkspace();
  const { data:status, error, refresh } = useApi<VoiceStatus>(`/backend/api/v1/businesses/${businessId}/voice/status/`);
  const recognition = useRef<RecognitionInstance|null>(null);
  const callId = useRef<string|null>(null);
  const [supported, setSupported] = useState<boolean|null>(null);
  const [hasActiveCall, setHasActiveCall] = useState(false);
  const [state, setState] = useState<"idle"|"starting"|"listening"|"thinking"|"speaking"|"ended">("idle");
  const [transcript, setTranscript] = useState<TranscriptItem[]>([]);
  const [message, setMessage] = useState("");

  const speak = useCallback((text:string) => {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.onstart = () => setState("speaking");
    utterance.onend = () => setState("idle");
    utterance.onerror = () => setState("idle");
    window.speechSynthesis.speak(utterance);
  }, []);

  const sendTurn = useCallback(async (text:string) => {
    if (!callId.current) return;
    setState("thinking"); setMessage("");
    setTranscript(items => [...items, { speaker:"caller", text }]);
    try {
      const response = await apiRequest<{ reply:string }>(`/backend/api/v1/businesses/${businessId}/voice/calls/${callId.current}/turns/`, { method:"POST", body:JSON.stringify({ text }) });
      setTranscript(items => [...items, { speaker:"agent", text:response.reply }]);
      speak(response.reply);
    } catch (reason) {
      setState("idle");
      setMessage(reason instanceof Error ? reason.message : "The AI could not respond.");
    }
  }, [businessId, speak]);

  useEffect(() => {
    const speechWindow = window as typeof window & { SpeechRecognition?:RecognitionConstructor; webkitSpeechRecognition?:RecognitionConstructor };
    const Recognition = speechWindow.SpeechRecognition || speechWindow.webkitSpeechRecognition;
    queueMicrotask(() => setSupported(Boolean(Recognition && "speechSynthesis" in window)));
    if (!Recognition || !("speechSynthesis" in window)) return;
    const instance = new Recognition();
    instance.continuous = false; instance.interimResults = false; instance.lang = "en-IN";
    instance.onresult = (event) => {
      const text = event.results[event.results.length - 1][0].transcript.trim();
      if (text) void sendTurn(text);
    };
    instance.onerror = (event) => {
      setState("idle");
      setMessage(event.error === "not-allowed" ? "Microphone permission was not granted." : "I could not understand that. Please try again.");
    };
    instance.onend = () => setState(current => current === "listening" ? "idle" : current);
    recognition.current = instance;
    return () => { instance.stop(); window.speechSynthesis.cancel(); };
  }, [sendTurn]);

  async function startTest() {
    if (!status?.available) return;
    setState("starting"); setMessage(""); setTranscript([]);
    try {
      const response = await apiRequest<{ call_id:string; reply:string }>(`/backend/api/v1/businesses/${businessId}/voice/calls/`, { method:"POST" });
      callId.current = response.call_id; setHasActiveCall(true);
      setTranscript([{ speaker:"agent", text:response.reply }]);
      speak(response.reply);
    } catch (reason) {
      setState("idle");
      setMessage(reason instanceof Error ? reason.message : "Could not start the voice test.");
    }
  }

  function listen() {
    if (!callId.current || !recognition.current || state === "thinking" || state === "speaking") return;
    setMessage(""); setState("listening"); recognition.current.start();
  }

  async function endTest() {
    window.speechSynthesis.cancel(); recognition.current?.stop();
    if (callId.current) {
      try { await apiRequest(`/backend/api/v1/businesses/${businessId}/voice/calls/${callId.current}/complete/`, { method:"POST" }); } catch { /* transcript remains saved */ }
    }
    callId.current = null; setHasActiveCall(false); setState("ended");
    setMessage("Test ended. The transcript and lead record were saved to your workspace.");
  }

  if (error) return <PageError message={error}/>;
  if (!status || supported === null) return <PageLoading/>;
  const title = !hasActiveCall ? (state === "ended" ? "Test complete" : "Ready to talk") : state === "listening" ? "Listening…" : state === "thinking" ? "Thinking…" : state === "speaking" ? "Speaking…" : "Ready for your next question";
  return <div className="content voice-page"><PageHeader title="Test your agent" subtitle="Speak naturally. Your browser transcribes your voice, the local AI responds, and the reply is spoken back."/>
    {!supported && <section className="panel voice-notice"><strong>This browser does not support local speech recognition.</strong><span>Use Chrome or Brave on desktop and allow microphone access to run the voice test.</span></section>}
    {supported && !status.available && <section className="panel voice-notice"><strong>Local model not ready</strong><span>Start Ollama, then run <code>ollama pull {status.model}</code>. Once it finishes, refresh this status.</span><button className="secondary-button" onClick={() => void refresh()}>Check again</button></section>}
    {supported && status.available && <section className="voice-layout"><article className="panel voice-console"><div className="voice-model"><span className="voice-dot"/><div><strong>{status.model}</strong><small>Local conversational model</small></div></div><div className={`voice-orb ${state}`}><Waves size={42}/></div><h2>{title}</h2><p>{hasActiveCall ? "Speak after the agent finishes, then tap the microphone for your next turn." : "Start a test to hear the agent’s greeting."}</p><div className="voice-actions">{!hasActiveCall ? <button className="primary-button voice-start" onClick={() => void startTest()} disabled={state === "starting"}><Play size={17}/>{state === "ended" ? "Start another test" : "Start voice test"}</button> : <><button className={`mic-button ${state === "listening" ? "active" : ""}`} onClick={listen} disabled={state === "thinking" || state === "speaking"}><Mic size={20}/>{state === "listening" ? "Listening…" : "Speak"}</button><button className="secondary-button" onClick={() => window.speechSynthesis.cancel()}><Volume2 size={16}/>Stop speech</button><button className="danger-button" onClick={() => void endTest()}><PhoneOff size={16}/>End test</button></>}</div>{message && <p className="voice-message">{message}</p>}</article><article className="panel voice-transcript"><div className="panel-heading"><div><h2>Live transcript</h2><p>Every turn is saved with this test call.</p></div><RotateCcw size={16}/></div><div className="transcript-list">{transcript.length === 0 ? <p className="transcript-empty">Your conversation will appear here.</p> : transcript.map((item,index) => <div className={`transcript-turn ${item.speaker}`} key={`${item.speaker}-${index}`}><span>{item.speaker === "agent" ? "AI agent" : "You"}</span><p>{item.text}</p></div>)}</div></article></section>}
  </div>;
}
