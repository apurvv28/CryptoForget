import { useEffect, useState } from "react";
import ChatInterface from "./components/chat/ChatInterface";
import PublicVerificationPage from "./components/verification/PublicVerificationPage";

export default function App() {
  const [route, setRoute] = useState<string>(() => window.location.pathname);

  useEffect(() => {
    const handlePopState = () => {
      setRoute(window.location.pathname);
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  if (route.startsWith("/verify/")) {
    const certId = route.replace("/verify/", "").trim();
    return (
      <PublicVerificationPage
        certificateId={certId}
        onBack={() => {
          window.history.pushState({}, "", "/");
          setRoute("/");
        }}
      />
    );
  }

  return (
    <main className="w-full min-h-screen bg-black">
      <ChatInterface
        onOpenCertificate={(certId: string) => {
          window.history.pushState({}, "", `/verify/${certId}`);
          setRoute(`/verify/${certId}`);
        }}
      />
    </main>
  );
}
