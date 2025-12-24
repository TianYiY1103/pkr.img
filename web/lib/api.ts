const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// export async function apiHealth(): Promise<string> {
//   const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
//   if (!res.ok) throw new Error(await res.text());
//   return res.text();
// }

export async function apiHealth(): Promise<string> {
  const url = `${API_URL}/health`;
  console.log("API health url =", url);
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.text();
}


export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiPostJson<T>(path: string, body: any): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiPostForm<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
