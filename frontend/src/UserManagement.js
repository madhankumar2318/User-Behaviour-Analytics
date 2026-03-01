import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './UserManagement.css';

function UserManagement({ currentUser }) {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newUser, setNewUser] = useState({
        username: '',
        email: '',
        password: '',
        role: 'Viewer',
        full_name: ''
    });

    useEffect(() => {
        fetchUsers();
    }, []);

    const fetchUsers = async () => {
        try {
            setLoading(true);
            const res = await axios.get('http://127.0.0.1:5000/users');
            setUsers(res.data);
            setError(null);
        } catch (err) {
            setError('Failed to fetch users');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateUser = async (e) => {
        e.preventDefault();
        try {
            await axios.post('http://127.0.0.1:5000/users', newUser);
            setShowCreateModal(false);
            setNewUser({
                username: '',
                email: '',
                password: '',
                role: 'Viewer',
                full_name: ''
            });
            fetchUsers();
        } catch (err) {
            alert(err.response?.data?.error || 'Failed to create user');
        }
    };

    const handleDeleteUser = async (userId) => {
        if (!window.confirm('Are you sure you want to delete this user?')) return;

        try {
            await axios.delete(`http://127.0.0.1:5000/users/${userId}`);
            fetchUsers();
        } catch (err) {
            alert('Failed to delete user');
        }
    };

    if (loading) return <div className="loading">Loading users...</div>;

    return (
        <div className="user-management">
            <div className="header-actions">
                <h2>👥 User Management</h2>
                <button className="create-btn" onClick={() => setShowCreateModal(true)}>
                    + New User
                </button>
            </div>

            {error && <div className="error-message">{error}</div>}

            <div className="users-grid">
                {users.map(user => (
                    <div key={user.id} className={`user-card ${user.is_active ? '' : 'inactive'}`}>
                        <div className="user-header">
                            <span className={`role-badge ${user.role.toLowerCase()}`}>{user.role}</span>
                            <div className="actions">
                                <button
                                    className="delete-btn"
                                    onClick={() => handleDeleteUser(user.id)}
                                    disabled={user.id === currentUser.id || user.username === 'admin'}
                                    title="Delete User"
                                >
                                    🗑️
                                </button>
                            </div>
                        </div>

                        <h3>{user.full_name || user.username}</h3>
                        <p className="email">{user.email}</p>

                        <div className="user-meta">
                            <span>👤 {user.username}</span>
                            <span>🕒 {new Date(user.created_at).toLocaleDateString()}</span>
                        </div>
                    </div>
                ))}
            </div>

            {showCreateModal && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <h3>Create New User</h3>
                        <form onSubmit={handleCreateUser}>
                            <div className="form-group">
                                <label>Username</label>
                                <input
                                    type="text"
                                    required
                                    value={newUser.username}
                                    onChange={e => setNewUser({ ...newUser, username: e.target.value })}
                                />
                            </div>

                            <div className="form-group">
                                <label>Full Name</label>
                                <input
                                    type="text"
                                    value={newUser.full_name}
                                    onChange={e => setNewUser({ ...newUser, full_name: e.target.value })}
                                />
                            </div>

                            <div className="form-group">
                                <label>Email</label>
                                <input
                                    type="email"
                                    required
                                    value={newUser.email}
                                    onChange={e => setNewUser({ ...newUser, email: e.target.value })}
                                />
                            </div>

                            <div className="form-group">
                                <label>Role</label>
                                <select
                                    value={newUser.role}
                                    onChange={e => setNewUser({ ...newUser, role: e.target.value })}
                                >
                                    <option value="Viewer">Viewer</option>
                                    <option value="Analyst">Analyst</option>
                                    <option value="Admin">Admin</option>
                                </select>
                            </div>

                            <div className="form-group">
                                <label>Password</label>
                                <input
                                    type="password"
                                    required
                                    value={newUser.password}
                                    onChange={e => setNewUser({ ...newUser, password: e.target.value })}
                                />
                            </div>

                            <div className="modal-actions">
                                <button type="button" onClick={() => setShowCreateModal(false)} className="cancel-btn">
                                    Cancel
                                </button>
                                <button type="submit" className="submit-btn">
                                    Create User
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

export default UserManagement;
