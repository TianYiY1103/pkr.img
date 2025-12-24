"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiPostJson, apiHealth } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [hostName, setHostName] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [error, setError] = useState("");

  async function createParty() {
    setError("");
    try {
      const res = await apiPostJson<{ code: string }>("/party", {
        host_name: hostName,
      });
      router.push(`/party/${res.code}/host`);
    } catch (e: any) {
      setError(String(e?.message ?? e));
    }
  }

  return (
    <main className="p-8 max-w-xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">pkr.img</h1>

      {/* 🔎 API Connectivity Test */}
      <button
        className="border p-2 rounded"
        onClick={async () => {
          try {
            const txt = await apiHealth();
            alert(txt);
          } catch (e: any) {
            alert("API error: " + String(e?.message ?? e));
          }
        }}
      >
        Ping API
      </button>

      <div className="space-y-3">
        <h2 className="text-xl font-semibold">Host a game</h2>
        <input
          className="border p-2 w-full"
          placeholder="Your name"
          value={hostName}
          onChange={(e) => setHostName(e.target.value)}
        />
        <button
          className="bg-black text-white p-2 w-full"
          onClick={createParty}
        >
          Create Party
        </button>
      </div>

      <div className="space-y-3">
        <h2 className="text-xl font-semibold">Join a game</h2>
        <input
          className="border p-2 w-full"
          placeholder="Party code"
          value={joinCode}
          onChange={(e) => setJoinCode(e.target.value)}
        />
        <button
          className="bg-blue-600 text-white p-2 w-full"
          onClick={() => router.push(`/party/${joinCode}/join`)}
        >
          Join Party
        </button>
      </div>

      {error && <p className="text-red-600">{error}</p>}
    </main>
  );
}
