import React, { useState, useEffect, useRef, useCallback } from 'react';

/**
 * AlertsPanel
 * -----------
 * Bell icon with animated unread badge + dropdown alert list.
 *
 * Props:
 *   alerts       — array of alert objects from parent
 *   unreadCount  — number of unseen alerts
 *   onDismiss    — fn(index) to remove one alert
 *   onClearAll   — fn() to clear all alerts
 *   onOpen       — fn() called when panel opens (resets unread count in parent)
 */
function AlertsPanel({ alerts, unreadCount, onDismiss, onClearAll, onOpen }) {
    const [isOpen, setIsOpen] = useState(false);
    const panelRef = useRef(null);

    // Close panel when clicking outside
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (panelRef.current && !panelRef.current.contains(e.target)) {
                setIsOpen(false);
            }
        };
        if (isOpen) document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [isOpen]);

    const handleToggle = useCallback(() => {
        setIsOpen(prev => {
            const next = !prev;
            if (next) onOpen(); // mark as read when opened
            return next;
        });
    }, [onOpen]);

    const getStatusColor = (status) => {
        if (status === 'LOCKED') return '#ef4444';
        if (status === 'HIGH_RISK') return '#f59e0b';
        return '#10b981';
    };

    const getStatusIcon = (status) => {
        if (status === 'LOCKED') return '🔒';
        if (status === 'HIGH_RISK') return '⚠️';
        return '✅';
    };

    const formatTime = (timeStr) => {
        if (!timeStr) return '—';
        return timeStr;
    };

    return (
        <div className="alerts-wrapper" ref={panelRef}>
            {/* ── Bell Button ── */}
            <button
                className={`alerts-btn ${isOpen ? 'alerts-btn--open' : ''}`}
                onClick={handleToggle}
                title="Security Alerts"
                aria-label={`Security Alerts — ${unreadCount} unread`}
            >
                🔔
                {unreadCount > 0 && (
                    <span className={`alerts-badge ${unreadCount > 0 ? 'alerts-badge--pulse' : ''}`}>
                        {unreadCount > 99 ? '99+' : unreadCount}
                    </span>
                )}
            </button>

            {/* ── Dropdown Panel ── */}
            {isOpen && (
                <div className="alerts-dropdown">
                    {/* Header */}
                    <div className="alerts-header">
                        <div className="alerts-header__left">
                            <span className="alerts-header__icon">🚨</span>
                            <span className="alerts-header__title">Security Alerts</span>
                            {alerts.length > 0 && (
                                <span className="alerts-header__count">{alerts.length}</span>
                            )}
                        </div>
                        {alerts.length > 0 && (
                            <button className="alerts-clear-btn" onClick={onClearAll}>
                                Clear All
                            </button>
                        )}
                    </div>

                    {/* Alert List */}
                    <div className="alerts-list">
                        {alerts.length === 0 ? (
                            <div className="alerts-empty">
                                <span className="alerts-empty__icon">✅</span>
                                <p>No active alerts</p>
                                <small>All clear — no high-risk events detected</small>
                            </div>
                        ) : (
                            alerts.map((alert, index) => (
                                <div
                                    key={`alert-${index}-${alert.id || index}`}
                                    className={`alert-item alert-item--${(alert.status || '').toLowerCase()}`}
                                    style={{ borderLeftColor: getStatusColor(alert.status) }}
                                >
                                    <div className="alert-item__header">
                                        <div className="alert-item__identity">
                                            <span className="alert-item__icon">
                                                {getStatusIcon(alert.status)}
                                            </span>
                                            <strong className="alert-item__user">
                                                {alert.user_id}
                                            </strong>
                                        </div>
                                        <button
                                            className="alert-item__dismiss"
                                            onClick={() => onDismiss(index)}
                                            title="Dismiss alert"
                                        >
                                            ✕
                                        </button>
                                    </div>

                                    <div className="alert-item__body">
                                        <div className="alert-item__meta">
                                            <span
                                                className="alert-item__badge"
                                                style={{
                                                    background: getStatusColor(alert.status),
                                                    color: 'white',
                                                }}
                                            >
                                                {alert.status}
                                            </span>
                                            <span className="alert-item__score">
                                                🎯 {typeof alert.risk_score === 'number'
                                                    ? alert.risk_score.toFixed(1)
                                                    : alert.risk_score ?? '—'}
                                            </span>
                                        </div>
                                        <div className="alert-item__details">
                                            <span>📍 {alert.location || '—'}</span>
                                            <span>🕐 {formatTime(alert.login_time)}</span>
                                        </div>
                                        {alert.ip_address && (
                                            <div className="alert-item__ip">
                                                🌐 {alert.ip_address}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>

                    {/* Footer */}
                    {alerts.length > 0 && (
                        <div className="alerts-footer">
                            Showing {alerts.length} alert{alerts.length !== 1 ? 's' : ''}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default AlertsPanel;
