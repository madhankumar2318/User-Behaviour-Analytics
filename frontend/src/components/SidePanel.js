import React, { useEffect } from 'react';
import ReactDOM from 'react-dom';

function SidePanel({ selectedUser, onClose }) {
    useEffect(() => {
        // When a user is selected: lock scroll + listen for Escape
        // When selectedUser becomes null (modal closed): restore scroll
        if (!selectedUser) {
            document.body.style.overflow = '';
            return; // nothing else to set up
        }

        const handleEsc = (e) => { if (e.key === 'Escape') onClose(); };
        window.addEventListener('keydown', handleEsc);
        document.body.style.overflow = 'hidden';

        return () => {
            window.removeEventListener('keydown', handleEsc);
            document.body.style.overflow = ''; // always restore on cleanup
        };
    }, [selectedUser, onClose]); // re-run when selectedUser changes (open ↔ close)

    if (!selectedUser) return null;

    // ── helpers ──────────────────────────────────────────────────────────
    const statusMeta = {
        LOCKED: { color: '#ef4444', glow: 'rgba(239,68,68,0.4)', bg: 'rgba(239,68,68,0.12)', icon: '🔒' },
        HIGH_RISK: { color: '#f59e0b', glow: 'rgba(245,158,11,0.4)', bg: 'rgba(245,158,11,0.1)', icon: '⚠️' },
        ACTIVE: { color: '#10b981', glow: 'rgba(16,185,129,0.35)', bg: 'rgba(16,185,129,0.08)', icon: '✅' },
    };
    const meta = statusMeta[selectedUser.status] || statusMeta.ACTIVE;

    const initials = (selectedUser.user_id || 'U')
        .replace(/[^a-zA-Z0-9]/g, '')
        .slice(0, 2)
        .toUpperCase();

    const score = typeof selectedUser.risk_score === 'number'
        ? selectedUser.risk_score
        : parseFloat(selectedUser.risk_score) || 0;

    const pct = Math.min(100, Math.max(0, score));
    const scoreColor = pct >= 70 ? '#ef4444' : pct >= 40 ? '#f59e0b' : '#10b981';

    const modal = (
        /* ── backdrop ─────────────────────────────────────────────────────
           Rendered via portal → directly on document.body, so position:fixed
           works relative to the TRUE viewport regardless of any parent
           transforms (e.g. .container { transform: translateZ(0) })
        ── */
        <div className="sp-backdrop" onClick={onClose}>
            <div className="sp-modal" onClick={e => e.stopPropagation()}>

                {/* ── Gradient Header ── */}
                <div className="sp-modal-header">
                    <div
                        className="sp-avatar"
                        style={{ boxShadow: `0 0 0 3px ${meta.color}, 0 0 20px ${meta.glow}` }}
                    >
                        {initials}
                    </div>

                    <div className="sp-modal-header__info">
                        <span className="sp-modal-header__user">{selectedUser.user_id || '—'}</span>
                        <span
                            className="sp-modal-header__badge"
                            style={{ background: meta.color }}
                        >
                            {meta.icon} {selectedUser.status || 'UNKNOWN'}
                        </span>
                    </div>

                    <button className="sp-modal-close" onClick={onClose} title="Close (Esc)">✕</button>
                </div>

                {/* ── Body ── */}
                <div className="sp-modal-body">

                    {/* Risk Score Gauge */}
                    <div className="sp-gauge-card">
                        <div className="sp-gauge-label">Risk Score</div>
                        <div className="sp-gauge-bar-bg">
                            <div
                                className="sp-gauge-bar-fill"
                                style={{
                                    width: `${pct}%`,
                                    background: `linear-gradient(90deg, #10b981, ${scoreColor})`,
                                }}
                            />
                        </div>
                        <div className="sp-gauge-value" style={{ color: scoreColor }}>
                            {score.toFixed(1)}
                            <span style={{ color: '#475569', fontSize: '0.75rem' }}> / 100</span>
                        </div>
                    </div>

                    {/* 2-col stat grid */}
                    <div className="sp-stat-grid">
                        <StatCard icon="🕐" label="Login Time" value={selectedUser.login_time} />
                        <StatCard icon="📍" label="Location" value={selectedUser.location} />
                        <StatCard icon="⬇️" label="Downloads" value={selectedUser.downloads} />
                        <StatCard icon="❌" label="Failed Attempts" value={selectedUser.failed_attempts} />
                    </div>

                    {/* IP / Device */}
                    <div className="sp-mono-card">
                        <div className="sp-mono-row">
                            <span className="sp-mono-label">🌐 IP Address</span>
                            <span className="sp-mono-val">{selectedUser.ip_address || 'N/A'}</span>
                        </div>
                        {selectedUser.device_fingerprint && (
                            <div className="sp-mono-row">
                                <span className="sp-mono-label">💻 Device</span>
                                <span className="sp-mono-val" style={{ fontSize: '0.72rem' }}>
                                    {selectedUser.device_fingerprint}
                                </span>
                            </div>
                        )}
                    </div>

                    {/* ML Insights */}
                    {selectedUser.ml_anomaly !== undefined && (
                        <div className="sp-insight-card">
                            <div className="sp-card-title">🤖 ML Insights</div>
                            <div className="sp-insight-row">
                                <span>Anomaly Detected</span>
                                {selectedUser.ml_anomaly
                                    ? <span className="sp-tag sp-tag--red">⚠️ Yes</span>
                                    : <span className="sp-tag sp-tag--green">✅ No</span>}
                            </div>
                            {selectedUser.ml_confidence !== undefined && (
                                <div className="sp-insight-row">
                                    <span>ML Confidence</span>
                                    <span className="sp-tag sp-tag--purple">
                                        {(+selectedUser.ml_confidence).toFixed(1)}%
                                    </span>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Velocity Alerts */}
                    {selectedUser.velocity_alerts && (
                        <div className="sp-velocity">
                            ⚡ Rapid or impossible travel detected
                        </div>
                    )}

                    {/* Risk Reasons */}
                    {selectedUser.risk_reasons?.length > 0 && (
                        <div className="sp-reasons-card">
                            <div className="sp-card-title">🚨 Risk Reasons</div>
                            {selectedUser.risk_reasons.map((r, i) => (
                                <div key={i} className="sp-reason">{r}</div>
                            ))}
                        </div>
                    )}

                    <button className="sp-close-action" onClick={onClose}>Close Panel</button>
                </div>
            </div>
        </div>
    );

    // Portal renders directly into document.body — bypasses all parent CSS transforms
    return ReactDOM.createPortal(modal, document.body);
}

function StatCard({ icon, label, value }) {
    return (
        <div className="sp-stat-card">
            <span className="sp-stat-icon">{icon}</span>
            <span className="sp-stat-label">{label}</span>
            <span className="sp-stat-value">{value ?? '—'}</span>
        </div>
    );
}

export default SidePanel;
