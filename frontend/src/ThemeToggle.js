import React, { useState, useEffect } from 'react';
import './ThemeToggle.css';

const ThemeToggle = () => {
    const [theme, setTheme] = useState('dark');

    useEffect(() => {
        // Load theme from localStorage
        const savedTheme = localStorage.getItem('theme') || 'dark';
        setTheme(savedTheme);
        document.documentElement.setAttribute('data-theme', savedTheme);
    }, []);

    const toggleTheme = () => {
        const newTheme = theme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    };

    return (
        <div className="theme-toggle" onClick={toggleTheme}>
            <span className="theme-toggle-icon">
                {theme === 'dark' ? '🌙' : '☀️'}
            </span>
            <span className="theme-toggle-text">
                {theme === 'dark' ? 'Dark' : 'Light'}
            </span>
        </div>
    );
};

export default ThemeToggle;
