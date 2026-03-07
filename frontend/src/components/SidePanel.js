import React from 'react';

function SidePanel({ selectedUser, onClose }) {
    if (!selectedUser) return null;

    return (
        <div className="side-panel">
            <div className="panel-content">
                <div className="panel-header">
                    <h2>User Behavioral Profile</h2>
                    <button className="close-btn" onClick={onClose}>×</button>
                </div>

                <p><strong>User ID:</strong> {selectedUser.user_id}</p>
                <p><strong>Login Time:</strong> {selectedUser.login_time}</p>
                <p><strong>Location:</strong> {selectedUser.location}</p>
                <p><strong>IP Address:</strong> <span style={{ color: '#00f5ff', fontFamily: 'monospace' }}>{selectedUser.ip_address || 'N/A'}</span></p>
                <p><strong>Device:</strong> <span style={{ color: '#a78bfa', fontSize: '0.85rem', fontFamily: 'monospace' }}>{selectedUser.device_fingerprint || 'N/A'}</span></p>
                <p><strong>Downloads:</strong> {selectedUser.downloads}</p>
                <p><strong>Failed Attempts:</strong> {selectedUser.failed_attempts}</p>
                <p><strong>Risk Score:</strong> {selectedUser.risk_score}</p>
                <p><strong>Status:</strong> {selectedUser.status}</p>

                {/* ML Insights */}
                {selectedUser.ml_anomaly !== undefined && (
                    <div className="insight-box">
                        <h4>🤖 ML Insights</h4>
                        <p>
                            <strong>Anomaly Detected:</strong>{" "}
                            {selectedUser.ml_anomaly ? (
                                <span style={{ color: "#dc2626" }}>⚠️ Yes</span>
                            ) : (
                                <span style={{ color: "#10b981" }}>✅ No</span>
                            )}
                        </p>
                        {selectedUser.ml_confidence && (
                            <p>
                                <strong>ML Confidence:</strong> {selectedUser.ml_confidence}%
                            </p>
                        )}
                    </div>
                )}

                {/* Velocity Alerts */}
                {selectedUser.velocity_alerts && (
                    <div className="insight-box warning">
                        <h4>⚡ Velocity Alerts</h4>
                        <p style={{ color: "#f59e0b" }}>
                            ⚠️ Rapid activity or impossible travel detected
                        </p>
                    </div>
                )}

                {selectedUser.risk_reasons && (
                    <>
                        <h4>Risk Reasons:</h4>
                        <ul className="reasons-list">
                            {selectedUser.risk_reasons.map((reason, i) => (
                                <li key={i}>{reason}</li>
                            ))}
                        </ul>
                    </>
                )}

                <div style={{ marginTop: '20px' }}>
                    <button className="view-profile-btn">View Full Profile</button>
                </div>
            </div>
        </div>
    );
}

export default SidePanel;
