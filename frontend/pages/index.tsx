import React from 'react';
import Link from 'next/link';

const stats = [
  { label: 'Sources', value: '12', tone: '#76d6ff' },
  { label: 'Batches', value: '48', tone: '#8ee3a8' },
  { label: 'Exceptions', value: '16', tone: '#ffd166' },
  { label: 'Readiness', value: '84%', tone: '#8ac5ff' },
];

export default function Home() {
  return (
    <main style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0b1020 0%, #111827 100%)',
      color: '#e6edf7',
      padding: '48px 24px'
    }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <header style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 32
        }}>
          <div>
            <div style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: 2, color: '#7dd3fc' }}>PensionOS</div>
            <h1 style={{ margin: '8px 0 0', fontSize: 36 }}>Data Onboarding & Resolution Factory</h1>
          </div>
          <Link href="/sources" style={{
            background: '#1d4ed8',
            color: 'white',
            borderRadius: 10,
            padding: '12px 18px',
            fontWeight: 600,
            boxShadow: '0 10px 30px rgba(29,78,216,0.4)'
          }}>
            Open registry
          </Link>
        </header>

        <section style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 18,
          marginBottom: 32
        }}>
          {stats.map((stat) => (
            <div key={stat.label} style={{
              background: 'rgba(15, 23, 42, 0.9)',
              border: '1px solid rgba(148,163,184,0.2)',
              borderRadius: 14,
              padding: 20
            }}>
              <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 8 }}>{stat.label}</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: stat.tone }}>{stat.value}</div>
            </div>
          ))}
        </section>

        <section style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: 18
        }}>
          <div style={{
            background: 'rgba(15, 23, 42, 0.9)',
            border: '1px solid rgba(148,163,184,0.2)',
            borderRadius: 14,
            padding: 20
          }}>
            <h3 style={{ marginTop: 0 }}>Operational focus</h3>
            <ul style={{
              margin: 0,
              paddingLeft: 18,
              lineHeight: 1.9,
              color: '#cbd5e1'
            }}>
              <li>Source registration and lifecycle</li>
              <li>Secure intake and quarantine</li>
              <li>Profiling and mapping packs</li>
              <li>DQ, trust, and exception workbench</li>
            </ul>
          </div>

          <div style={{
            background: 'rgba(15, 23, 42, 0.9)',
            border: '1px solid rgba(148,163,184,0.2)',
            borderRadius: 14,
            padding: 20
          }}>
            <h3 style={{ marginTop: 0 }}>Bounded-context model</h3>
            <ul style={{
              margin: 0,
              paddingLeft: 18,
              lineHeight: 1.9,
              color: '#cbd5e1'
            }}>
              <li>Domain logic stays in <code>data_onboarding</code></li>
              <li>Backend exposes APIs</li>
              <li>Frontend renders operational views</li>
              <li>Ownership remains separate from Member/Payroll domains</li>
            </ul>
          </div>
        </section>
      </div>
    </main>
  );
}
