import { StrictMode, useCallback, useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { createRoot } from 'react-dom/client';
import { Activity, ArrowUp, BookOpen, Check, CheckCheck, ChevronDown, ChevronRight, CircleHelp, Database, FileText, FolderClosed, GitCompareArrows, Layers, Library, LoaderCircle, LogOut, MessageSquare, Plus, Search, Settings2, ShieldCheck, Sparkles, Upload, X } from 'lucide-react';
import { api, setCsrf } from './api';
import type { Answer, Collection, Document, EvalRun, Job, Passage, User } from './api';
import { DocumentManager } from './DocumentManager';
import { EvaluationCard } from './EvaluationCard';
import './style.css';
import './professional.css';

type Page = 'workspace' | 'library' | 'evaluations' | 'system';
type Message = { question: string; answer: Answer };

function Brand() { return <div className="brand"><div className="brand-symbol"><BookOpen size={22} strokeWidth={1.8}/></div><div>KnowDoc<span className="brand-ai">AI</span></div></div>; }

function Auth({ onLogin }: { onLogin: (user: User) => void }) {
  const [register, setRegister] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setBusy(true); setError('');
    const data = new FormData(e.currentTarget);
    try {
      const result = await api<{ user: User; csrf_token: string }>(`/sessions/${register ? 'register' : 'login'}`, { method: 'POST', body: JSON.stringify(Object.fromEntries(data)) });
      setCsrf(result.csrf_token); onLogin(result.user);
    } catch (err) { setError((err as Error).message); } finally { setBusy(false); }
  }
  return <main className="auth-layout"><section className="auth-story"><Brand/><div><span className="eyebrow light">YOUR KNOWLEDGE. A CLEARER PICTURE.</span><h1>Good answers<br/>start with<br/><em>good evidence.</em></h1><p>Turn your documents into clear, cited answers.<br/>Find the answer. Follow the source. Know the version.</p><div className="auth-proof"><ShieldCheck size={20}/> Local inference · Private collections · Traceable passages</div></div><small>KnowDoc AI / Evidence-first knowledge intelligence</small></section><section className="auth-form"><div><span className="eyebrow">WELCOME TO YOUR WORKSPACE</span><h2>{register ? 'Create your account' : 'Welcome back.'}</h2><p>{register ? 'Your documents stay private by default.' : 'Sign in to explore your knowledge library.'}</p><form onSubmit={submit}><label>Email address<input name="email" type="email" placeholder="you@company.com" required autoComplete="email"/></label><label>Password<input name="password" type="password" placeholder="At least 10 characters" minLength={10} maxLength={128} required autoComplete={register ? 'new-password' : 'current-password'}/></label>{error && <p role="alert" className="error">{error}</p>}<button className="primary" disabled={busy}>{busy ? <LoaderCircle className="spin" size={18}/> : null}{register ? 'Create private workspace' : 'Sign in'}</button></form><p className="auth-switch">{register ? 'Already have an account?' : 'New to KnowDoc AI?'} <button className="text-button" onClick={() => { setRegister(!register); setError(''); }}>{register ? 'Sign in' : 'Create an account'}</button></p><div className="privacy-note"><ShieldCheck size={18}/><span>Documents are processed locally. No hosted AI provider is enabled by default.</span></div></div></section></main>;
}

