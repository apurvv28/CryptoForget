import React, { useState, useRef, useEffect, useCallback } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  ArrowUpIcon,
  Mic,
  MicOff,
  Sparkles,
  ShieldCheck,
  ShieldAlert,
  Bot,
  User as UserIcon,
  Trash2,
  RefreshCw,
  Layers,
  Fingerprint,
  SlidersHorizontal,
  X,
  History,
  Database,
  CheckCircle2,
} from "lucide-react";
import DeletionProgressModal from "../deletion/DeletionProgressModal";

interface Message {
  id?: string;
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
}

interface ConsentStatus {
  training_consent: boolean;
  purpose: string;
  scope: string;
  policy_version: string;
  last_updated: string | null;
  events_count: number;
  history: Array<{
    id: number;
    status: string;
    effective_timestamp: string;
    audit_hash: string;
  }>;
}

interface DataInventory {
  total_messages_stored: number;
  training_eligible_messages: number;
  messages_used_in_model: number;
  training_consent_active: boolean;
  categories: Array<{
    category: string;
    purpose: string;
    storage_location: string;
    retention_period: string;
    training_eligible: boolean;
    count: number;
  }>;
}

interface AutoResizeProps {
  minHeight: number;
  maxHeight?: number;
}

function useAutoResizeTextarea({ minHeight, maxHeight }: AutoResizeProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustHeight = useCallback(
    (reset?: boolean) => {
      const textarea = textareaRef.current;
      if (!textarea) return;

      if (reset) {
        textarea.style.height = `${minHeight}px`;
        return;
      }

      textarea.style.height = `${minHeight}px`;
      const newHeight = Math.max(
        minHeight,
        Math.min(textarea.scrollHeight, maxHeight ?? Infinity)
      );
      textarea.style.height = `${newHeight}px`;
    },
    [minHeight, maxHeight]
  );

  useEffect(() => {
    if (textareaRef.current) textareaRef.current.style.height = `${minHeight}px`;
  }, [minHeight]);

  return { textareaRef, adjustHeight };
}

interface ChatInterfaceProps {
  onOpenCertificate?: (certificateId: string) => void;
}

