import React, { useState } from 'react';
import ReactDOM from 'react-dom';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5000';

const PRESETS = [
    { label: 'Today', type: 'daily' },
    { label: 'Last 7 Days', type: 'weekly' },
    { label: 'Last 30 Days', type: 'monthly' },
    { label: 'Custom Range', type: 'custom' },
];

function ReportModal({ onClose, token }) {
    const [selected, setSelected] = useState('weekly');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const handleDownload = async () => {
        setError('');
        setSuccess('');

        if (selected === 'custom' && (!startDate || !endDate)) {
            setError('Please pick both a start and end date.');
            return;
        }
        if (selected === 'custom' && startDate > endDate) {
            setError('Start date must be before end date.');
            return;
        }

        setLoading(true);
        try {
            let url = `${API_URL}/reports/generate?type=${selected}`;
            if (selected === 'custom') {
                url += `&start=${startDate}&end=${endDate}`;
            }

            const res = await axios.get(url, {
                headers: { Authorization: `Bearer ${token}` },
                responseType: 'blob',
            });

            // Derive filename from Content-Disposition or fallback
            const cd = res.headers['content-disposition'] || '';
            const match = cd.match(/filename="?([^"]+)"?/);
            const filename = match ? match[1] : `uba_report_${new Date().toISOString().slice(0, 10)}.pdf`;

            // Trigger browser download
            const blobUrl = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
            const a = document.createElement('a');
            a.href = blobUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(blobUrl);

            setSuccess(`✅ Downloaded: ${filename}`);
        } catch (err) {
            if (err.response?.status === 403) {
                setError('Access denied. Admin or Analyst role required.');
            } else {
                setError('Failed to generate report. Please try again.');
            }
        } finally {
            setLoading(false);
        }
    };

    const modal = (
        <div className="rm-backdrop" onClick={onClose}>
            <div className="rm-modal" onClick={e => e.stopPropagation()}>

                {/* Header */}
                <div className="rm-header">
                    <div className="rm-header__left">
                        <span className="rm-header__icon">📄</span>
                        <div>
                            <div className="rm-header__title">Download Report</div>
                            <div className="rm-header__sub">PDF format · Risk analytics summary</div>
                        </div>
                    </div>
                    <button className="rm-close" onClick={onClose}>✕</button>
                </div>

                {/* Preset selector */}
                <div className="rm-body">
                    <div className="rm-section-label">Report Period</div>
                    <div className="rm-presets">
                        {PRESETS.map(p => (
                            <button
                                key={p.type}
                                className={`rm-preset ${selected === p.type ? 'rm-preset--active' : ''}`}
                                onClick={() => { setSelected(p.type); setError(''); setSuccess(''); }}
                            >
                                {p.label}
                            </button>
                        ))}
                    </div>

                    {/* Custom date pickers */}
                    {selected === 'custom' && (
                        <div className="rm-dates">
                            <div className="rm-date-field">
                                <label className="rm-date-label">From</label>
                                <input
                                    type="date"
                                    className="rm-date-input"
                                    value={startDate}
                                    max={endDate || undefined}
                                    onChange={e => setStartDate(e.target.value)}
                                />
                            </div>
                            <div className="rm-date-sep">→</div>
                            <div className="rm-date-field">
                                <label className="rm-date-label">To</label>
                                <input
                                    type="date"
                                    className="rm-date-input"
                                    value={endDate}
                                    min={startDate || undefined}
                                    max={new Date().toISOString().slice(0, 10)}
                                    onChange={e => setEndDate(e.target.value)}
                                />
                            </div>
                        </div>
                    )}

                    {/* What's included info */}
                    <div className="rm-info-box">
                        <div className="rm-info-row">📊 <span>Executive summary with total, high-risk, and locked counts</span></div>
                        <div className="rm-info-row">📈 <span>Risk score breakdown and statistics</span></div>
                        <div className="rm-info-row">🚨 <span>Top 20 flagged (HIGH_RISK + LOCKED) activity log</span></div>
                    </div>

                    {/* Error / Success */}
                    {error && <div className="rm-alert rm-alert--error">⚠️ {error}</div>}
                    {success && <div className="rm-alert rm-alert--success">{success}</div>}

                    {/* Download button */}
                    <button
                        className="rm-download-btn"
                        onClick={handleDownload}
                        disabled={loading}
                    >
                        {loading ? (
                            <><span className="rm-spinner" /> Generating PDF…</>
                        ) : (
                            <><span>⬇️</span> Download PDF Report</>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );

    return ReactDOM.createPortal(modal, document.body);
}

export default ReportModal;
