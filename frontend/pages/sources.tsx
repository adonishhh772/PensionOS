import { useEffect, useState } from 'react';
import Link from 'next/link';

type SourceRecord = {
  id: string;
  source_name: string;
  source_type: string;
  scheme_id: string;
  status?: string;
};

export default function SourcesPage() {
  const [sources, setSources] = useState<SourceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/sources')
      .then((res) => res.json())
      .then((data) => {
        setSources(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(() => {
        setError('Unable to load source registry');
        setLoading(false);
      });
  }, []);

  return (
    <main style={{ minHeight: '100vh', background: '#0b1020', color: '#e2e8f0', padding: '48px 24px' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
          <div>
            <div style={{ fontSize: 12, letterSpacing: 2, textTransform: 'uppercase', color: '#7dd3fc' }}>Registry</div>
            <h1 style={{ margin: '8px 0 0' }}>Source Registry</h1>
          </div>
          <Link href="/" style={{ color: '#e2e8f0', border: '1px solid rgba(148,163,184,0.3)', borderRadius: 10, padding: '10px 14px' }}>
            Dashboard
          </Link>
        </header>

        {loading ? (
          <div style={{ background: '#0f172a', borderRadius: 12, padding: 24 }}>Loading registry…</div>
        ) : error ? (
          <div style={{ background: '#7f1d1d', borderRadius: 12, padding: 24, color: '#fee2e2' }}>{error}</div>
        ) : (
          <div style={{ background: '#111827', borderRadius: 16, overflow: 'hidden', border: '1px solid rgba(148,163,184,0.2)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead style={{ background: '#0f172a' }}>
                <tr>
                  <th style={{ textAlign: 'left', padding: '16px 18px' }}>Source</th>
                  <th style={{ textAlign: 'left', padding: '16px 18px' }}>Type</th>
                  <th style={{ textAlign: 'left', padding: '16px 18px' }}>Scheme</th>
                  <th style={{ textAlign: 'left', padding: '16px 18px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((source) => (
                  <tr key={source.id} style={{ borderTop: '1px solid rgba(148,163,184,0.15)' }}>
                    <td style={{ padding: '16px 18px' }}>{source.source_name}</td>
                    <td style={{ padding: '16px 18px' }}>{source.source_type}</td>
                    <td style={{ padding: '16px 18px' }}>{source.scheme_id}</td>
                    <td style={{ padding: '16px 18px' }}>{source.status ?? 'REGISTERED'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}
