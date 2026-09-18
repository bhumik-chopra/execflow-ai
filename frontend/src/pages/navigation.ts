export const pages = [
  { id: 'daily-brief', title: 'Daily Brief', description: 'A clear view of your commitments and what needs attention.' },
  { id: 'my-actions', title: 'My Actions', description: 'Commitments owned by Arjun, supported by source evidence.' },
  { id: 'waiting-on-others', title: 'Waiting on Others', description: 'Deliverables you are waiting to receive from others.' },
  { id: 'unclear-ownership', title: 'Unclear Ownership', description: 'Open items whose owner cannot be established from evidence.' },
  { id: 'add-source', title: 'Add Source', description: 'Turn emails, meeting notes and voice notes into evidence-backed actions.' },
  { id: 'sources', title: 'Sources', description: 'Meeting transcripts, email threads, calendars, and personal voice notes.' },
  { id: 'ask-execflow', title: 'Ask ExecFlow', description: 'Answers grounded in your supplied evidence.' },
  { id: 'audit-trail', title: 'Audit Trail', description: 'Trace how evidence changes a commitment over time.' },
] as const

export type PageId = typeof pages[number]['id']

export function readPage(): PageId {
  const id = window.location.hash.slice(1)
  return pages.find((page) => page.id === id)?.id ?? 'daily-brief'
}
