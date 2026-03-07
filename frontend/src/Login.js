import React, { useState } from 'react';
import axios from 'axios';
import './Login.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5000';

function Login({ onLogin }) {
    const [mode, setMode] = useState('signin'); // 'signin' | 'register'

    // Sign-in state
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [showPass, setShowPass] = useState(false);
    const [loginError, setLoginError] = useState('');
    const [loginLoading, setLoginLoading] = useState(false);

    // Register state
    const [reg, setReg] = useState({
        username: '', email: '', full_name: '', password: '', confirm: '', role: 'Viewer'
    });
    const [showRegPass, setShowRegPass] = useState(false);
    const [regError, setRegError] = useState('');
    const [regSuccess, setRegSuccess] = useState('');
    const [regLoading, setRegLoading] = useState(false);

    // ── Sign In ──────────────────────────────────────────────────────────────
    const handleLogin = async (e) => {
        e.preventDefault();
        setLoginError('');
        setLoginLoading(true);
        try {
            await onLogin(username, password);
        } catch (err) {
            setLoginError(err.response?.data?.error || 'Invalid credentials. Please try again.');
            setLoginLoading(false);
        }
    };

    // ── Register ─────────────────────────────────────────────────────────────
    const handleRegister = async (e) => {
        e.preventDefault();
        setRegError('');
        setRegSuccess('');

        if (reg.password !== reg.confirm) {
            setRegError('Passwords do not match.');
            return;
        }
        if (reg.password.length < 8) {
            setRegError('Password must be at least 8 characters.');
            return;
        }

        setRegLoading(true);
        try {
            // Registration requires Admin auth in the backend, so we call it here.
            // In a real setup you'd have a public /register endpoint.
            // For now we try with the default admin token from localStorage.
            const token = localStorage.getItem('token');
            await axios.post(
                `${API_URL}/users`,
                {
                    username: reg.username,
                    email: reg.email,
                    password: reg.password,
                    full_name: reg.full_name,
                    role: reg.role,
                },
                { headers: token ? { Authorization: token } : {} }
            );
            setRegSuccess(`✅ Account created for "${reg.username}"! You can now sign in.`);
            setReg({ username: '', email: '', full_name: '', password: '', confirm: '', role: 'Viewer' });
        } catch (err) {
            setRegError(
                err.response?.data?.error ||
                'Registration failed. An Admin must be logged in to create accounts.'
            );
        } finally {
            setRegLoading(false);
        }
    };

    const updateReg = (field) => (e) => setReg((p) => ({ ...p, [field]: e.target.value }));

    // ── Render ────────────────────────────────────────────────────────────────
    return (
        <div className="lp-root">
            {/* Animated background orbs */}
            <div className="lp-orb lp-orb-1" />
            <div className="lp-orb lp-orb-2" />
            <div className="lp-orb lp-orb-3" />

            <div className="lp-card">
                {/* === Left branding panel === */}
                <div className="lp-brand">
                    <div className="lp-brand-inner">
                        <div className="lp-logo">
                            <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                                <circle cx="24" cy="24" r="24" fill="url(#lg1)" opacity=".15" />
                                <path d="M14 34l10-20 10 20" stroke="url(#lg2)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                                <circle cx="24" cy="14" r="3" fill="#00f5ff" />
                                <defs>
                                    <linearGradient id="lg1" x1="0" y1="0" x2="48" y2="48">
                                        <stop stopColor="#00f5ff" /><stop offset="1" stopColor="#a78bfa" />
                                    </linearGradient>
                                    <linearGradient id="lg2" x1="14" y1="14" x2="34" y2="34">
                                        <stop stopColor="#00f5ff" /><stop offset="1" stopColor="#a78bfa" />
                                    </linearGradient>
                                </defs>
                            </svg>
                        </div>
                        <h1 className="lp-brand-title">User Behavior<br />Analytics</h1>
                        <p className="lp-brand-sub">AI-powered security monitoring platform</p>

                        <div className="lp-features">
                            {[
                                ['🤖', 'ML Anomaly Detection'],
                                ['⚡', 'Real-time Monitoring'],
                                ['🔐', 'Role-based Access Control'],
                                ['📊', 'Advanced Analytics'],
                            ].map(([icon, label]) => (
                                <div key={label} className="lp-feature-item">
                                    <span className="lp-feature-icon">{icon}</span>
                                    <span>{label}</span>
                                </div>
                            ))}
                        </div>

                        <div className="lp-demo-badge">
                            <span className="lp-badge-dot" />
                            <span>Live Demo &nbsp;·&nbsp; <code>admin / admin123</code></span>
                        </div>
                    </div>
                </div>

                {/* === Right form panel === */}
                <div className="lp-form-panel">
                    {/* Tabs */}
                    <div className="lp-tabs" role="tablist">
                        <button
                            role="tab"
                            aria-selected={mode === 'signin'}
                            className={`lp-tab ${mode === 'signin' ? 'lp-tab--active' : ''}`}
                            onClick={() => { setMode('signin'); setLoginError(''); }}
                        >
                            Sign In
                        </button>
                        <button
                            role="tab"
                            aria-selected={mode === 'register'}
                            className={`lp-tab ${mode === 'register' ? 'lp-tab--active' : ''}`}
                            onClick={() => { setMode('register'); setRegError(''); setRegSuccess(''); }}
                        >
                            New Account
                        </button>
                        <div className={`lp-tab-indicator ${mode === 'register' ? 'lp-tab-indicator--right' : ''}`} />
                    </div>

                    {/* ── Sign In form ── */}
                    {mode === 'signin' && (
                        <form className="lp-form" onSubmit={handleLogin} noValidate>
                            <div className="lp-field-group">
                                <label className="lp-label">Username</label>
                                <div className="lp-input-wrap">
                                    <span className="lp-input-icon">
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                                            <circle cx="12" cy="7" r="4" />
                                        </svg>
                                    </span>
                                    <input
                                        id="si-username"
                                        className="lp-input"
                                        type="text"
                                        placeholder="Enter your username"
                                        value={username}
                                        onChange={(e) => setUsername(e.target.value)}
                                        required
                                        autoFocus
                                        disabled={loginLoading}
                                    />
                                </div>
                            </div>

                            <div className="lp-field-group">
                                <label className="lp-label">Password</label>
                                <div className="lp-input-wrap">
                                    <span className="lp-input-icon">
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                                            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                                        </svg>
                                    </span>
                                    <input
                                        id="si-password"
                                        className="lp-input"
                                        type={showPass ? 'text' : 'password'}
                                        placeholder="Enter your password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                        disabled={loginLoading}
                                    />
                                    <button
                                        type="button"
                                        className="lp-eye-btn"
                                        onClick={() => setShowPass((p) => !p)}
                                        aria-label={showPass ? 'Hide password' : 'Show password'}
                                    >
                                        {showPass ? '🙈' : '👁️'}
                                    </button>
                                </div>
                            </div>

                            {loginError && (
                                <div className="lp-alert lp-alert--error" role="alert">
                                    <span>⚠️</span> {loginError}
                                </div>
                            )}

                            <button className="lp-submit-btn" type="submit" disabled={loginLoading}>
                                {loginLoading ? (
                                    <><span className="lp-spinner" /> Authenticating…</>
                                ) : (
                                    <>Sign In <span className="lp-arrow">→</span></>
                                )}
                            </button>

                            <p className="lp-hint">
                                🔒 Secured with JWT &amp; bcrypt encryption
                            </p>
                        </form>
                    )}

                    {/* ── Register form ── */}
                    {mode === 'register' && (
                        <form className="lp-form" onSubmit={handleRegister} noValidate>
                            <div className="lp-info-banner">
                                ℹ️ An <strong>Admin</strong> must be signed in (in another tab) to approve new accounts.
                            </div>

                            <div className="lp-row">
                                <div className="lp-field-group">
                                    <label className="lp-label">Full Name</label>
                                    <div className="lp-input-wrap">
                                        <span className="lp-input-icon">
                                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                                                <circle cx="12" cy="7" r="4" />
                                            </svg>
                                        </span>
                                        <input className="lp-input" type="text" placeholder="John Doe"
                                            value={reg.full_name} onChange={updateReg('full_name')} required />
                                    </div>
                                </div>
                                <div className="lp-field-group">
                                    <label className="lp-label">Username</label>
                                    <div className="lp-input-wrap">
                                        <span className="lp-input-icon">@</span>
                                        <input className="lp-input" type="text" placeholder="johndoe"
                                            value={reg.username} onChange={updateReg('username')} required />
                                    </div>
                                </div>
                            </div>

                            <div className="lp-field-group">
                                <label className="lp-label">Email Address</label>
                                <div className="lp-input-wrap">
                                    <span className="lp-input-icon">
                                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                                            <polyline points="22,6 12,13 2,6" />
                                        </svg>
                                    </span>
                                    <input className="lp-input" type="email" placeholder="john@company.com"
                                        value={reg.email} onChange={updateReg('email')} required />
                                </div>
                            </div>

                            <div className="lp-row">
                                <div className="lp-field-group">
                                    <label className="lp-label">Password</label>
                                    <div className="lp-input-wrap">
                                        <span className="lp-input-icon">🔑</span>
                                        <input className="lp-input" type={showRegPass ? 'text' : 'password'}
                                            placeholder="Min 8 chars" value={reg.password} onChange={updateReg('password')} required />
                                        <button type="button" className="lp-eye-btn"
                                            onClick={() => setShowRegPass((p) => !p)}>
                                            {showRegPass ? '🙈' : '👁️'}
                                        </button>
                                    </div>
                                </div>
                                <div className="lp-field-group">
                                    <label className="lp-label">Confirm</label>
                                    <div className="lp-input-wrap">
                                        <span className="lp-input-icon">✔</span>
                                        <input className="lp-input" type="password" placeholder="Repeat password"
                                            value={reg.confirm} onChange={updateReg('confirm')} required />
                                    </div>
                                </div>
                            </div>

                            <div className="lp-field-group">
                                <label className="lp-label">Role</label>
                                <div className="lp-input-wrap">
                                    <span className="lp-input-icon">🏷</span>
                                    <select className="lp-input lp-select" value={reg.role} onChange={updateReg('role')}>
                                        <option value="Viewer">Viewer — read-only access</option>
                                        <option value="Analyst">Analyst — log &amp; simulate activity</option>
                                        <option value="Admin">Admin — full access</option>
                                    </select>
                                </div>
                            </div>

                            {regError && (
                                <div className="lp-alert lp-alert--error" role="alert">
                                    <span>⚠️</span> {regError}
                                </div>
                            )}
                            {regSuccess && (
                                <div className="lp-alert lp-alert--success" role="alert">
                                    {regSuccess}
                                </div>
                            )}

                            <button className="lp-submit-btn lp-submit-btn--register" type="submit" disabled={regLoading}>
                                {regLoading ? (
                                    <><span className="lp-spinner" /> Creating account…</>
                                ) : (
                                    <>Create Account <span className="lp-arrow">→</span></>
                                )}
                            </button>
                        </form>
                    )}
                </div>
            </div>
        </div>
    );
}

export default Login;
