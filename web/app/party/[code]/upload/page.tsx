"use client";

import { useParams } from "next/navigation";
import { useState } from "react";
import { apiPostForm } from "@/lib/api";

export default function UploadPage() {
  const { code } = useParams<{ code: string }>();
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState("");
  const [err, setErr] = useState("");

  async function upload() {
    setErr("");
    setStatus("");

    const playerId = localStorage.getItem(`player_id:${code}`);
    if (!playerId) return setErr("No player_id found. Please join first.");
    if (!file) return setErr("Choose an image first.");

    const form = new FormData();
    form.append("player_id", playerId);
    form.append("image", file);

    try {
      const res = await apiPostForm<any>(`/party/${code}/upload`, form);
      setStatus(`Uploaded! submission_id=${res.submission_id}`);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    }
  }

  return (
    <main className="p-8 max-w-md mx-auto space-y-3">
      <h1 className="text-2xl font-bold">Upload your chips</h1>
      <input type="file" accept="image/*" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      <button className="bg-black text-white p-2 w-full" onClick={upload}>Upload</button>
      {status && <p className="text-green-700">{status}</p>}
      {err && <p className="text-red-600">{err}</p>}
    </main>
  );
}
