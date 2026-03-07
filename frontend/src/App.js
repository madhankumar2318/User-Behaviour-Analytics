import React, { useEffect, useState, useRef } from "react";
import axios from "axios";
import { io } from "socket.io-client";
import "./App.css";
import Login from "./Login";
import UserManagement from "./UserManagement";
import ThemeToggle from "./ThemeToggle";
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  BarElement,
  ArcElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend
} from "chart.js";
import { Line, Pie, Bar } from "react-chartjs-2";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:5000";


ChartJS.register(
  LineElement,
  PointElement,
  BarElement,
  ArcElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend
);



function App() {
  // Socket ref — initialized in useEffect to avoid calling io() during render
  const socketRef = useRef(null);
  // Auth State
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [authLoading, setAuthLoading] = useState(true);
  const [viewMode, setViewMode] = useState('dashboard'); // dashboard, users

  // App State
  const [logs, setLogs] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterStatus, setFilterStatus] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [toast, setToast] = useState(null);
  const [simulating, setSimulating] = useState(false);
  const [activeChartTab, setActiveChartTab] = useState("timeline");
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        try {
          // Set default header
          axios.defaults.headers.common['Authorization'] = storedToken;

          // Verify token and get user info
          const res = await axios.get(`${API_URL}/auth/me`);
          setCurrentUser(res.data);
          setIsAuthenticated(true);
          setToken(storedToken);
        } catch (err) {
          console.error("Auth check failed:", err);
          logout();
        }
      }
      setAuthLoading(false);
    };

    checkAuth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Keep a ref to latest logs so socket handler can use it without being a dependency
  const logsRef = useRef([]);
  useEffect(() => {
    logsRef.current = logs;
  }, [logs]);

  // Initialize socket connection once on mount
  useEffect(() => {
    socketRef.current = io(API_URL);
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;

    fetchLogs();

    const handleNewActivity = (newLog) => {
      setLogs((prev) => [...prev, newLog]);

      if (newLog.status === "HIGH_RISK" || newLog.status === "LOCKED") {
        showToast(`🚨 ${newLog.status} Alert: ${newLog.user_id}`, newLog.status);
      }
    };

    const socket = socketRef.current;
    if (socket) {
      socket.on("new_activity", handleNewActivity);
    }

    return () => {
      if (socket) {
        socket.off("new_activity", handleNewActivity);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  const login = async (username, password) => {
    try {
      const res = await axios.post(`${API_URL}/auth/login`, {
        username,
        password
      });

      const { token, user } = res.data;

      localStorage.setItem('token', token);
      setToken(token);
      setCurrentUser(user);
      setIsAuthenticated(true);
      axios.defaults.headers.common['Authorization'] = token;

      return true;
    } catch (err) {
      throw err;
    }
  };

  const logout = async () => {
    try {
      if (token) {
        await axios.post(`${API_URL}/auth/logout`);
      }
    } catch (err) {
      console.error("Logout error:", err);
    } finally {
      localStorage.removeItem('token');
      setToken(null);
      setCurrentUser(null);
      setIsAuthenticated(false);
      delete axios.defaults.headers.common['Authorization'];
      setLogs([]);
      setSelectedUser(null);
      setViewMode('dashboard');
    }
  };

  const fetchLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await axios.get(`${API_URL}/get-logs`);
      setLogs(res.data);
    } catch (err) {
      if (err.response && err.response.status === 401) {
        logout();
      } else {
        setError("Failed to fetch logs. Please ensure the backend is running.");
        console.error(err);
      }
    } finally {
      setLoading(false);
    }
  };

  const simulateActivity = async () => {
    try {
      setSimulating(true);
      const res = await axios.post(`${API_URL}/simulate-activity`);
      showToast(`✅ Activity simulated for ${res.data.user_id}`, "SUCCESS");
    } catch (err) {
      if (err.response && (err.response.status === 401 || err.response.status === 403)) {
        showToast("❌ Permission denied", "ERROR");
      } else {
        showToast("❌ Failed to simulate activity", "ERROR");
        console.error(err);
      }
    } finally {
      setSimulating(false);
    }
  };

  const showToast = (message, type) => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  const exportToCSV = () => {
    const headers = ['User ID', 'Login Time', 'Location', 'Downloads', 'Failed Attempts', 'Risk Score', 'Status'];

    const csvContent = [
      headers.join(','),
      ...filteredLogs.map(log =>
        [log.user_id, log.login_time, log.location, log.downloads, log.failed_attempts, log.risk_score, log.status].join(',')
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', 'security_logs.csv');
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

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

  // Sort handler
  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  // Filter and sort logs
  const filteredLogs = logs.filter((log) => {
    const matchesStatus = filterStatus === "ALL" || log.status === filterStatus;
    const matchesSearch =
      log.user_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.location.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  }).sort((a, b) => {
    if (!sortConfig.key) return 0;

    let aVal = a[sortConfig.key];
    let bVal = b[sortConfig.key];

    // Handle numeric values
    if (sortConfig.key === 'downloads' || sortConfig.key === 'failed_attempts' || sortConfig.key === 'risk_score') {
      aVal = Number(aVal) || 0;
      bVal = Number(bVal) || 0;
    }

    if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
    return 0;
  });

  // Data for Charts
  const riskDistribution = {
    labels: ['Active', 'High Risk', 'Locked'],
    datasets: [{
      data: [
        logs.filter(l => l.status === 'ACTIVE').length,
        logs.filter(l => l.status === 'HIGH_RISK').length,
        logs.filter(l => l.status === 'LOCKED').length
      ],
      backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
      borderColor: ['#10b981', '#f59e0b', '#ef4444'],
      borderWidth: 1
    }]
  };

  const timelineData = {
    labels: logs.map(l => l.login_time),
    datasets: [
      {
        label: 'Risk Score',
        data: logs.map(l => l.risk_score),
        borderColor: '#a78bfa',
        tension: 0.4,
        fill: true,
        backgroundColor: 'rgba(167, 139, 250, 0.1)'
      },
      {
        label: 'Downloads',
        data: logs.map(l => l.downloads),
        borderColor: '#00f5ff',
        tension: 0.4
      }
    ]
  };

  const locationData = {
    labels: [...new Set(logs.map(l => l.location))].slice(0, 10),
    datasets: [{
      label: 'Activity Count',
      data: [...new Set(logs.map(l => l.location))].slice(0, 10).map(
        loc => logs.filter(l => l.location === loc).length
      ),
      backgroundColor: 'rgba(0, 245, 255, 0.6)'
    }]
  };

  // Heatmap data — 24-hour activity grid derived from real log data
  const generateHeatmapData = () => {
    const hours = Array.from({ length: 24 }, (_, i) => i);
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    // Initialize grid
    const grid = days.map(() => hours.map(() => 0));

    // Process logs: try to extract real weekday from login_time.
    // If login_time is a full ISO datetime string (e.g. "2025-01-15T09:30:00"),
    // use getDay(); otherwise fall back to a stable index derived from the log id.
    logs.forEach((log, idx) => {
      const timeStr = log.login_time || '';
      let hour = 0;
      let dayIndex = idx % 7; // stable deterministic fallback

      // Try full ISO parsing first
      const parsed = new Date(timeStr);
      if (!isNaN(parsed.getTime()) && timeStr.includes('-')) {
        hour = parsed.getHours();
        // getDay() returns 0=Sunday; shift so 0=Monday
        dayIndex = (parsed.getDay() + 6) % 7;
      } else {
        // HH:MM only — extract hour, keep deterministic day fallback
        const parts = timeStr.split(':');
        hour = parts.length > 0 ? parseInt(parts[0], 10) : 0;
        if (isNaN(hour) || hour < 0 || hour > 23) hour = 0;
      }

      if (hour >= 0 && hour < 24) {
        grid[dayIndex][hour]++;
      }
    });

    return { hours, days, grid };
  };

  const heatmapData = generateHeatmapData();

  if (authLoading) {
    return <div className="loading-screen"><div className="spinner"></div></div>;
  }

  if (!isAuthenticated) {
    return <Login onLogin={login} />;
  }

  return (
    <div className="container">
      <ThemeToggle />
      {toast && (
        <div className={`toast toast-${toast.type.toLowerCase()}`}>
          {toast.message}
        </div>
      )}

      {/* Header with User Info */}
      <header className="app-header">
        <h1>🔍 User Behavior Analytics</h1>

        <div className="user-controls">
          {/* Navigation Controls for Admin */}
          {currentUser?.role === 'Admin' && (
            <div className="nav-buttons">
              <button
                className={`nav-btn ${viewMode === 'dashboard' ? 'active' : ''}`}
                onClick={() => setViewMode('dashboard')}
              >
                📊 Dashboard
              </button>
              <button
                className={`nav-btn ${viewMode === 'users' ? 'active' : ''}`}
                onClick={() => setViewMode('users')}
              >
                👥 Users
              </button>
            </div>
          )}

          <div className="user-info">
            <span className="user-name">{currentUser?.full_name || currentUser?.username}</span>
            <span className="user-role badge">{currentUser?.role}</span>
          </div>
          <button className="logout-btn" onClick={logout}>
            Sign Out
          </button>
        </div>
      </header>

      {/* Main Content Switcher */}
      {viewMode === 'users' && currentUser?.role === 'Admin' ? (
        <UserManagement currentUser={currentUser} />
      ) : (
        /* Dashboard Content */
        <div className="dashboard-grid">

          {/* ── Summary Cards ── */}
          <div className="summary-cards">
            <div className="stat-card stat-card--total">
              <div className="stat-card__icon">📋</div>
              <div className="stat-card__body">
                <span className="stat-card__label">Total Logs</span>
                <span className="stat-card__value">{logs.length}</span>
                <span className="stat-card__sub">all recorded sessions</span>
              </div>
              <div className="stat-card__glow" />
            </div>

            <div className="stat-card stat-card--active">
              <div className="stat-card__icon">✅</div>
              <div className="stat-card__body">
                <span className="stat-card__label">Active</span>
                <span className="stat-card__value">
                  {logs.filter(l => l.status === 'ACTIVE').length}
                </span>
                <span className="stat-card__sub">normal sessions</span>
              </div>
              <div className="stat-card__glow" />
            </div>

            <div className="stat-card stat-card--highrisk">
              <div className="stat-card__icon">⚠️</div>
              <div className="stat-card__body">
                <span className="stat-card__label">High Risk</span>
                <span className="stat-card__value">
                  {logs.filter(l => l.status === 'HIGH_RISK').length}
                </span>
                <span className="stat-card__sub">flagged sessions</span>
              </div>
              <div className="stat-card__glow" />
            </div>

            <div className="stat-card stat-card--locked">
              <div className="stat-card__icon">🔒</div>
              <div className="stat-card__body">
                <span className="stat-card__label">Locked</span>
                <span className="stat-card__value">
                  {logs.filter(l => l.status === 'LOCKED').length}
                </span>
                <span className="stat-card__sub">blocked accounts</span>
              </div>
              <div className="stat-card__glow" />
            </div>

            <div className="stat-card stat-card--avgrisk">
              <div className="stat-card__icon">🤖</div>
              <div className="stat-card__body">
                <span className="stat-card__label">Avg Risk Score</span>
                <span className="stat-card__value">
                  {logs.length > 0
                    ? (logs.reduce((s, l) => s + (Number(l.risk_score) || 0), 0) / logs.length).toFixed(1)
                    : '—'}
                </span>
                <span className="stat-card__sub">ML anomaly index</span>
              </div>
              <div className="stat-card__glow" />
            </div>
          </div>

          {/* Charts Section */}
          <div className="chart-section">
            <div className="chart-controls">
              <button
                className={activeChartTab === 'timeline' ? 'active' : ''}
                onClick={() => setActiveChartTab('timeline')}
              >Timeline</button>
              <button
                className={activeChartTab === 'distribution' ? 'active' : ''}
                onClick={() => setActiveChartTab('distribution')}
              >Risk Distribution</button>
              <button
                className={activeChartTab === 'locations' ? 'active' : ''}
                onClick={() => setActiveChartTab('locations')}
              >Locations</button>
              <button
                className={activeChartTab === 'heatmap' ? 'active' : ''}
                onClick={() => setActiveChartTab('heatmap')}
              >24h Heatmap</button>
            </div>

            <div className="chart-container">
              {activeChartTab === 'timeline' && <Line data={timelineData} options={{ responsive: true, plugins: { legend: { position: 'top' } } }} />}
              {activeChartTab === 'distribution' && <div style={{ maxWidth: '400px', margin: '0 auto' }}><Pie data={riskDistribution} /></div>}
              {activeChartTab === 'locations' && <Bar data={locationData} />}
              {activeChartTab === 'heatmap' && (
                <div className="heatmap-container">
                  <div className="heatmap-grid">
                    <div className="heatmap-y-labels">
                      {heatmapData.days.map((day, i) => (
                        <div key={i} className="heatmap-label">{day}</div>
                      ))}
                    </div>
                    <div className="heatmap-cells">
                      {heatmapData.grid.map((row, dayIdx) => (
                        <div key={dayIdx} className="heatmap-row">
                          {row.map((count, hourIdx) => {
                            const maxCount = Math.max(...heatmapData.grid.flat());
                            const intensity = maxCount > 0 ? count / maxCount : 0;
                            const color = `rgba(167, 139, 250, ${intensity})`;
                            return (
                              <div
                                key={hourIdx}
                                className="heatmap-cell"
                                style={{ backgroundColor: color }}
                                title={`${heatmapData.days[dayIdx]} ${hourIdx}:00 - ${count} activities`}
                              >
                                {count > 0 ? count : ''}
                              </div>
                            );
                          })}
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="heatmap-x-labels">
                    {heatmapData.hours.filter((_, i) => i % 2 === 0).map((hour, i) => (
                      <div key={i} className="heatmap-label">{hour}h</div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Controls Section */}
          <div className="controls-section">
            <div className="filter-controls">
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="filter-select"
              >
                <option value="ALL">All Statuses</option>
                <option value="ACTIVE">Active</option>
                <option value="HIGH_RISK">High Risk</option>
                <option value="LOCKED">Locked</option>
              </select>

              <input
                type="text"
                placeholder="Search users or locations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
            </div>

            <div className="action-buttons">
              <button className="export-btn" onClick={exportToCSV}>
                📥 Export CSV
              </button>

              {(currentUser?.role === 'Admin' || currentUser?.role === 'Analyst') && (
                <button
                  className="simulate-btn"
                  onClick={simulateActivity}
                  disabled={simulating}
                >
                  {simulating ? '🎲 Simulating...' : '🎲 Simulate Activity'}
                </button>
              )}
            </div>
          </div>

          {/* Main Content Area */}
          <div className="main-content">
            {/* Logs Table */}
            <table className="logs-table">
              <thead>
                <tr>
                  <th onClick={() => handleSort('user_id')} style={{ cursor: 'pointer' }}>
                    User ID {sortConfig.key === 'user_id' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                  </th>
                  <th onClick={() => handleSort('login_time')} style={{ cursor: 'pointer' }}>
                    Time {sortConfig.key === 'login_time' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                  </th>
                  <th onClick={() => handleSort('location')} style={{ cursor: 'pointer' }}>
                    Location {sortConfig.key === 'location' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                  </th>
                  <th onClick={() => handleSort('ip_address')} style={{ cursor: 'pointer' }}>
                    IP {sortConfig.key === 'ip_address' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                  </th>
                  <th onClick={() => handleSort('downloads')} style={{ cursor: 'pointer' }}>
                    Downloads {sortConfig.key === 'downloads' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                  </th>
                  <th onClick={() => handleSort('failed_attempts')} style={{ cursor: 'pointer' }}>
                    Failed {sortConfig.key === 'failed_attempts' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                  </th>
                  <th onClick={() => handleSort('status')} style={{ cursor: 'pointer' }}>
                    Status {sortConfig.key === 'status' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan="6" style={{ textAlign: "center" }}>Loading logs...</td></tr>
                ) : error ? (
                  <tr><td colSpan="6" style={{ textAlign: "center", color: "#ef4444" }}>{error}</td></tr>
                ) : filteredLogs.map((log, index) => (
                  <tr
                    key={index}
                    onClick={() => setSelectedUser(log)}
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

            {filteredLogs.length === 0 && !loading && (
              <div className="no-results">
                <p>No logs match your current filters</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Side Panel (kept outside of switcher to show on top if needed, though mostly relevant for dashboard) */}
      {selectedUser && viewMode === 'dashboard' && (
        <div className="side-panel">
          <div className="panel-content">
            <div className="panel-header">
              <h2>User Behavioral Profile</h2>
              <button className="close-btn" onClick={() => setSelectedUser(null)}>×</button>
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
      )}
    </div>
  );
}

export default App;