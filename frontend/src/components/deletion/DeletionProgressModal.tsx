import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Loader2,
  RefreshCw,
  ShieldCheck,
  Trash2,
  X,
} from "lucide-react";

export interface TimelineEvent {
  status: string;
  timestamp: string;
  detail: string;
}

export interface DeletionDetail {
  deletion_request_id: string;
  status: string;
  scope: string;
  exclusion_epoch: number;
  affected_records_count: number;
  tombstone_latency_ms: number;
  unlearning_time_ms?: number | null;
  retrained_model_version?: string | null;
  affected_shards: number[];
  earliest_affected_slice?: number | null;
  store_checks: Record<string, any>;
  timeline: TimelineEvent[];
  policy_version: string;
  error_message?: string | null;
  requested_at: string;
  tombstoned_at?: string | null;
  completed_at?: string | null;
  certificate_id?: string | null;
  policy_notice: string;
}

interface DeletionProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeDeletionId: string | null;
  onRequestDeletion: () => Promise<void>;
  isInitiating: boolean;
  onRefreshDataInventory?: () => void;
  onOpenCertificate?: (certificateId: string) => void;
}

export default function DeletionProgressModal({
  isOpen,
  onClose,
  activeDeletionId,
  onRequestDeletion,
  isInitiating,
  onRefreshDataInventory,
  onOpenCertificate,
}: DeletionProgressModalProps) {
  const [detail, setDetail] = useState<DeletionDetail | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  // Poll deletion details
  useEffect(() => {
    if (!isOpen || !activeDeletionId) {
      setDetail(null);
      return;
    }

    let intervalId: any;
    const fetchDetail = async () => {
      try {
        const res = await fetch(`/api/v1/deletion-requests/${activeDeletionId}`);
        if (res.ok) {
          const data: DeletionDetail = await res.json();
          setDetail(data);
          if (data.status === "COMPLETED" || data.status.startsWith("FAILED")) {
            setIsPolling(false);
            if (onRefreshDataInventory) onRefreshDataInventory();
            clearInterval(intervalId);
          }
        }
      } catch {
        // network retry
      }
    };

    fetchDetail();
    setIsPolling(true);
    intervalId = setInterval(fetchDetail, 1200);

    return () => clearInterval(intervalId);
  }, [isOpen, activeDeletionId, onRefreshDataInventory]);

  if (!isOpen) return null;

  const isCompleted = detail?.status === "COMPLETED";
  const isFailed = detail?.status?.startsWith("FAILED");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-neutral-900 border border-neutral-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[88vh]">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-neutral-800 flex items-center justify-between bg-neutral-950/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-rose-950/80 border border-rose-800 text-rose-400">
              <Trash2 className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-semibold text-white text-base">
                Data Deletion & SISA Selective Unlearning
              </h3>
              <p className="text-xs text-neutral-400">
                Pre-tombstone exclusion, source reconciliation & retrained shard verification
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-neutral-400 hover:text-white p-1 rounded-lg hover:bg-neutral-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-sm">
          {!activeDeletionId ? (
            /* Confirmation View before initiating deletion */
            <div className="space-y-4">
              <div className="p-4 rounded-xl border border-amber-900/50 bg-amber-950/30 text-amber-200/90 text-xs leading-relaxed space-y-2">
                <div className="flex items-center gap-2 font-semibold text-amber-300">
                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                  <span>Deletion & Machine Unlearning Disclosure (Doc 02 §7)</span>
                </div>
                <p>
                  “Your request will stop future use of the selected data immediately. If the data
                  was already used to train a model, the system will run the configured unlearning
                  process. This can take time. A certificate is issued only after the required checks
                  complete.”
                </p>
              </div>

              <div className="space-y-2 text-xs text-neutral-300">
                <p className="font-semibold text-white">What happens during this workflow:</p>
                <ul className="list-disc list-inside space-y-1.5 text-neutral-400">
                  <li>
                    <strong className="text-neutral-200">Instant Pre-Tombstoning:</strong> All your
                    records are placed under an immutable exclusion hold at a new monotonic epoch,
                    blocking active training jobs immediately.
                  </li>
                  <li>
                    <strong className="text-neutral-200">Source Store Redaction:</strong> Raw chat
                    messages in the SQLite database and cached representations are redacted.
                  </li>
                  <li>
                    <strong className="text-neutral-200">SISA Selective Retraining:</strong> Only
                    the specific model shards containing your data are retrained from slice
                    checkpoints; untouched shards remain unaltered.
                  </li>
                  <li>
                    <strong className="text-neutral-200">Verifiable Certificate:</strong> A
                    digitally signed cryptographic certificate (Ed25519) and transparency log entry
                    will be generated.
                  </li>
                </ul>
              </div>

              <div className="pt-2 flex justify-end gap-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onClose}
                  className="border-neutral-700 text-neutral-300"
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  disabled={isInitiating}
                  onClick={onRequestDeletion}
                  className="bg-rose-600 hover:bg-rose-500 text-white font-semibold flex items-center gap-2"
                >
                  {isInitiating ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Initiating Deletion...</span>
                    </>
                  ) : (
                    <>
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>Confirm & Execute Deletion</span>
                    </>
                  )}
                </Button>
              </div>
            </div>
          ) : (
            /* Active Progress & Detailed Lifecycle View */
            <div className="space-y-5">
              {/* Status Header Badge */}
              <div className="flex items-center justify-between p-3.5 rounded-xl border border-neutral-800 bg-neutral-950/70">
                <div className="flex items-center gap-3">
                  {isCompleted ? (
                    <div className="p-2 rounded-lg bg-emerald-950 border border-emerald-800 text-emerald-400">
                      <CheckCircle2 className="w-5 h-5" />
                    </div>
                  ) : isFailed ? (
                    <div className="p-2 rounded-lg bg-rose-950 border border-rose-800 text-rose-400">
                      <AlertTriangle className="w-5 h-5" />
                    </div>
                  ) : (
                    <div className="p-2 rounded-lg bg-blue-950 border border-blue-800 text-blue-400">
                      <Loader2 className="w-5 h-5 animate-spin" />
                    </div>
                  )}

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-white">Status:</span>
                      <span
                        className={cn("px-2 py-0.5 rounded text-xs font-mono font-bold uppercase", {
                          "bg-emerald-950 text-emerald-400 border border-emerald-800": isCompleted,
                          "bg-rose-950 text-rose-400 border border-rose-800": isFailed,
                          "bg-blue-950 text-blue-300 border border-blue-800": !isCompleted && !isFailed,
                        })}
                      >
                        {detail?.status || "INITIALIZING"}
                      </span>
                    </div>
                    <p className="text-xs text-neutral-400 mt-0.5 font-mono">
                      Request ID: {activeDeletionId} • Epoch: {detail?.exclusion_epoch ?? 1}
                    </p>
                  </div>
                </div>

                {isPolling && (
                  <div className="flex items-center gap-1.5 text-xs text-neutral-400 font-mono">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-400" />
                    <span>Live Tracking</span>
                  </div>
                )}
              </div>

              {/* Policy copy banner per Doc 02 §7 */}
              {detail?.policy_notice && (
                <div className="p-3 rounded-lg border border-neutral-800 bg-neutral-950/50 text-xs text-neutral-300 leading-relaxed font-sans">
                  <strong>Notice:</strong> {detail.policy_notice}
                </div>
              )}

              {/* Key Metrics Grid */}
              {detail && (
                <div className="grid grid-cols-4 gap-2 text-center text-xs">
                  <div className="p-2.5 rounded-lg bg-neutral-950/60 border border-neutral-800">
                    <span className="block text-base font-bold text-white">
                      {detail.tombstone_latency_ms} ms
                    </span>
                    <span className="text-[10px] text-neutral-400 uppercase">Tombstone Latency</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-neutral-950/60 border border-neutral-800">
                    <span className="block text-base font-bold text-emerald-400">
                      {detail.affected_records_count}
                    </span>
                    <span className="text-[10px] text-neutral-400 uppercase">Records Locked</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-neutral-950/60 border border-neutral-800">
                    <span className="block text-base font-bold text-blue-400">
                      {detail.unlearning_time_ms ? `${(detail.unlearning_time_ms / 1000).toFixed(2)}s` : "0.0s"}
                    </span>
                    <span className="text-[10px] text-neutral-400 uppercase">Unlearn Time</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-neutral-950/60 border border-neutral-800">
                    <span className="block text-base font-bold text-purple-400">
                      {detail.affected_shards?.length > 0 ? `Shard ${detail.affected_shards.join(", ")}` : "None"}
                    </span>
                    <span className="text-[10px] text-neutral-400 uppercase">Affected Shards</span>
                  </div>
                </div>
              )}

              {/* Store Checks Verification Status */}
              {detail?.store_checks && Object.keys(detail.store_checks).length > 0 && (
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-neutral-300" />
                    <span>Store Verification Checks</span>
                  </span>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="flex items-center justify-between p-2 rounded-lg bg-neutral-950/50 border border-neutral-800/80">
                      <span className="text-neutral-300">SQLite Message Redaction</span>
                      {detail.store_checks.source_data_purged || detail.store_checks.sqlite_messages_redacted ? (
                        <span className="text-emerald-400 font-bold">Passed</span>
                      ) : (
                        <span className="text-neutral-500">Pending</span>
                      )}
                    </div>
                    <div className="flex items-center justify-between p-2 rounded-lg bg-neutral-950/50 border border-neutral-800/80">
                      <span className="text-neutral-300">Tombstones Active</span>
                      {detail.store_checks.tombstones_active ? (
                        <span className="text-emerald-400 font-bold">Passed</span>
                      ) : (
                        <span className="text-neutral-500">Pending</span>
                      )}
                    </div>
                    <div className="flex items-center justify-between p-2 rounded-lg bg-neutral-950/50 border border-neutral-800/80">
                      <span className="text-neutral-300">Model Deployment Swap</span>
                      {detail.store_checks.deployment_verified ? (
                        <span className="text-emerald-400 font-bold">Verified</span>
                      ) : (
                        <span className="text-neutral-500">Pending</span>
                      )}
                    </div>
                    <div className="flex items-center justify-between p-2 rounded-lg bg-neutral-950/50 border border-neutral-800/80">
                      <span className="text-neutral-300">Backup Policy Enforced</span>
                      {detail.store_checks.backup_policy_recorded || detail.store_checks.all_policy_checks_passed ? (
                        <span className="text-emerald-400 font-bold">30-Day Purge</span>
                      ) : (
                        <span className="text-neutral-500">Pending</span>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Lifecycle Timeline */}
              <div className="space-y-2">
                <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-neutral-300" />
                  <span>Lifecycle Event Log</span>
                </span>
                <div className="max-h-48 overflow-y-auto space-y-2 text-xs">
                  {detail?.timeline?.map((ev, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-lg bg-neutral-950/60 border border-neutral-800/70 space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-neutral-800 text-neutral-200">
                          {ev.status}
                        </span>
                        <span className="text-neutral-500 text-[10px] font-mono">
                          {new Date(ev.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-neutral-300 text-xs">{ev.detail}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-neutral-800 flex justify-between items-center bg-neutral-950/40 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-neutral-500">Policy Version 1.0 • Hardware Guardrails Active</span>
            {isCompleted && detail?.certificate_id && (
              <Button
                size="sm"
                onClick={() => {
                  if (onOpenCertificate) {
                    onOpenCertificate(detail.certificate_id!);
                  } else {
                    window.location.assign(`/verify/${detail.certificate_id}`);
                  }
                }}
                className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center gap-1.5 ml-2"
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>View Cryptographic Certificate</span>
              </Button>
            )}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={onClose}
            className="border-neutral-700 text-neutral-300 hover:bg-neutral-800"
          >
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}
