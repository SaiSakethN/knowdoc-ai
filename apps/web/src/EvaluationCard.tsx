import type { EvalRun } from './api';

export function EvaluationCard({ run }: { run: EvalRun }) {
  const groups = new Map<string, { attempts: number; matches: number; violations: number }>();
  for (const item of run.report.behavior || []) {
    const group = groups.get(item.category) || { attempts: 0, matches: 0, violations: 0 };
    group.attempts++;
    if (item.status_match) group.matches++;
    if (item.no_forbidden_output === false) group.violations++;
    groups.set(item.category, group);
  }
  return <section className="table-card"><div className="section-heading"><div><h2>{run.report.dataset}</h2><p className="fine">{new Date(run.created_at).toLocaleString()} · {run.report.annotation_status}</p></div><span className="badge amber">Provisional benchmark</span></div>{run.report.results.length ? <div className="metrics-table"><table><thead><tr><th>Method</th><th>Recall@5</th><th>MRR@5</th><th>nDCG@5</th><th>p95</th><th>Cases</th><th>Errors</th></tr></thead><tbody>{run.report.results.map(result => <tr key={result.method}><td>{result.method}</td><td>{result.recall_at_5?.toFixed(3) ?? 'Unavailable'}</td><td>{result.mrr?.toFixed(3) ?? 'Unavailable'}</td><td>{result.ndcg_at_5?.toFixed(3) ?? 'Unavailable'}</td><td>{result.p95_ms === null ? 'Unavailable' : `${result.p95_ms.toFixed(0)} ms`}</td><td>{result.cases}</td><td>{result.errors || 0}</td></tr>)}</tbody></table></div> : <p className="empty-inline">Generation and behavior run; retrieval baselines were not repeated.</p>}{groups.size ? <div className="metrics-table"><table><caption className="behavior-caption">Deterministic expected-status checks · not human correctness scores</caption><thead><tr><th>Category</th><th>Attempts</th><th>Status matches</th><th>Flagged outputs</th></tr></thead><tbody>{Array.from(groups).map(([name, value]) => <tr key={name}><td>{name.replaceAll('_', ' ')}</td><td>{value.attempts}</td><td>{value.matches}</td><td>{value.violations}</td></tr>)}</tbody></table></div> : null}{run.report.failures?.length ? <details className="failure-details"><summary>{run.report.failures.length} recorded retrieval misses</summary>{run.report.failures.slice(0, 12).map((failure, index) => <p key={index}>{failure.case_id} · {failure.method} · {failure.reason.replaceAll('_', ' ')}</p>)}</details> : null}<div className="eval-limitations">{run.report.release_gate ? <strong>{run.report.release_gate}</strong> : null}{run.report.limitations.map(limit => <p key={limit}>{limit}</p>)}</div></section>;
}