function SourcePanel({ source, close }: { source: Passage; close: () => void }) {
  const [passage, setPassage] = useState<Passage | null>(null);
  const [error, setError] = useState('');
  useEffect(() => { let active = true; setPassage(null); setError(''); api<Passage>(`/citations/${source.id}`).then(p => { if (active) setPassage(p); }).catch(e => { if (active) setError(e.message); }); return () => { active = false; }; }, [source.id]);
  return <aside className="source-panel" aria-label="Source evidence"><div className="panel-title"><span><BookOpen size={18}/> Source evidence</span><button className="icon-button" onClick={close} aria-label="Close source"><X size={18}/></button></div>{error ? <p className="error" role="alert">{error}</p> : !passage ? <p className="muted">Resolving stored passage…</p> : <><span className="badge mint"><ShieldCheck size={13}/> Citation resolved</span><h3>{passage.title}</h3><div className="source-details"><span>Source version</span><strong>{passage.version}</strong><span>Location</span><strong>{passage.location.page ? `Page ${passage.location.page}` : passage.location.section || 'Document'}</strong><span>Captured</span><strong>{passage.retrieved_at ? new Date(passage.retrieved_at).toLocaleDateString() : 'Not recorded'}</strong><span>Currentness</span><strong>Not independently verified</strong><span>Text offsets</span><strong>{passage.location.start}–{passage.location.end}</strong></div><div className="passage-text">{passage.text}</div><p className="fine">Offsets refer to the normalized section. This is the stored source passage; citation resolution does not guarantee semantic correctness.</p>{passage.source_url?.startsWith('https://') ? <a className="source-link" href={passage.source_url} target="_blank" rel="noreferrer">Open publisher page <ChevronRight size={15}/></a> : null}<a className="source-link" href={`/api/v1/versions/${passage.version_id}/original`}>Download original source</a><div className="source-id"><span>IMMUTABLE VERSION ID</span><code>{passage.version_id}</code></div></>}</aside>;
}

