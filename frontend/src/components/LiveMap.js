import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { getCoordinates } from '../utils/locationCoordinates';

// Fix Leaflet's default icon path issues in React
delete L.Icon.Default.prototype._getIconUrl;

// Custom Icons for different risk levels
const createIcon = (color) => {
    return new L.DivIcon({
        className: 'custom-leaflet-icon',
        html: `<div style="background-color: ${color}; width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px ${color}"></div>`,
        iconSize: [20, 20],
        iconAnchor: [10, 10],
    });
};

const icons = {
    ACTIVE: createIcon('#10b981'),      // Green
    HIGH_RISK: createIcon('#f59e0b'),   // Orange
    LOCKED: createIcon('#ef4444')       // Red
};

// Component to dynamically fit bounds if needed, or simply render map
function LiveMap({ logs }) {
    // We want to render the latest logs on top, so we reverse a copy of the array for rendering
    // or just rely on Leaflet's z-index.
    const recentLogs = [...logs].slice(-500); // Limit to last 500 for performance

    return (
        <div style={{ height: '500px', width: '100%', borderRadius: '12px', overflow: 'hidden' }}>
            <MapContainer
                center={[20, 0]}
                zoom={2}
                style={{ height: '100%', width: '100%' }}
                scrollWheelZoom={true}
                worldCopyJump={true}
            >
                {/* CartoDB Dark Matter tile layer matches the dark theme beautifully */}
                <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                />

                {recentLogs.map((log, index) => {
                    const coords = getCoordinates(log.location);

                    // Jitter coordinates slightly so markers at the exact same city don't completely overlap
                    const jitterLat = coords[0] + (Math.random() - 0.5) * 0.1;
                    const jitterLng = coords[1] + (Math.random() - 0.5) * 0.1;

                    return (
                        <Marker
                            key={`map-marker-${index}-${log.id || index}`}
                            position={[jitterLat, jitterLng]}
                            icon={icons[log.status] || icons.ACTIVE}
                        >
                            <Popup className="dark-popup">
                                <div>
                                    <strong style={{ color: '#00f5ff' }}>{log.user_id}</strong><br />
                                    <span style={{ color: '#a78bfa' }}>{log.location}</span><br />
                                    Status: {log.status}<br />
                                    Risk Score: {log.risk_score}<br />
                                    Time: {log.login_time}
                                </div>
                            </Popup>
                        </Marker>
                    );
                })}
            </MapContainer>
        </div>
    );
}

export default LiveMap;
