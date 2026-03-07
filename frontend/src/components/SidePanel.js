import React, { useEffect } from 'react';

function SidePanel({ selectedUser, onClose }) {
    // Close on escape key
    useEffect(() => {
        const handleEsc = (e) => {
            if (e.key === 'Escape') onClose();
        };
        window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
    }, [onClose]);

    if (!selectedUser) return null;

    return (
        <div className="side-panel-overlay" onClick={onClose}>
            <div className="side-panel" onClick={(e) => e.stopPropagation()}>
                <div className="panel-content">
                    <div className="panel-header">
                        <h2>User Behavioral Profile</h2>
                        <button className="panel-close-btn" onClick={onClose} title="Close Panel">×</button>
                    </div>

                    <div className="profile-details-grid">
                        <span className="profile-label">User ID:</span>
                        <span className="profile-value">{selectedUser.user_id}</span>

                        <span className="profile-label">Login Time:</span>
                        <span className="profile-value">{selectedUser.login_time}</span>

                        <span className="profile-label">Location:</span>
                        <span className="profile-value">{selectedUser.location}</span>

                        <span className="profile-label">IP Address:</span>
                        <span className="profile-value" style={{ color: '#00f5ff', fontFamily: 'monospace' }}>
                            {selectedUser.ip_address || 'N/A'}
                        </span>

                        <span className="profile-label">Device:</span>
                        <span className="profile-value" style={{ color: '#a78bfa', fontSize: '0.85rem', fontFamily: 'monospace' }}>
                            {selectedUser.device_fingerprint || 'N/A'}
                        </span>

                        <span className="profile-label">Downloads:</span>
                        <span className="profile-value">{selectedUser.downloads}</span>

                        <span className="profile-label">Failed Attempts:</span>
                        <span className="profile-value">{selectedUser.failed_attempts}</span>

                        <span className="profile-label">Risk Score:</span>
                        <span className="profile-value">{selectedUser.risk_score}</span>

                        <span className="profile-label">Status:</span>
                        <span className="profile-value">{selectedUser.status}</span>
                    </div>

                    {/* ML Insights */}
                    {selectedUser.ml_anomaly !== undefined && (
                        <div className="insight-box" style={{ marginBottom: '20px' }}>
                            <h4 style={{ color: '#00f5ff', margin: '0 0 10px 0' }}>🤖 ML Insights</h4>
                            <p style={{ margin: '5px 0' }}>
                                <strong style={{ color: '#a78bfa' }}>Anomaly Detected:</strong>{" "}
                                {selectedUser.ml_anomaly ? (
                                    <span style={{ color: "#dc2626" }}>⚠️ Yes</span>
                                ) : (
                                    <span style={{ color: "#10b981" }}>✅ No</span>
                                )}
                            </p>
                            {selectedUser.ml_confidence && (
                                <p style={{ margin: '5px 0' }}>
                                    <strong style={{ color: '#a78bfa' }}>ML Confidence:</strong> {selectedUser.ml_confidence}%
                                </p>
                            )}
                        </div>
                    )}

                    {/* Velocity Alerts */}
                    {selectedUser.velocity_alerts && (
                        <div className="insight-box warning" style={{ marginBottom: '20px' }}>
                            <h4 style={{ color: '#00f5ff', margin: '0 0 10px 0' }}>⚡ Velocity Alerts</h4>
                            <p style={{ color: "#f59e0b", margin: 0 }}>
                                ⚠️ Rapid activity or impossible travel detected
                            </p>
                        </div>
                    )}

                    {selectedUser.risk_reasons && (
                        <div style={{ marginBottom: '20px' }}>
                            <h4 style={{ color: '#00f5ff', margin: '0 0 10px 0' }}>Risk Reasons:</h4>
                            <ul className="reasons-list" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                                {selectedUser.risk_reasons.map((reason, i) => (
                                    <li key={i} style={{
                                        background: 'rgba(220, 38, 38, 0.2)',
                                        padding: '10px',
                                        margin: '8px 0',
                                        borderRadius: '6px',
                                        borderLeft: '3px solid #dc2626'
                                    }}>
                                        {reason}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    <div style={{ marginTop: '30px' }}>
                        <button className="side-panel-action-btn">View Full Profile</button>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default SidePanel;
