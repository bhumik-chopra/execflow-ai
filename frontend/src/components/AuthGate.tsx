import { useEffect, useState, type FormEvent } from 'react'
import { ArrowRight, Eye, EyeOff, Mail, LockKeyhole, Check, ArrowUpRight, Sparkles } from 'lucide-react'
import App from '../App'
import { api } from '../services/api'
import './login.css'

export default function AuthGate() {
  const [status, setStatus] = useState<'checking' | 'signed-out' | 'signed-in'>('checking')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [visible, setVisible] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => {
    let mounted = true
    api('/auth/me').then(() => { if (mounted) setStatus('signed-in') }).catch(() => { if (mounted) setStatus('signed-out') })
    const expired = () => { setPassword(''); setStatus('signed-out'); setError('Your session has ended. Please sign in again.') }
    window.addEventListener('execflow:session-expired', expired)
    return () => { mounted = false; window.removeEventListener('execflow:session-expired', expired) }
  }, [])
  async function signIn(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError('')
    try { await api('/auth/login', { email: email.trim(), password }); setPassword(''); setStatus('signed-in') }
    catch (e) { setError((e as Error).message) }
    finally { setBusy(false) }
  }
  async function signOut() {
    try { await api('/auth/logout', {}); setEmail(''); setPassword(''); setError(''); setStatus('signed-out'); window.location.hash = 'daily-brief' }
    catch { setError('Could not sign out. Please try again.') }
  }
  if (status === 'checking') return <div className="auth-loading"><span className="brand-mark">E</span><p>Opening your workspace…</p></div>
  if (status === 'signed-in') return <>{error && <div className="auth-toast" role="alert">{error}</div>}<App onLogout={signOut}/></>
  return <div className="login-shell">
    <section className="login-story" aria-label="About ExecFlow">
      <a className="login-brand" href="#daily-brief" aria-label="ExecFlow home"><span className="brand-mark">E</span><span>ExecFlow <small>AI</small></span></a>
      <div className="login-story-body"><div className="login-kicker"><span/> CLARITY FOR WHAT COMES NEXT</div>
        <h1>Less to remember.<br/><em>More to move forward.</em></h1>
        <p className="login-story-copy">Bring your conversations, commitments, and next steps into one focused workspace.</p>
        <div className="login-visual" aria-hidden="true"><div className="login-orbit orbit-one"/><div className="login-orbit orbit-two"/>
          <div className="login-note"><div className="login-note-top"><span className="note-icon"><Sparkles size={17}/></span><span>FROM CONVERSATION TO ACTION</span><ArrowUpRight size={16}/></div><h2>Every commitment.<br/>A clear next step.</h2><div className="login-note-line"><span className="note-check"><Check size={12}/></span><span>Know what needs your attention</span></div><div className="login-note-line"><span className="note-check"><Check size={12}/></span><span>See the evidence behind every action</span></div><div className="login-note-footer"><span className="note-dot"/> Built for a more focused day</div></div>
          <div className="login-float"><span><Check size={16}/></span>Nothing lost in the follow-up.</div>
        </div>
      </div>
      <div className="login-story-footer"><span>YOUR EXECUTIVE ACTION COPILOT</span><span>01 / FOCUS</span></div>
    </section>
    <section className="login-entry"><div className="login-entry-top"><LockKeyhole size={13}/><span>Your private workspace</span></div>
      <div className="login-form-wrap"><div className="login-welcome-icon"><ArrowUpRight size={25}/></div><p className="login-overline">WELCOME BACK</p><h2>Pick up where<br/>you left off.</h2><p className="login-subtitle">Sign in to your ExecFlow workspace.</p>
        <form onSubmit={signIn} className="login-form">
          <label htmlFor="login-email">Email address</label><div className="login-input"><Mail size={17}/><input id="login-email" type="email" autoComplete="username" placeholder="Enter your work email" required value={email} onChange={e=>setEmail(e.target.value)} autoFocus disabled={busy}/></div>
          <label htmlFor="login-password">Password</label><div className="login-input"><LockKeyhole size={17}/><input id="login-password" type={visible ? 'text' : 'password'} autoComplete="current-password" placeholder="Enter your password" required value={password} onChange={e=>setPassword(e.target.value)} disabled={busy}/><button type="button" className="password-toggle" aria-label={visible ? 'Hide password' : 'Show password'} aria-pressed={visible} onClick={()=>setVisible(!visible)}>{visible ? <EyeOff size={17}/> : <Eye size={17}/>}</button></div>
          {error && <p className="login-error" role="alert">{error}</p>}
          <button className="login-submit" type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign in to workspace'}<ArrowRight size={18}/></button>
        </form>
        <div className="login-assurance"><span/><p>A little clarity goes a long way.</p><span/></div>
      </div>
      <footer className="login-entry-footer"><span>ExecFlow AI</span><span>Focus on what matters.</span></footer>
    </section>
  </div>
}
