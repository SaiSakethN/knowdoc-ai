export type User = { id: string; email: string };
export type Collection = { id: string; name: string };
export type Version = { id: string; label: string; status: string; checksum: string; file_type: string; size: number; provenance: Record<string, unknown>; warnings: string[] };
export type Document = { id: string; title: string; collection_id: string; owned: boolean; versions: Version[] };
export type Passage = { id: string; title: string; document_id: string; version_id: string; version: string; text: string; score: number; location: Record<string, string | number>; source_url?: string; retrieved_at?: string };
export type Answer = { answer_method?: 'extractive' | 'local_model' | 'hosted_model' | 'evidence'; status: string; answer: string; claims: { text: string; citation_ids: string[]; quote: string }[]; citations: Passage[]; mode: string; conflicts?: { citation_ids: string[]; quotes: string[]; versions: string[]; reason: string }[]; limitations: string[]; timings: { retrieval_ms: number; total_ms: number }; usage?: { input_tokens: number; output_tokens: number; model: string } };
export type Job = { id: string; title: string; version: string; status: string; attempts: number; error: string | null; timings: { total_ms?: number; chunks?: number } };
export type EvalRun = { id: string; created_at: string; report: { dataset: string; annotation_status: string; results: { method: string; recall_at_5: number | null; mrr: number | null; ndcg_at_5: number | null; p95_ms: number | null; cases: number; errors?: number }[]; behavior?: { category: string; status_match: boolean; no_forbidden_output?: boolean }[]; failures?: { case_id: string; method: string; reason: string }[]; release_gate?: string; limitations: string[] } };

let csrf = '';
export function setCsrf(value: string) { csrf = value; }
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const form = options.body instanceof FormData;
  const response = await fetch(`/api/v1${path}`, { ...options, credentials: 'include', headers: {
    ...(!form && options.body ? { 'Content-Type': 'application/json' } : {}),
    ...(csrf ? { 'X-CSRF-Token': csrf } : {}), ...options.headers,
  }});
  if (!response.ok) {
    const body = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
    throw new Error(String(body.error || 'Request failed').replaceAll('_', ' '));
  }
  return response.status === 204 ? undefined as T : response.json();
}
