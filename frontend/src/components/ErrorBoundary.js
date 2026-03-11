import React from 'react';

/**
 * ErrorBoundary — Catches unexpected rendering errors in the component tree
 * and shows a graceful fallback instead of crashing the whole page.
 *
 * Usage:
 *   <ErrorBoundary>
 *     <ComponentThatMightCrash />
 *   </ErrorBoundary>
 */
class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, info) {
        console.error('ErrorBoundary caught an error:', error, info);
    }

    handleReset = () => {
        this.setState({ hasError: false, error: null });
    };

    render() {
        if (this.state.hasError) {
            return (
                <div
                    style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: '2rem',
                        background: 'rgba(239,68,68,0.1)',
                        border: '1px solid rgba(239,68,68,0.4)',
                        borderRadius: '12px',
                        color: '#ef4444',
                        textAlign: 'center',
                        minHeight: '200px',
                        gap: '1rem',
                    }}
                >
                    <span style={{ fontSize: '2.5rem' }}>⚠️</span>
                    <div>
                        <strong style={{ display: 'block', fontSize: '1.1rem', marginBottom: '0.5rem' }}>
                            Something went wrong
                        </strong>
                        <code
                            style={{
                                fontSize: '0.75rem',
                                color: '#fca5a5',
                                wordBreak: 'break-word',
                                maxWidth: '500px',
                                display: 'block',
                            }}
                        >
                            {this.state.error?.message}
                        </code>
                    </div>
                    <button
                        onClick={this.handleReset}
                        style={{
                            marginTop: '0.5rem',
                            padding: '0.5rem 1.25rem',
                            background: '#ef4444',
                            color: 'white',
                            border: 'none',
                            borderRadius: '8px',
                            cursor: 'pointer',
                            fontWeight: 600,
                        }}
                    >
                        Try Again
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