export default function ChatInterface({ onOpenCertificate }: ChatInterfaceProps = {}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);

  // Privacy & Consent state
  const [isPrivacyModalOpen, setIsPrivacyModalOpen] = useState(false);
  const [consentStatus, setConsentStatus] = useState<ConsentStatus | null>(null);
  const [dataInventory, setDataInventory] = useState<DataInventory | null>(null);
  const [isUpdatingConsent, setIsUpdatingConsent] = useState(false);

  // Deletion & Machine Unlearning state
  const [isDeletionModalOpen, setIsDeletionModalOpen] = useState(false);
  const [activeDeletionId, setActiveDeletionId] = useState<string | null>(null);
  const [isInitiatingDeletion, setIsInitiatingDeletion] = useState(false);

  const { textareaRef, adjustHeight } = useAutoResizeTextarea({
    minHeight: 48,
    maxHeight: 140,
  });

  const chatEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  // Fetch consent & inventory on mount
  const fetchPrivacyData = useCallback(async () => {
    try {
      const [cRes, iRes] = await Promise.all([
        fetch("/api/v1/consent"),
        fetch("/api/v1/data-inventory"),
      ]);
      if (cRes.ok) setConsentStatus(await cRes.json());
      if (iRes.ok) setDataInventory(await iRes.json());
    } catch {
      // Backend may be starting
    }
  }, []);

  useEffect(() => {
    fetchPrivacyData();
  }, [fetchPrivacyData]);

  // Scroll to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Voice recognition setup
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = "en-US";

      recognition.onresult = (event: any) => {
        const transcript = Array.from(event.results)
          .map((r: any) => r[0].transcript)
          .join("");
        setInput(transcript);
        adjustHeight();
      };

      recognition.onerror = (_event: any) => {
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, [adjustHeight]);

  const toggleVoice = () => {
    if (!recognitionRef.current) {
      alert("Speech recognition is not supported in this browser. Please use Chrome/Edge.");
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const handleToggleConsent = async (newConsent: boolean) => {
    setIsUpdatingConsent(true);
    try {
      const res = await fetch("/api/v1/consent", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          training_consent: newConsent,
          purpose: "model_training",
          policy_version: "1.0",
        }),
      });
      if (res.ok) {
        const updated = await res.json();
        setConsentStatus(updated);
        await fetchPrivacyData();
      }
    } finally {
      setIsUpdatingConsent(false);
    }
  };

  const handleRequestDeletion = async () => {
    setIsInitiatingDeletion(true);
    try {
      const res = await fetch("/api/v1/deletion-requests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scope: "all_user_data",
          auto_orchestrate: true,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setActiveDeletionId(data.deletion_request_id);
        await fetchPrivacyData();
      } else {
        const err = await res.json();
        alert(`Error: ${err.detail || "Failed to submit deletion request"}`);
      }
    } catch (err: any) {
      alert(`Network error: ${err.message}`);
    } finally {
      setIsInitiatingDeletion(false);
    }
  };

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    const userMsg: Message = {
      role: "user",
      content: trimmed,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    adjustHeight(true);
    setIsLoading(true);

    try {
      const res = await fetch("/api/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: trimmed, max_new_tokens: 60 }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      const botMsg: Message = {
        role: "assistant",
        content: data.response || "No response generated.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, botMsg]);
      await fetchPrivacyData(); // update data inventory count
    } catch (err: any) {
      const errorMsg: Message = {
        role: "assistant",
        content: `Connection error: ${err.message}. Ensure backend is running at http://localhost:8000.`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const setPrompt = (text: string) => {
    setInput(text);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
    setTimeout(adjustHeight, 50);
  };

  const isConsentOn = consentStatus?.training_consent ?? false;

  return (
    <div
      className="relative w-full min-h-screen bg-cover bg-center flex flex-col justify-between"
      style={{
        backgroundImage:
          "url('https://cdn.21st.dev/assets/mirror/c3/c333918af688a4a8a3d004652e6c0ee219457a9d84d380eeb31f513d4b59a09f.png')",
        backgroundAttachment: "fixed",
      }}
    >
      {/* Top Header */}
      <header className="w-full px-6 py-4 flex items-center justify-between border-b border-neutral-800/80 bg-black/40 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-neutral-800 flex items-center justify-center border border-neutral-700">
            <Fingerprint className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <h2 className="text-sm font-semibold tracking-wide text-white">CryptoForget</h2>
            <p className="text-xs text-neutral-400">DistilGPT2-82M • SISA Unlearning Active</p>
          </div>
        </div>

        {/* Privacy & Consent Quick Indicator / Modal trigger */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsPrivacyModalOpen(true)}
            className={cn(
              "flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-medium border transition-all cursor-pointer backdrop-blur-md",
              isConsentOn
                ? "bg-amber-950/70 border-amber-700 text-amber-300 hover:bg-amber-900/60"
                : "bg-emerald-950/60 border-emerald-800 text-emerald-300 hover:bg-emerald-900/60"
            )}
            title="Manage Training Consent & Data Lineage"
          >
            {isConsentOn ? (
              <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
            ) : (
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            )}
            <span>
              Training Consent: <strong>{isConsentOn ? "ON (Consented)" : "OFF (Default)"}</strong>
            </span>
            <SlidersHorizontal className="w-3 h-3 ml-1 text-neutral-400" />
          </button>
        </div>
      </header>

      {/* Main Conversation Stream */}
      <main className="flex-1 w-full max-w-4xl mx-auto px-4 py-6 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="h-full min-h-[50vh] flex flex-col items-center justify-center text-center">
            <div className="w-12 h-12 rounded-2xl bg-neutral-900 border border-neutral-700 flex items-center justify-center mb-4 shadow-xl">
              <Sparkles className="w-6 h-6 text-neutral-300" />
            </div>
            <h1 className="text-3xl font-semibold text-white drop-shadow-sm">
              CryptoForget AI
            </h1>
            <p className="mt-2 text-sm text-neutral-300 max-w-md">
              A privacy-preserving conversational SLM with verifiable machine unlearning and cryptographic certificates.
            </p>
          </div>
        ) : (
          <div className="space-y-4 pb-8">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={cn("flex gap-3 max-w-2xl", {
                  "ml-auto justify-end": m.role === "user",
                  "mr-auto justify-start": m.role === "assistant",
                })}
              >
                {m.role === "assistant" && (
                  <div className="w-8 h-8 rounded-lg bg-neutral-800 border border-neutral-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Bot className="w-4 h-4 text-neutral-300" />
                  </div>
                )}
                <div
                  className={cn("px-4 py-3 rounded-2xl text-sm leading-relaxed backdrop-blur-md", {
                    "bg-white/10 text-white border border-white/15 rounded-br-none":
                      m.role === "user",
                    "bg-black/60 text-neutral-200 border border-neutral-800 rounded-bl-none shadow-lg":
                      m.role === "assistant",
                  })}
                >
                  <p className="whitespace-pre-wrap">{m.content}</p>
                  {m.timestamp && (
                    <span className="block text-[10px] text-neutral-500 mt-1.5 text-right">
                      {m.timestamp}
                    </span>
                  )}
                </div>
                {m.role === "user" && (
                  <div className="w-8 h-8 rounded-lg bg-neutral-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <UserIcon className="w-4 h-4 text-white" />
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-3 mr-auto items-center text-neutral-400 text-xs py-2">
                <div className="w-8 h-8 rounded-lg bg-neutral-800 border border-neutral-700 flex items-center justify-center">
                  <RefreshCw className="w-4 h-4 animate-spin text-neutral-300" />
                </div>
                <span>DistilGPT2 generating response...</span>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>
        )}
      </main>

      {/* Input Composer Section */}
      <footer className="w-full max-w-3xl mx-auto px-4 pb-6 pt-2">
        <div className="relative bg-black/70 backdrop-blur-xl rounded-2xl border border-neutral-800 shadow-2xl">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              adjustHeight();
            }}
            onKeyDown={handleKeyDown}
            placeholder={isListening ? "Listening to your voice..." : "Type your message or request deletion..."}
            className={cn(
              "w-full px-4 pt-3.5 pb-2 resize-none border-none",
              "bg-transparent text-white text-sm",
              "focus-visible:ring-0 focus-visible:ring-offset-0",
              "placeholder:text-neutral-500 min-h-[48px]"
            )}
            style={{ overflow: "hidden" }}
          />

          {/* Action Toolbar */}
          <div className="flex items-center justify-between p-3 border-t border-neutral-800/50">
            <div className="flex items-center gap-1.5">
              {/* Voice Input Toggle Button */}
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleVoice}
                className={cn("h-8 w-8 rounded-lg transition-colors", {
                  "bg-rose-950/80 text-rose-400 border border-rose-800 animate-pulse": isListening,
                  "text-neutral-400 hover:text-white hover:bg-neutral-800": !isListening,
                })}
                title={isListening ? "Stop listening" : "Start voice input"}
              >
                {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </Button>

              {messages.length > 0 && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setMessages([])}
                  className="h-8 w-8 rounded-lg text-neutral-400 hover:text-rose-400 hover:bg-neutral-800"
                  title="Clear chat"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              )}
            </div>

            <div className="flex items-center gap-2">
              <Button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className={cn(
                  "flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all",
                  input.trim() && !isLoading
                    ? "bg-white text-black hover:bg-neutral-200 cursor-pointer shadow-md"
                    : "bg-neutral-800 text-neutral-500 cursor-not-allowed"
                )}
              >
                <ArrowUpIcon className="w-3.5 h-3.5" />
                <span>Send</span>
              </Button>
            </div>
          </div>
        </div>

        {/* Quick Action Pills */}
        <div className="flex items-center justify-center flex-wrap gap-2 mt-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPrompt("Explain how SISA machine unlearning protects my privacy.")}
            className="rounded-full text-xs border-neutral-800 bg-black/40 text-neutral-300 hover:text-white hover:bg-neutral-800"
          >
            <ShieldCheck className="w-3.5 h-3.5 mr-1 text-emerald-400" />
            <span>How SISA Unlearning Works</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setPrompt("What is a verifiable cryptographic deletion certificate?")}
            className="rounded-full text-xs border-neutral-800 bg-black/40 text-neutral-300 hover:text-white hover:bg-neutral-800"
          >
            <Fingerprint className="w-3.5 h-3.5 mr-1 text-blue-400" />
            <span>Verifiable Certificates</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setPrompt("Show me the current SISA sharding and slice configuration.")}
            className="rounded-full text-xs border-neutral-800 bg-black/40 text-neutral-300 hover:text-white hover:bg-neutral-800"
          >
            <Layers className="w-3.5 h-3.5 mr-1 text-purple-400" />
            <span>Shards & Slices</span>
          </Button>
        </div>
      </footer>

      {/* Privacy & Consent Settings Modal (Phase 2) */}
      {isPrivacyModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
          <div className="w-full max-w-xl bg-neutral-900 border border-neutral-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-neutral-800 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-semibold text-white">Privacy & Training Consent</h3>
              </div>
              <button
                onClick={() => setIsPrivacyModalOpen(false)}
                className="text-neutral-400 hover:text-white rounded-lg p-1 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto space-y-6 text-sm">
              {/* Consent Toggle Box */}
              <div className="p-4 rounded-xl border border-neutral-800 bg-neutral-950/50 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-white">Model Training Participation</h4>
                    <p className="text-xs text-neutral-400 mt-0.5">
                      Allow future conversations to be partitioned into SISA shards to fine-tune the model.
                    </p>
                  </div>
                  <Button
                    size="sm"
                    disabled={isUpdatingConsent}
                    onClick={() => handleToggleConsent(!isConsentOn)}
                    className={cn(
                      "px-4 font-semibold text-xs transition-all",
                      isConsentOn
                        ? "bg-rose-950 border border-rose-800 text-rose-300 hover:bg-rose-900"
                        : "bg-emerald-950 border border-emerald-700 text-emerald-300 hover:bg-emerald-900"
                    )}
                  >
                    {isUpdatingConsent
                      ? "Updating..."
                      : isConsentOn
                      ? "Withdraw Consent"
                      : "Grant Consent (Opt-in)"}
                  </Button>
                </div>

                <div className="text-xs text-neutral-400 bg-neutral-900/60 p-3 rounded-lg border border-neutral-800/80 leading-relaxed">
                  <p>
                    <strong>Policy Version:</strong> {consentStatus?.policy_version || "1.0"} •{" "}
                    <strong>Default:</strong> OFF •{" "}
                    <strong>Immediate Exclusion:</strong> Withdrawing consent immediately blocks future conversations from entering any new training manifests.
                  </p>
                </div>
              </div>

              {/* Data Lineage & Inventory Summary (Doc 02 FR-04) */}
              {dataInventory && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-400">
                    <Database className="w-4 h-4 text-neutral-300" />
                    <span>Data Inventory & Lineage</span>
                  </div>

                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div className="p-3 rounded-xl bg-neutral-950/70 border border-neutral-800">
                      <span className="block text-xl font-bold text-white">{dataInventory.total_messages_stored}</span>
                      <span className="text-[11px] text-neutral-400">Total Messages</span>
                    </div>
                    <div className="p-3 rounded-xl bg-neutral-950/70 border border-neutral-800">
                      <span className="block text-xl font-bold text-emerald-400">{dataInventory.training_eligible_messages}</span>
                      <span className="text-[11px] text-neutral-400">Training Eligible</span>
                    </div>
                    <div className="p-3 rounded-xl bg-neutral-950/70 border border-neutral-800">
                      <span className="block text-xl font-bold text-blue-400">{dataInventory.messages_used_in_model}</span>
                      <span className="text-[11px] text-neutral-400">Used in SISA Model</span>
                    </div>
                  </div>

                  <div className="border border-neutral-800 rounded-xl overflow-hidden text-xs">
                    <table className="w-full text-left">
                      <thead className="bg-neutral-950/80 text-neutral-400 border-b border-neutral-800">
                        <tr>
                          <th className="py-2 px-3">Data Category</th>
                          <th className="py-2 px-3">Training Eligible?</th>
                          <th className="py-2 px-3">Retention</th>
                          <th className="py-2 px-3 text-right">Items</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-neutral-800/60 text-neutral-300">
                        {dataInventory.categories.map((cat, idx) => (
                          <tr key={idx} className="hover:bg-neutral-800/20">
                            <td className="py-2 px-3 font-medium text-white">{cat.category}</td>
                            <td className="py-2 px-3">
                              {cat.training_eligible ? (
                                <span className="inline-flex items-center text-amber-400">
                                  <CheckCircle2 className="w-3 h-3 mr-1" /> Eligible
                                </span>
                              ) : (
                                <span className="text-neutral-500">Excluded</span>
                              )}
                            </td>
                            <td className="py-2 px-3 text-neutral-400">{cat.retention_period}</td>
                            <td className="py-2 px-3 text-right font-mono">{cat.count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Consent Event Audit History */}
              {consentStatus && consentStatus.history.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-400">
                    <History className="w-4 h-4 text-neutral-300" />
                    <span>Immutable Consent Event Log</span>
                  </div>
                  <div className="max-h-36 overflow-y-auto space-y-1.5 text-xs">
                    {consentStatus.history.map((ev) => (
                      <div
                        key={ev.id}
                        className="flex items-center justify-between p-2 rounded-lg bg-neutral-950/50 border border-neutral-800/60 font-mono text-[11px]"
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className={cn("px-1.5 py-0.5 rounded text-[10px] uppercase font-bold", {
                              "bg-emerald-950 text-emerald-400 border border-emerald-800": ev.status === "granted",
                              "bg-rose-950 text-rose-400 border border-rose-800": ev.status === "withdrawn",
                            })}
                          >
                            {ev.status}
                          </span>
                          <span className="text-neutral-400 text-[10px]">
                            {new Date(ev.effective_timestamp).toLocaleString()}
                          </span>
                        </div>
                        <span className="text-neutral-500 text-[10px]">{ev.audit_hash.substring(0, 16)}...</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-3 border-t border-neutral-800 flex justify-between items-center bg-neutral-950/40">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setIsPrivacyModalOpen(false);
                  setIsDeletionModalOpen(true);
                }}
                className="text-xs border-rose-900/80 bg-rose-950/40 text-rose-300 hover:bg-rose-900 hover:text-white flex items-center gap-1.5"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Request Data Deletion & SISA Retraining</span>
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsPrivacyModalOpen(false)}
                className="text-xs border-neutral-700 hover:bg-neutral-800"
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Deletion & SISA Selective Unlearning Progress Modal */}
      <DeletionProgressModal
        isOpen={isDeletionModalOpen}
        onClose={() => setIsDeletionModalOpen(false)}
        activeDeletionId={activeDeletionId}
        onRequestDeletion={handleRequestDeletion}
        isInitiating={isInitiatingDeletion}
        onRefreshDataInventory={fetchPrivacyData}
        onOpenCertificate={onOpenCertificate}
      />
    </div>
  );
}
