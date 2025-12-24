"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { apiPostJson } from "@/lib/api";

export default function JoinPage() {
  const { code } = useParams<{ code: string }>();
  const router = useRouter();
  const [name, setName] = useState("");
  const [venmo, setVenmo] = useState("");
  const [err, setErr] = useState("");

  async function join() {
    setErr("");
    try {
      const res = await apiPostJson<{ player_id: number }>(`/party/${code}/join`, {
        name,
        venmo: venmo || undefined,
      });
      localStorage.setItem(`player_id:${code}`, String(res.player_id));
      router.push(`/party/${code}/upload`);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    }
  }

  return (
    <main className="p-8 max-w-md mx-auto space-y-3">
      <h1 className="text-2xl font-bold">Join Party {code}</h1>
      <input className="border p-2 w-full" placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} />
      <input className="border p-2 w-full" placeholder="Venmo (optional)" value={venmo} onChange={(e) => setVenmo(e.target.value)} />
      <button className="bg-black text-white p-2 w-full" onClick={join}>Join</button>
      {err && <p className="text-red-600">{err}</p>}
    </main>
  );
}
