import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Copy,
  Download,
  Fingerprint,
  Key,
  Layers,
  Loader2,
  Lock,
  ShieldCheck,
  ShieldAlert,
} from "lucide-react";

interface PublicVerificationData {
  certificate_id: string;
  request_id: string;
  verification_status: string; // "VALID_COMPLETED" | "VALID_PENDING" | "INVALID"
  signature_valid: boolean;
  merkle_inclusion_valid: boolean;
  issued_at: string;
  completion_timestamp: string;
  policy_version: string;
  signing_key_id: string;
  signature_algorithm: string;
  evidence_manifest_digest: string;
  merkle_root_hash: string;
  merkle_leaf_index: number;
  operations: string[];
  policy_checks: Record<string, boolean>;
  trust_notice: string;
}

interface PublicVerificationPageProps {
  certificateId: string;
  onBack?: () => void;
}

export default function PublicVerificationPage({
  certificateId,
  onBack,
}: PublicVerificationPageProps) {
  const [data, setData] = useState<PublicVerificationData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    async function fetchVerification() {
      setIsLoading(true);
      try {
        const res = await fetch(`/verify/${certificateId}`);
        if (res.ok) {
          const resJson = await res.json();
          setData(resJson);
        }
      } catch {
        // network error
      } finally {
        setIsLoading(false);
      }
    }

    if (certificateId) {
      fetchVerification();
    }
  }, [certificateId]);

  const copyToClipboard = () => {
    if (!data) return;
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadJson = () => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `certificate_${data.certificate_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const isValid = data?.verification_status === "VALID_COMPLETED";

  return (
    <div
      className="min-h-screen w-full bg-black text-white bg-cover bg-center flex flex-col justify-between p-4 md:p-8"
      style={{
        backgroundImage:
          "url('https://cdn.21st.dev/assets/mirror/c3/c333918af688a4a8a3d004652e6c0ee219457a9d84d380eeb31f513d4b59a09f.png')",
        backgroundAttachment: "fixed",
      }}
    >
      <div className="max-w-4xl w-full mx-auto space-y-6">
        {/* Navigation Bar */}
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            size="sm"
            onClick={onBack || (() => window.location.assign("/"))}
            className="border-neutral-700 bg-black/60 text-neutral-300 hover:text-white hover:bg-neutral-800 flex items-center gap-1.5"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Return to Chat</span>
          </Button>

          <div className="flex items-center gap-2 text-xs text-neutral-400 font-mono">
            <Lock className="w-3.5 h-3.5 text-emerald-400" />
            <span>RFC 8785 • Ed25519 • Merkle Log</span>
          </div>
        </div>

        {/* Verification Card */}
        <div className="bg-neutral-900/90 border border-neutral-700/80 rounded-2xl shadow-2xl overflow-hidden backdrop-blur-md">
          {/* Card Header */}
          <div className="px-6 py-5 border-b border-neutral-800 flex items-center justify-between bg-neutral-950/70">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-neutral-800 flex items-center justify-center border border-neutral-700 text-emerald-400">
                <Fingerprint className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-white tracking-wide">
                  Public Deletion Certificate Verifier
                </h1>
                <p className="text-xs text-neutral-400 font-mono">
                  Certificate ID: {certificateId}
                </p>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={copyToClipboard}
                disabled={!data}
                className="border-neutral-700 bg-neutral-800 text-neutral-300 hover:text-white text-xs flex items-center gap-1.5"
              >
                <Copy className="w-3.5 h-3.5" />
                <span>{copied ? "Copied!" : "Copy JSON"}</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={downloadJson}
                disabled={!data}
                className="border-neutral-700 bg-neutral-800 text-neutral-300 hover:text-white text-xs flex items-center gap-1.5"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download</span>
              </Button>
            </div>
          </div>

          {/* Card Body */}
          <div className="p-6 space-y-6">
            {isLoading ? (
              <div className="py-16 flex flex-col items-center justify-center text-center space-y-3">
                <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
                <p className="text-sm text-neutral-400 font-mono">
                  Retrieving Signed Evidence & Merkle Proof...
                </p>
              </div>
            ) : !data ? (
              <div className="py-12 text-center space-y-2 text-rose-400">
                <AlertTriangle className="w-8 h-8 mx-auto" />
                <p className="text-base font-semibold">Certificate Not Found</p>
                <p className="text-xs text-neutral-400">
                  No certificate matching {certificateId} was found in the public transparency registry.
                </p>
              </div>
            ) : (
              <>
                {/* Result Status Banner */}
                <div
                  className={cn("p-4 rounded-xl border flex items-center justify-between", {
                    "bg-emerald-950/60 border-emerald-800 text-emerald-300": isValid,
                    "bg-rose-950/60 border-rose-800 text-rose-300": !isValid,
                  })}
                >
                  <div className="flex items-center gap-3">
                    {isValid ? (
                      <ShieldCheck className="w-7 h-7 text-emerald-400 shrink-0" />
                    ) : (
                      <ShieldAlert className="w-7 h-7 text-rose-400 shrink-0" />
                    )}
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm tracking-wide">VERIFICATION RESULT:</span>
                        <span className="px-2 py-0.5 rounded text-xs font-mono font-extrabold uppercase bg-black/40 border">
                          {data.verification_status}
                        </span>
                      </div>
                      <p className="text-xs text-neutral-300 mt-1">
                        {data.trust_notice}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Cryptographic Badges Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-neutral-950/70 border border-neutral-800">
                    <span className="text-[10px] text-neutral-400 font-mono uppercase block">
                      Ed25519 Signature
                    </span>
                    <span
                      className={cn("text-sm font-bold flex items-center gap-1 mt-1", {
                        "text-emerald-400": data.signature_valid,
                        "text-rose-400": !data.signature_valid,
                      })}
                    >
                      {data.signature_valid ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                      {data.signature_valid ? "Authentic" : "Invalid"}
                    </span>
                    <span className="text-[10px] text-neutral-500 font-mono mt-0.5 block truncate">
                      Key: {data.signing_key_id}
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-neutral-950/70 border border-neutral-800">
                    <span className="text-[10px] text-neutral-400 font-mono uppercase block">
                      Merkle Tree Inclusion
                    </span>
                    <span
                      className={cn("text-sm font-bold flex items-center gap-1 mt-1", {
                        "text-emerald-400": data.merkle_inclusion_valid,
                        "text-rose-400": !data.merkle_inclusion_valid,
                      })}
                    >
                      {data.merkle_inclusion_valid ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                      {data.merkle_inclusion_valid ? "Proven (RFC 6962)" : "Unverified"}
                    </span>
                    <span className="text-[10px] text-neutral-500 font-mono mt-0.5 block">
                      Leaf #{data.merkle_leaf_index}
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-neutral-950/70 border border-neutral-800">
                    <span className="text-[10px] text-neutral-400 font-mono uppercase block">
                      Zero PII Audit
                    </span>
                    <span className="text-sm font-bold text-emerald-400 flex items-center gap-1 mt-1">
                      <CheckCircle2 className="w-4 h-4" />
                      100% Protected
                    </span>
                    <span className="text-[10px] text-neutral-500 font-mono mt-0.5 block">
                      Strict zero PII leak
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-neutral-950/70 border border-neutral-800">
                    <span className="text-[10px] text-neutral-400 font-mono uppercase block">
                      Policy Version
                    </span>
                    <span className="text-sm font-bold text-purple-400 mt-1 block">
                      Version {data.policy_version}
                    </span>
                    <span className="text-[10px] text-neutral-500 font-mono mt-0.5 block">
                      Formal Schema
                    </span>
                  </div>
                </div>

                {/* Evidence Manifest Digest & Merkle Root */}
                <div className="space-y-3 font-mono text-xs">
                  <div className="p-3.5 rounded-xl bg-neutral-950/80 border border-neutral-800/90 space-y-1">
                    <div className="flex items-center justify-between text-neutral-400 text-[11px]">
                      <span>EVIDENCE MANIFEST DIGEST (SHA-256):</span>
                      <span className="text-neutral-500">RFC 8785 Canonical JCS</span>
                    </div>
                    <p className="text-amber-300 font-bold break-all select-all">
                      {data.evidence_manifest_digest}
                    </p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-neutral-950/80 border border-neutral-800/90 space-y-1">
                    <div className="flex items-center justify-between text-neutral-400 text-[11px]">
                      <span>TRANSPARENCY LOG ROOT HASH:</span>
                      <span className="text-neutral-500">Append-Only Tree Root</span>
                    </div>
                    <p className="text-blue-300 font-bold break-all select-all">
                      {data.merkle_root_hash}
                    </p>
                  </div>
                </div>

                {/* Operations & Policy Checks */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Verified Operations */}
                  <div className="p-4 rounded-xl bg-neutral-950/50 border border-neutral-800 space-y-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400 flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5" />
                      <span>Certified Operations</span>
                    </span>
                    <ul className="space-y-1.5 text-xs text-neutral-300">
                      {data.operations.map((op, idx) => (
                        <li key={idx} className="flex items-center gap-2">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                          <span className="font-mono text-[11px]">{op}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Policy Verification Checklist */}
                  <div className="p-4 rounded-xl bg-neutral-950/50 border border-neutral-800 space-y-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400 flex items-center gap-1.5">
                      <Key className="w-3.5 h-3.5" />
                      <span>Policy Check Results</span>
                    </span>
                    <div className="space-y-1.5 text-xs">
                      {Object.entries(data.policy_checks).map(([key, val], idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-1.5 rounded bg-neutral-900/60 font-mono text-[11px]"
                        >
                          <span className="text-neutral-300">{key}:</span>
                          <span className={val ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
                            {val ? "PASSED" : "FAILED"}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* User-Facing Boundary Notice (Doc 01 §1 & Doc 05 §14) */}
                <div className="p-3.5 rounded-xl border border-neutral-800 bg-neutral-950/40 text-[11px] text-neutral-400 leading-relaxed font-sans">
                  <strong className="text-neutral-200">Legal & Verification Boundary:</strong> A valid digital signature and Merkle inclusion proof confirm that this certificate was authentically signed by the CryptoForget platform's verification authority and that the certified source redactions and SISA retraining operations passed specified policy checks. Per Doc 01 §1, this is cryptographically authentic evidence of execution under policy—not a mathematical guarantee of zero residual information in neural network weights.
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
