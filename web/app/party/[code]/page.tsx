"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

export default function PartyDashboardPage() {
  const params = useParams();
  const code = (params?.code as string) || "";

  const [party, setParty] = useState<any>(null);
  const [err, setErr] = useState("");

  async function load() {
    if (!code) return; // IMPORTANT: don't fetch /party/undefined
    setErr("");
    try {
      const data = await apiGet(`/party/${code}`);
      setParty(data);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 2000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code]);

  if (!code) {
    return (
      <main className="p-8 max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold">Party Dashboard</h1>
        <p className="text-red-500 mt-4">
          Missing party code in URL (code is undefined).
        </p>
      </main>
    );
  }

  return (
    <main className="p-8 max-w-2xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold">Party Dashboard — {code}</h1>

      <div className="space-x-3">
        <Link className="underline" href={`/party/${code}/join`}>Join link</Link>
        <Link className="underline" href={`/party/${code}/upload`}>Upload link</Link>
      </div>

      {err && <pre className="text-red-500">{err}</pre>}

      {party ? (
        <>
          <h2 className="font-semibold">Players</h2>
          <ul className="list-disc pl-6">
            {party.players.map((p: any) => (
              <li key={p.id}>
                {p.name} — {p.submitted ? "✅ submitted" : "⏳ waiting"}
              </li>
            ))}
          </ul>
        </>
      ) : (
        <p>Loading...</p>
      )}
    </main>
  );
}
