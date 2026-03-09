export const CITY_COORDINATES = {
    "New York": [40.7128, -74.0060],
    "London": [51.5074, -0.1278],
    "Tokyo": [35.6762, 139.6503],
    "Singapore": [1.3521, 103.8198],
    "Mumbai": [19.0760, 72.8777],
    "Berlin": [52.5200, 13.4050],
    "Paris": [48.8566, 2.3522],
    "San Francisco": [37.7749, -122.4194],
    "Sydney": [-33.8688, 151.2093],
    "Toronto": [43.6532, -79.3832],
    "Dubai": [25.2048, 55.2708],
    "Amsterdam": [52.3676, 4.9041],
    "Hong Kong": [22.3193, 114.1694],
    "Frankfurt": [50.1109, 8.6821],
    "Sao Paulo": [-23.5505, -46.6333],
    "Unknown": [0, 0]
};

export const getCoordinates = (locationName) => {
    // Basic fuzzy matching logic could go here if needed
    // Default to Null Island (0,0) if location is truly unknown
    return CITY_COORDINATES[locationName] || CITY_COORDINATES["Unknown"];
};