function Workspace({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [page, setPage] = useState<Page>('workspace');
  const [collections, setCollections] = useState<Collection[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [collectionId, setCollectionId] = useState('');
  const [versionId, setVersionId] = useState('');
  const [source, setSource] = useState<Passage | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState('');
  const [mode, setMode] = useState('generate');
  const [method, setMethod] = useState('hybrid');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [uploadOpen, setUploadOpen] = useState(false);
  const [newCollection, setNewCollection] = useState(false);
  const [collectionName, setCollectionName] = useState('');
  const [newVersionDoc, setNewVersionDoc] = useState('');
  const [versionLabel, setVersionLabel] = useState('');
  const [uploadBusy, setUploadBusy] = useState(false);
  const [uploadMessage, setUploadMessage] = useState('');
  const [runs, setRuns] = useState<EvalRun[]>([]);
  const [system, setSystem] = useState<Record<string, unknown> | null>(null);
  const [compareDoc, setCompareDoc] = useState<Document | null>(null);
  const [manageDoc, setManageDoc] = useState<Document | null>(null);
  const [evalTasks, setEvalTasks] = useState<{id: string; status: string; error: string | null}[]>([]);
  const [compared, setCompared] = useState<Passage[][]>([]);
  const fileInput = useRef<HTMLInputElement>(null);
  const end = useRef<HTMLDivElement>(null);

  const refresh = useCallback(async () => {
    const [c, d, j] = await Promise.all([api<{ items: Collection[] }>('/collections'), api<{ items: Document[] }>('/documents'), api<{ items: Job[] }>('/jobs')]);
    setCollections(c.items); setDocuments(d.items); setJobs(j.items);
  }, []);
  useEffect(() => { if (!user) return; refresh().catch(e => setError(e.message)); const id = setInterval(() => refresh().catch(() => {}), 4000); return () => clearInterval(id); }, [user, refresh]);
  useEffect(() => { if (!user) return; if (page === 'evaluations') api<{ items: EvalRun[]; tasks: typeof evalTasks }>('/evaluations').then(r => { setRuns(r.items); setEvalTasks(r.tasks || []); }).catch(e => setError(e.message)); if (page === 'system') api<Record<string, unknown>>('/system').then(setSystem).catch(e => setError(e.message)); }, [page, user]);
  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }); }, [messages.length, busy]);

  useEffect(() => { if (page !== 'evaluations' || !user) return; const id = setInterval(() => api<{items: EvalRun[]; tasks: typeof evalTasks}>('/evaluations').then(r => {setRuns(r.items); setEvalTasks(r.tasks || []);}).catch(() => {}), 4000); return () => clearInterval(id); }, [page, user]);
  useEffect(() => {
    if (!uploadOpen && !newCollection && !compareDoc && !manageDoc) return;
    const previous = document.activeElement as HTMLElement | null;
    const modal = document.querySelector<HTMLElement>('[role=dialog]');
    const focusable = () => Array.from(modal?.querySelectorAll<HTMLElement>('button:not([disabled]),input:not([hidden]),select,textarea,a[href]') || []).filter(el => el.offsetParent !== null);
    focusable()[0]?.focus();
    const listener = (e: KeyboardEvent) => { if(e.key === 'Escape') {setUploadOpen(false);setNewCollection(false);setCompareDoc(null);setManageDoc(null);} if(e.key === 'Tab') {const all=focusable(); const first=all[0],last=all.at(-1); if(e.shiftKey && document.activeElement===first) {e.preventDefault();last?.focus();} else if(!e.shiftKey && document.activeElement===last) {e.preventDefault();first?.focus();}} };
    document.addEventListener('keydown',listener); return () => {document.removeEventListener('keydown',listener);previous?.focus();};
  }, [uploadOpen,newCollection,compareDoc,manageDoc]);

  const visibleDocs = documents.filter(d => !collectionId || d.collection_id === collectionId);
  const versions = visibleDocs.flatMap(d => d.versions.map(v => ({ ...v, title: d.title })));
  const readyCount = versions.filter(v => v.status === 'ready').length;
  const processing = jobs.filter(j => ['queued', 'running'].includes(j.status)).length;

  async function ask(e?: FormEvent, override?: string) {
    e?.preventDefault(); const value = override || question;
    if (busy || value.trim().length < 3) return;
    setBusy(true); setError(''); setQuestion('');
    try {
      const answer = await api<Answer>('/answers', { method: 'POST', body: JSON.stringify({ question: value, mode, method, collection_id: collectionId || null, version_ids: versionId ? [versionId] : [] }) });
      setMessages(m => [...m, { question: value, answer }]);
    } catch (e) { setError((e as Error).message); setQuestion(value); } finally { setBusy(false); }
  }

  async function addCollection(e: FormEvent) {
    e.preventDefault(); setError('');
    try { const c = await api<Collection>('/collections', { method: 'POST', body: JSON.stringify({ name: collectionName }) }); await refresh(); setCollectionId(c.id); setCollectionName(''); setNewCollection(false); }
    catch (e) { setError((e as Error).message); }
  }

  async function upload(files: FileList | File[]) {
    if (!collectionId) { setUploadMessage('Choose a collection first.'); return; }
    if (files.length > 20) { setUploadMessage('Choose at most 20 files per batch.'); return; }
    setUploadBusy(true); setUploadMessage('');
    let success = 0;
    try {
      for (const file of Array.from(files)) {
        const body = new FormData(); body.set('collection_id', collectionId); body.set('label', versionLabel || 'unversioned'); body.set('file', file);
        if (newVersionDoc) body.set('document_id', newVersionDoc);
        await api('/documents', { method: 'POST', body }); success++;
      }
      setUploadMessage(`${success} document${success === 1 ? '' : 's'} accepted. Processing continues in the background.`); await refresh();
    } catch (e) { setUploadMessage(`${success} accepted. ${(e as Error).message}`); } finally { setUploadBusy(false); if (fileInput.current) fileInput.current.value = ''; }
  }

  async function compare(doc: Document) {
    setCompareDoc(doc); setCompared([]); setError('');
    try { const data = await Promise.all(doc.versions.slice(-2).map(v => api<{ items: Passage[] }>(`/versions/${v.id}/passages`))); setCompared(data.map(r => r.items)); }
    catch (e) { setError((e as Error).message); }
  }


  return <div className="app-shell"><aside className="sidebar"><Brand/><div className="workspace-label"><span className="workspace-avatar">K</span><span>Your workspace<small>Private knowledge base</small></span><ShieldCheck size={15}/></div><span className="nav-label">WORKSPACE</span><nav>{([
    ['workspace', MessageSquare, 'Ask your knowledge'], ['library', Library, 'Document library'], ['evaluations', Activity, 'Evaluations'], ['system', Settings2, 'System health'],
  ] as const).map(([id, Icon, label]) => <button key={id} className={page === id ? 'nav-item active' : 'nav-item'} onClick={() => { setPage(id); setError(''); }}><Icon size={18}/>{label}{id === 'library' ? <span className="nav-count">{documents.length}</span> : null}</button>)}</nav><div className="collection-heading"><span className="nav-label">COLLECTIONS</span><button className="icon-button" title="Create collection" onClick={() => setNewCollection(true)}><Plus size={16}/></button></div><button className={`collection-item ${!collectionId ? 'selected' : ''}`} onClick={() => { setCollectionId(''); setVersionId(''); }}><Layers size={16}/>All collections<span>{documents.length}</span></button>{collections.map(c => <button key={c.id} className={`collection-item ${collectionId === c.id ? 'selected' : ''}`} onClick={() => { setCollectionId(c.id); setVersionId(''); }}><FolderClosed size={16}/><span className="truncate">{c.name}</span></button>)}{collections.length === 0 ? <p className="sidebar-hint">Create a collection to organize your first documents.</p> : null}<div className="sidebar-bottom"><div className="local-card"><ShieldCheck size={20}/><strong>Private by design</strong><p>Your sources stay local.<br/>Your evidence stays inspectable.</p></div><div className="profile"><span className="avatar">{user.email[0].toUpperCase()}</span><span className="truncate">{user.email}<small>Local account</small></span><button className="icon-button" title="Sign out" onClick={async () => { try { await api('/sessions/current', { method: 'DELETE' }); onLogout(); } catch (e) { setError((e as Error).message); } }}><LogOut size={16}/></button></div></div></aside>
    <div className="main-shell"><header className="topbar"><div className="breadcrumb">Workspace <ChevronRight size={14}/><strong>{({ workspace: 'Ask your knowledge', library: 'Document library', evaluations: 'Evaluations', system: 'System health' })[page]}</strong></div><div className="top-actions"><span className="badge quiet"><ShieldCheck size={14}/> Local processing</span><button className="secondary small" onClick={() => { setUploadOpen(true); setUploadMessage(''); }}><Upload size={15}/> Add documents</button></div></header><main className={`main-content ${source ? 'with-source' : ''}`}>
      <div className="page-content">{error ? <div className="alert" role="alert">{error}<button className="icon-button" onClick={() => setError('')} aria-label="Dismiss error"><X size={16}/></button></div> : null}
      {page === 'workspace' ? <><div className="page-heading"><div><span className="eyebrow">YOUR KNOWLEDGE WORKSPACE</span><h1>Ask your knowledge</h1><p>Clear answers, connected to your sources.</p></div><button className="text-button muted" onClick={() => { setMessages([]); setSource(null); }}><Plus size={16}/> New conversation</button></div><div className="scope-bar"><span><Database size={15}/> Knowledge scope</span><label className="select-wrap"><select aria-label="Collection scope" value={collectionId} onChange={e => { setCollectionId(e.target.value); setVersionId(''); }}><option value="">All collections</option>{collections.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select><ChevronDown size={14}/></label><label className="select-wrap"><select aria-label="Version scope" value={versionId} onChange={e => setVersionId(e.target.value)}><option value="">All source versions</option>{versions.map(v => <option key={v.id} value={v.id}>{v.title} · {v.label}</option>)}</select><ChevronDown size={14}/></label><span className="scope-count">{readyCount} indexed versions</span></div>
        <div className="conversation">{messages.length === 0 && !busy ? <div className="welcome"><div className="welcome-icon"><BookOpen size={29}/><span><Check size={12}/></span></div><span className="eyebrow">ANSWERS START HERE</span><h2>A little clarity.<br/><span>From everything you know.</span></h2><p>Ask a question about your documents.<br className="desktop"/> Get a focused answer with the source one click away.</p>{readyCount > 0 ? <div className="suggestions"><button onClick={() => ask(undefined, 'What are the main topics covered in these documents?')}><Search size={18}/><strong>Find the right guidance</strong><span>What are the main topics covered in these documents?</span><ChevronRight size={15}/></button><button onClick={() => ask(undefined, 'What differences are described across these sources?')}><GitCompareArrows size={18}/><strong>Explore across versions</strong><span>What differences are described across these sources?</span><ChevronRight size={15}/></button></div> : <div className="empty-start"><button className="primary" onClick={() => collections.length ? setUploadOpen(true) : setNewCollection(true)}><Plus size={17}/>{collections.length ? 'Add your first document' : 'Create your first collection'}</button><span>PDF, DOCX, Markdown, and HTML · 20 MB per file</span></div>}<div className="trust-row"><span><CheckCheck size={16}/> Inspectable sources</span><span><Layers size={16}/> Version-aware</span><span><ShieldCheck size={16}/> Permission-scoped</span></div></div> : messages.map((m, i) => <article className="message" key={i}><div className="question-row"><span className="avatar">{user.email[0].toUpperCase()}</span><h3>{m.question}</h3></div><div className="answer-row"><div className="answer-mark"><Sparkles size={17}/></div><div className="answer-body"><div className="answer-label">KnowDoc AI <span className={`badge ${m.answer.status === 'insufficient_evidence' || m.answer.status === 'conflicting_evidence' ? 'amber' : 'mint'}`}>{m.answer.status.replaceAll('_', ' ')}</span></div><div className="answer-text">{m.answer.answer}{m.answer.status === 'answered' ? m.answer.citations.map((p, index) => <button key={p.id} className="inline-reference" aria-label={`Open reference ${index + 1}`} title={`${p.title} ? ${p.location.page ? `Page ${p.location.page}` : p.location.section || p.version}`} onClick={() => setSource(p)}>[{index + 1}]</button>) : null}</div>{m.answer.conflicts?.map((conflict, cidx) => <div className="conflict-box" key={cidx}><strong>Potential source conflict</strong><p>{conflict.reason}</p>{conflict.quotes.map((quote, qi) => <blockquote key={qi}><span>Version {conflict.versions[qi]}</span>{quote}</blockquote>)}</div>)}{m.answer.citations.length > 0 ? <details className="answer-sources" open={m.answer.status !== 'answered'}><summary>Sources ({m.answer.citations.length})</summary>{m.answer.claims.map((claim, ci) => <div key={ci} className="claim-quote"><span>Supporting quote</span><blockquote>{claim.quote}</blockquote>{claim.citation_ids.map(id => { const p = m.answer.citations.find(s => s.id === id); return p ? <button key={id} className="citation-chip" onClick={() => setSource(p)}><FileText size={13}/>{p.title} · {p.version}</button> : null; })}</div>)}{m.answer.citations.length ? <div className="evidence-list"><div className="evidence-heading"><BookOpen size={15}/> {m.answer.citations.length} source passages <span>Click to inspect</span></div>{m.answer.citations.map((p, pi) => <button className={`evidence-card ${source?.id === p.id ? 'chosen' : ''}`} key={p.id} onClick={() => setSource(p)}><span className="evidence-number">{pi + 1}</span><div><strong>{p.title}</strong><span className="passage-preview">{p.text.slice(0, 190)}{p.text.length > 190 ? '…' : ''}</span><small>Version {p.version} · {p.location.page ? `Page ${p.location.page}` : p.location.section || 'Document'}</small></div><ChevronRight size={16}/></button>)}</div> : null}</details> : null}<div className="response-meta"><span>{(m.answer.timings.total_ms / 1000).toFixed(2)}s</span><span>{m.answer.answer_method === 'extractive' ? 'Document fact | source verified' : m.answer.mode === 'evidence' ? 'Source retrieval | no generation' : 'Local answer | references validated'}</span></div><details className="limitations"><summary>Limitations and uncertainty</summary>{m.answer.limitations.map(l => <p key={l}>{l}</p>)}</details></div></div></article>)}{busy ? <div className="working"><LoaderCircle className="spin" size={18}/>{mode === 'generate' ? 'Reading evidence and generating locally…' : 'Finding relevant source passages…'}</div> : null}<div ref={end}/></div>
        <form className="composer" onSubmit={e => ask(e)}><textarea aria-label="Ask a question" placeholder="Ask a question about your documents…" value={question} onChange={e => setQuestion(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask(); } }} rows={2} maxLength={2000}/><div className="composer-bottom"><div><label className="select-wrap"><select aria-label="Answer mode" value={mode} onChange={e => setMode(e.target.value)}><option value="evidence">Evidence only</option><option value="generate">Answer with sources</option></select><ChevronDown size={13}/></label><label className="select-wrap retrieval-select"><select aria-label="Retrieval method" value={method} onChange={e => setMethod(e.target.value)}><option value="hybrid">Hybrid retrieval</option><option value="keyword">Keyword search</option><option value="dense">Semantic search</option><option value="hybrid_rerank">Hybrid + reranking</option></select><ChevronDown size={13}/></label></div><button className="send-button" type="submit" disabled={busy || question.trim().length < 3} aria-label="Send question">{busy ? <LoaderCircle size={19} className="spin"/> : <ArrowUp size={20}/>}</button></div></form><p className="composer-disclaimer"><CircleHelp size={13}/> Answers can be incomplete. Always inspect source evidence for important decisions.</p></> : null}
      {page === 'library' ? <><div className="page-heading"><div><span className="eyebrow">YOUR SOURCE OF KNOWLEDGE</span><h1>Document library</h1><p>Organize your sources. Keep every version in view.</p></div><button className="primary small" onClick={() => setUploadOpen(true)}><Upload size={16}/> Upload documents</button></div><div className="stat-strip"><div><Library size={19}/><strong>{visibleDocs.length}</strong><span>Documents</span></div><div><CheckCheck size={19}/><strong>{readyCount}</strong><span>Indexed versions</span></div><div><LoaderCircle size={19}/><strong>{processing}</strong><span>Processing jobs</span></div></div><section className="table-card"><div className="section-heading"><h2>Sources</h2><span className="badge quiet">{collectionId ? collections.find(c => c.id === collectionId)?.name : 'All collections'}</span></div>{!visibleDocs.length ? <div className="empty-block"><FileText size={30}/><h3>No documents yet</h3><p>Add a document to begin building your knowledge base.</p></div> : <div className="document-table"><div className="table-head"><span>DOCUMENT</span><span>VERSIONS</span><span>STATUS</span><span>ACTIONS</span></div>{visibleDocs.map(d => <div className="document-row" key={d.id}><div><span className="file-icon"><FileText size={21}/></span><span><strong>{d.title}</strong><small>{collections.find(c => c.id === d.collection_id)?.name || 'Shared document'} · {d.versions[0]?.file_type.toUpperCase()}</small></span></div><span>{d.versions.map(v => <button className="version-tag" key={v.id} title="Open stored passages" onClick={() => { setCompareDoc(d); setCompared([]); api<{ items: Passage[] }>(`/versions/${v.id}/passages`).then(r => setCompared([r.items])).catch(e => setError(e.message)); }}>{v.label}</button>)}</span><span className={`badge ${d.versions.every(v => v.status === 'ready') ? 'mint' : 'amber'}`}>{d.versions.every(v => v.status === 'ready') ? 'Indexed' : d.versions.at(-1)?.status}</span><div className="row-actions">{d.owned ? <button className="icon-button" title="Manage document" onClick={() => setManageDoc(d)}><Settings2 size={17}/></button> : null}<button className="icon-button" title="Compare latest two uploaded versions" disabled={d.versions.length < 2} onClick={() => compare(d)}><GitCompareArrows size={17}/></button>{d.owned ? <button className="icon-button" title="Add a source version" onClick={() => { setCollectionId(d.collection_id); setNewVersionDoc(d.id); setUploadOpen(true); setUploadMessage(''); }}><Plus size={17}/></button> : null}</div></div>)}</div>}</section><section className="table-card jobs-card"><div className="section-heading"><h2>Ingestion activity</h2><span className="muted">Refreshes every 4 seconds</span></div>{jobs.length === 0 ? <p className="empty-inline">No ingestion jobs have run.</p> : jobs.slice(0, 12).map(j => <div className="job-row" key={j.id}><FileText size={16}/><div><strong>{j.title}</strong><small>Version {j.version} · Attempt {j.attempts}</small></div><span>{j.timings.chunks !== undefined ? `${j.timings.chunks} chunks` : j.error || 'Waiting for worker'}</span><span className={`badge ${j.status === 'ready' ? 'mint' : 'amber'}`}>{j.status}</span>{j.status === 'failed' ? <button className="text-button" onClick={() => api(`/jobs/${j.id}/retry`, { method: 'POST' }).then(refresh).catch(e => setError(e.message))}>Retry</button> : null}</div>)}</section></> : null}
      {page === 'evaluations' ? <><div className="page-heading"><div><span className="eyebrow">MEASURED, NOT ASSUMED</span><h1>Evaluations</h1><p>Retrieval quality and failure analysis, tied to real runs.</p></div><button className="primary small" disabled={evalTasks.some(t => ['queued','running'].includes(t.status))} onClick={() => api('/evaluations', {method: 'POST'}).then(() => api<{items: EvalRun[]; tasks: typeof evalTasks}>('/evaluations')).then(r => {setRuns(r.items);setEvalTasks(r.tasks || []);}).catch(e => setError(e.message))}><Activity size={16}/> Run benchmark</button></div>{evalTasks.slice(0,1).map(t => <p className="eval-task" key={t.id}>Latest benchmark: {t.status}{t.error ? ` ? ${t.error}` : ''}</p>)}{runs.length === 0 ? <section className="empty-block table-card"><Activity size={35}/><h2>No evaluation runs yet</h2><p>Run the local benchmark against indexed sources to see measured results here.</p><p className="fine">No sample scores are shown. Human-reviewed release gates remain open until annotations are reviewed.</p></section> : runs.map(run => <EvaluationCard key={run.id} run={run}/>)}</> : null}
      {page === 'system' ? <><div className="page-heading"><div><span className="eyebrow">A LOOK UNDER THE HOOD</span><h1>System health</h1><p>Live configuration and indexing counts for your account.</p></div><Settings2 size={28} className="muted"/></div>{system ? <div className="system-grid">{Object.entries(system).map(([key, value]) => <section className="system-card" key={key}><span>{key.replaceAll('_', ' ')}</span><strong>{String(value)}</strong></section>)}</div> : <p>Loading system information…</p>}<div className="info-card"><ShieldCheck size={22}/><div><h3>Source text is untrusted input</h3><p>Permission checks run before retrieval output reaches the reranker or model. Every citation is resolved from stored records and checked again when you open it.</p></div></div></> : null}
      </div>{source ? <SourcePanel source={source} close={() => setSource(null)}/> : null}</main></div>
    {newCollection ? <div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="collection-title"><div className="panel-title"><h2 id="collection-title">Create a collection</h2><button className="icon-button" aria-label="Close" onClick={() => setNewCollection(false)}><X size={20}/></button></div><p>Group related documents in a private knowledge collection.</p><form onSubmit={addCollection}><label>Collection name<input autoFocus required maxLength={120} placeholder="e.g. Engineering reference" value={collectionName} onChange={e => setCollectionName(e.target.value)}/></label><button className="primary" type="submit">Create collection</button></form></section></div> : null}
    {uploadOpen ? <div className="modal-backdrop"><section className="modal upload-modal" role="dialog" aria-modal="true" aria-labelledby="upload-title"><div className="panel-title"><h2 id="upload-title">Add to your knowledge</h2><button className="icon-button" aria-label="Close upload" onClick={() => { setUploadOpen(false); setNewVersionDoc(''); }}><X size={20}/></button></div><p>Sources are private to your account unless explicitly shared.</p><label>Collection<select value={collectionId} onChange={e => setCollectionId(e.target.value)} required><option value="">Choose a collection</option>{collections.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label>{collections.length === 0 ? <button className="text-button" onClick={() => { setUploadOpen(false); setNewCollection(true); }}>Create a collection first</button> : null}<label>Source version<input value={versionLabel} onChange={e => setVersionLabel(e.target.value)} maxLength={100} placeholder="e.g. 19.0 or internal-v2"/></label>{newVersionDoc ? <p className="badge mint">Adding a version to {documents.find(d => d.id === newVersionDoc)?.title}</p> : null}<div className={`dropzone ${uploadBusy ? 'disabled' : ''}`} onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); if (!uploadBusy) upload(e.dataTransfer.files); }}><Upload size={29}/><h3>Drop your documents here</h3><p>PDF, DOCX, Markdown, HTML · Up to 20 MB each</p><button className="secondary" disabled={uploadBusy} onClick={() => fileInput.current?.click()}>{uploadBusy ? 'Uploading…' : 'Choose files'}</button><input ref={fileInput} type="file" multiple accept=".pdf,.docx,.md,.markdown,.html,.htm" hidden onChange={e => e.target.files && upload(e.target.files)}/></div>{uploadMessage ? <p role="status" className="upload-message">{uploadMessage}</p> : null}<p className="fine"><ShieldCheck size={14}/> Files are checked, versioned, and indexed in the background.</p></section></div> : null}
    {manageDoc ? <DocumentManager document={manageDoc} close={() => setManageDoc(null)} refresh={refresh}/> : null}
    {compareDoc ? <div className="modal-backdrop"><section className="modal compare-modal" role="dialog" aria-modal="true" aria-labelledby="compare-title"><div className="panel-title"><h2 id="compare-title">{compareDoc.title} · source passages</h2><button className="icon-button" aria-label="Close comparison" onClick={() => setCompareDoc(null)}><X size={20}/></button></div><p>Stored versions are shown independently. Upload order does not establish which guidance is current.</p><div className="compare-grid">{compared.length ? compared.map((passages, i) => <div key={i}><h3>Version {passages[0]?.version || 'not indexed'}</h3>{passages.map(p => <button className="compare-passage" key={p.id} onClick={() => { setSource(p); setCompareDoc(null); }}><small>{p.location.section || (p.location.page ? `Page ${p.location.page}` : 'Document')}</small><span>{p.text}</span></button>)}</div>) : <p>Loading stored passages…</p>}</div></section></div> : null}
  </div>;
}

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(true);
  useEffect(() => {
    let active = true;
    api<{user: User; csrf_token: string}>('/sessions/me').then(result => {
      if (active) {setCsrf(result.csrf_token); setUser(result.user);}
    }).catch(() => {}).finally(() => {if (active) setChecking(false);});
    return () => {active = false;};
  }, []);
  if (checking) return <div className="boot"><LoaderCircle className="spin"/> Opening your workspace...</div>;
  if (!user) return <Auth onLogin={setUser}/>;
  return <Workspace key={user.id} user={user} onLogout={() => {setCsrf('');setUser(null);}}/>;
}

createRoot(document.getElementById('root')!).render(<StrictMode><App/></StrictMode>);
