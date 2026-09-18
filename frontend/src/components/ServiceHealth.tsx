import { useEffect, useState } from 'react'
import { getHealth, type Health } from '../services/api'
export default function ServiceHealth() {
  const [health, setHealth] = useState<Health | null>(null)
  const [failed, setFailed] = useState(false)
  useEffect(() => { getHealth().then(setHealth).catch(() => setFailed(true)) }, [])
  return <div className="system-status" title={health ? `Backend: ${health.backend} · MongoDB: ${health.mongodb} · Groq: ${health.groq} (configuration only)` : 'Checking services'}><span className={failed || health?.mongodb === 'unavailable' ? 'dot warning' : 'dot'} />{failed ? 'Backend unavailable' : !health ? 'Connecting…' : health.mongodb !== 'ok' ? 'Database unavailable' : 'System connected'}<span className="muted"> · Groq {health?.groq === 'configured' ? 'configured' : 'unavailable'}</span></div>
}
