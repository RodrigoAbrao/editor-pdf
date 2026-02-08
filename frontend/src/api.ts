/* ── API client ──────────────────────────────────────────────────────────── */

import type { DocumentInfo, EditOperation, PageText } from "./types";

// In production we prefer same-origin requests ("/api/..."), so Vercel rewrites
// can proxy to the backend without CORS headaches.
// In dev, allow overriding with VITE_API_URL (otherwise Vite proxy / same-origin).
const BASE = import.meta.env.DEV ? (import.meta.env.VITE_API_URL ?? "") : "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

/* ── Upload ─────────────────────────────────────────────────────────────── */
export async function uploadDocument(file: File): Promise<DocumentInfo> {
  const form = new FormData();
  form.append("file", file);
  return request<DocumentInfo>("/api/documents", { method: "POST", body: form });
}

/* ── PDF file URL (for PDF.js) ──────────────────────────────────────────── */
export function documentFileUrl(docId: string): string {
  return `${BASE}/api/documents/${docId}/file`;
}

/* ── Page text ──────────────────────────────────────────────────────────── */
export async function getPageText(docId: string, page: number): Promise<PageText> {
  return request<PageText>(`/api/documents/${docId}/pages/${page}/text`);
}

/* ── Fonts ───────────────────────────────────────────────────────────────── */
export async function listFonts(docId: string): Promise<string[]> {
  const data = await request<{ fonts: string[] }>(`/api/documents/${docId}/fonts`);
  return data.fonts;
}

export function fontFileUrl(docId: string, fontName: string): string {
  return `${BASE}/api/documents/${docId}/fonts/${encodeURIComponent(fontName)}`;
}

/* ── Export ──────────────────────────────────────────────────────────────── */
export async function exportDocument(
  docId: string,
  edits: EditOperation[],
): Promise<Blob> {
  const payload = {
    edits: edits.map(({ key, ...rest }) => rest),
  };
  const res = await fetch(`${BASE}/api/documents/${docId}/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Export failed (${res.status}): ${body}`);
  }
  return res.blob();
}
