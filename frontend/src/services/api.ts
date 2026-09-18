export interface Health { backend: string; mongodb: string; groq: string; groq_model: string }
export interface ReferenceContext { user: string; role: string; as_of: string }
export interface Evidence { source_id: string; timestamp: string; author: string; type: string; evidence_text: string }
export interface Task { task_id: string; canonical_title: string; owner: string | null; classification: string; status: string; counterparties: string[]; current_deadline: string | null; source_ids: string[]; evidence: Evidence[]; deadline_history: { deadline_text: string; normalized_deadline: string; accepted: boolean; assumption?: string }[]; decision_explanation: string }
export interface Source { source_id: string; source_type: string; timestamp: string; author: string; subject: string; content: string; processing_status: string }
export interface Conflict { event_a: { title: string }; event_b: { title: string }; overlap_start: string; overlap_end: string; overlap_minutes: number }
export interface Brief { metrics: Record<string, number>; sections: Record<string, Task[]> & { schedule_conflicts: Conflict[] } }
export async function api<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`/api${path}`, { method: body === undefined ? 'GET' : 'POST', headers: body === undefined ? undefined : { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body), signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(60000)]) : AbortSignal.timeout(60000) })
  const data = await response.json()
  if (response.status === 401 && !path.startsWith('/auth/')) window.dispatchEvent(new Event('execflow:session-expired'))
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Unable to complete the request. Check the input and try again.')
  return data as T
}
export const getHealth = (signal?: AbortSignal) => api<Health>('/health', undefined, signal)
export const getContext = (asOf: string, signal?: AbortSignal) => api<ReferenceContext>(`/context?as_of=${encodeURIComponent(asOf)}`, undefined, signal)
