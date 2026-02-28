# Project Requirements

This document outlines all the dependencies required to run the **User Behavior Analytics** platform. The project is split into a Python (Flask) backend and a Node.js (React) frontend.

---

## 🐍 Backend Requirements

The backend is built with Python 3.11+ and Flask. All dependencies are listed in `backend/requirements.txt` and can be installed via `pip install -r requirements.txt`.

### Core Framework & Networking
| Package | Version | Purpose |
|---------|---------|---------|
| `Flask` | 3.0.0 | Main web framework |
| `Flask-CORS` | 4.0.0 | Cross-Origin Resource Sharing |
| `Flask-SocketIO` | 5.3.6 | WebSocket integration for Flask |
| `python-socketio` | 5.11.0 | Core Socket.IO server |
| `python-engineio` | 4.9.0 | Core Engine.IO server |
| `eventlet` | 0.35.2 | Concurrent networking library |

### Machine Learning & Data Processing
| Package | Version | Purpose |
|---------|---------|---------|
| `scikit-learn` | 1.3.2 | ML models (Isolation Forest) |
| `numpy` | 1.24.3 | Numerical computation |
| `pandas` | 2.1.4 | Data manipulation & analysis |
| `joblib` | 1.3.2 | Model serialization |

### Authentication & Security
| Package | Version | Purpose |
|---------|---------|---------|
| `PyJWT` | 2.8.0 | JSON Web Token generation/validation |
| `bcrypt` | 4.1.2 | Password hashing |
| `python-dotenv` | 1.0.0 | Environment variable management |

### Validation & API
| Package | Version | Purpose |
|---------|---------|---------|
| `marshmallow` | 3.20.1 | Object serialization & validation |
| `email-validator` | 2.1.0 | Email validation |
| `flask-swagger-ui` | 4.11.1 | API documentation UI |
| `flasgger` | 0.9.7.1 | Swagger API specification generation |

### Testing & Production Server
| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | 7.4.3 | Testing framework |
| `pytest-flask` | 1.3.0 | Flask integration for pytest |
| `pytest-cov` | 4.1.0 | Test coverage reporting |
| `gunicorn` | 21.2.0 | Production WSGI HTTP server |
| `reportlab` | 4.0.7 | PDF generation (Phase 6 features) |
| `requests` | 2.31.0 | HTTP library |
| `schedule` | 1.2.0 | In-process scheduler |

---

## ⚛️ Frontend Requirements

The frontend is built with React 19 and Node.js 18+. All dependencies are listed in `frontend/package.json` and can be installed via `npm install`.

### Core React & UI
| Package | Version | Purpose |
|---------|---------|---------|
| `react` | ^19.2.4 | UI library |
| `react-dom` | ^19.2.4 | DOM render logic |
| `react-scripts` | 5.0.1 | Create React App configuration |

### Data Visualization & Networking
| Package | Version | Purpose |
|---------|---------|---------|
| `chart.js` | ^4.5.1 | Chart rendering engine |
| `react-chartjs-2` | ^5.3.1 | React wrapper for Chart.js |
| `axios` | ^1.13.4 | Promise-based HTTP client |
| `socket.io-client` | ^4.8.3 | WebSocket client for real-time updates |

### Testing & Utilities
| Package | Version | Purpose |
|---------|---------|---------|
| `@testing-library/react` | ^16.3.2 | React testing utilities |
| `@testing-library/dom` | ^10.4.1 | DOM testing utilities |
| `@testing-library/jest-dom` | ^6.9.1 | Custom jest matchers for DOM |
| `@testing-library/user-event` | ^13.5.0 | Simulate user interactions |
| `web-vitals` | ^2.1.4 | Performance metric tracking |

---

## 🐳 System Requirements

- **Python**: 3.11 or higher
- **Node.js**: 18.x or higher
- **Docker** (Optional): 24.0.0+ 
- **Docker Compose** (Optional): 2.20.0+
