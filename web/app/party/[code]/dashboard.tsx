"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPostJson } from "@/lib/api";

export default function Dashboard({
  code,
  isHost,
}: {
  code: string;
  isHost: boolean;
}) {
  const [party, setParty] = useState<any>(null);
  const [results, setResults] = useState<any>(null);
  const [err, setErr] = useState("");

  async function load() {
    setErr("");
    try {
      const data = await apiGet(`/party/${code}`);
      setParty(data);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    }
  }

  async function endGame() {
    setErr("");
    try {
      const hostToken = localStorage.getItem("host_token");
      if (!hostToken) return setErr("Missing host_token (host only).");

      const res = await apiPostJson(`/party/${code}/end`, {
        buy_in_cents: 2000,
        host_token: hostToken,
      });

      setResults(res);
      await load();
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 2000);
    return () => clearInterval(t);
  }, []);

  return (
    <main className="p-8 max-w-2xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold">
        {isHost ? "Host Dashboard" : "Party Dashboard"} — {code}
      </h1>

      <div className="space-x-2">
        <a className="underline" href={`/party/${code}/join`}>
          Join link
        </a>
        <a className="underline" href={`/party/${code}/upload`}>
          Upload link
        </a>
      </div>

      {err && <p className="text-red-600">{err}</p>}

      {party ? (
        <>
          <h2 className="font-semibold">Players</h2>
          <ul className="list-disc pl-6">
            {party.players.map((p: any) => (
              <li key={p.id}>
                {p.name} {p.venmo ? `(@${p.venmo})` : ""} —{" "}
                {p.submitted ? "✅ submitted" : "⏳ waiting"}
              </li>
            ))}
          </ul>

          {isHost && (
            <button className="bg-red-600 text-white p-2" onClick={endGame}>
              End Game (buy-in $20)
            </button>
          )}

          {results && (
            <pre className="bg-gray-100 p-4 overflow-auto">
              {JSON.stringify(results, null, 2)}
            </pre>
          )}
        </>
      ) : (
        <p>Loading...</p>
      )}
    </main>
  );
}
