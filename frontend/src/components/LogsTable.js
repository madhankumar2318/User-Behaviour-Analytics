import React from 'react';

function LogsTable({ logs, loading, error, sortConfig, onSort, onRowClick }) {
    const getStatusBadge = (status) => {
        let color = "#10b981"; // Active
        if (status === "LOCKED") color = "#ef4444";
        if (status === "HIGH_RISK") color = "#f59e0b";

        return (
            <span style={{
                padding: "4px 8px",
                borderRadius: "12px",
                backgroundColor: `${color}20`,
                color: color,
                fontWeight: "bold",
                fontSize: "0.85rem",
                border: `1px solid ${color}40`
            }}>
                {status}
            </span>
        );
    };

    return (
        <div className="main-content">
            <table className="logs-table">
                <thead>
                    <tr>
                        <th onClick={() => onSort('user_id')} style={{ cursor: 'pointer' }}>
                            User ID {sortConfig.key === 'user_id' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                        </th>
                        <th onClick={() => onSort('login_time')} style={{ cursor: 'pointer' }}>
                            Time {sortConfig.key === 'login_time' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                        </th>
                        <th onClick={() => onSort('location')} style={{ cursor: 'pointer' }}>
                            Location {sortConfig.key === 'location' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                        </th>
                        <th onClick={() => onSort('ip_address')} style={{ cursor: 'pointer' }}>
                            IP {sortConfig.key === 'ip_address' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                        </th>
                        <th onClick={() => onSort('downloads')} style={{ cursor: 'pointer' }}>
                            Downloads {sortConfig.key === 'downloads' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                        </th>
                        <th onClick={() => onSort('failed_attempts')} style={{ cursor: 'pointer' }}>
                            Failed {sortConfig.key === 'failed_attempts' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                        </th>
                        <th onClick={() => onSort('status')} style={{ cursor: 'pointer' }}>
                            Status {sortConfig.key === 'status' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {loading ? (
                        <tr><td colSpan="7" style={{ textAlign: "center" }}>Loading logs...</td></tr>
                    ) : error ? (
                        <tr><td colSpan="7" style={{ textAlign: "center", color: "#ef4444" }}>{error}</td></tr>
                    ) : logs.map((log, index) => (
                        <tr
                            key={index}
                            onClick={() => onRowClick(log)}
                            className={
                                log.status === "LOCKED"
                                    ? "row-locked"
                                    : log.status === "HIGH_RISK"
                                        ? "row-high"
                                        : ""
                            }
                        >
                            <td>{log.user_id}</td>
                            <td>{log.login_time}</td>
                            <td>{log.location}</td>
                            <td style={{ fontSize: '0.85rem', color: '#94a3b8' }}>{log.ip_address || 'N/A'}</td>
                            <td>{log.downloads}</td>
                            <td>{log.failed_attempts}</td>
                            <td>{getStatusBadge(log.status)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>

            {logs.length === 0 && !loading && (
                <div className="no-results">
                    <p>No logs match your current filters</p>
                </div>
            )}
        </div>
    );
}

export default LogsTable;
