"""
Velocity Checker
Detects rapid successive logins and impossible travel scenarios
"""

from datetime import datetime
import math


class VelocityChecker:
    def __init__(self):
        # Approximate distances between major cities (km)
        self.city_distances = {
            ('New York', 'London'): 5585,
            ('New York', 'Tokyo'): 10850,
            ('New York', 'Singapore'): 15345,
            ('New York', 'Mumbai'): 12550,
            ('New York', 'Berlin'): 6385,
            ('New York', 'Paris'): 5837,
            ('New York', 'Sydney'): 16014,
            ('New York', 'Dubai'): 11020,
            ('New York', 'Hong Kong'): 12970,
            ('London', 'Tokyo'): 9560,
            ('London', 'Singapore'): 10870,
            ('London', 'Mumbai'): 7200,
            ('London', 'Berlin'): 930,
            ('London', 'Paris'): 344,
            ('London', 'Sydney'): 17015,
            ('London', 'Dubai'): 5480,
            ('London', 'Hong Kong'): 9650,
            ('Tokyo', 'Singapore'): 5320,
            ('Tokyo', 'Mumbai'): 6700,
            ('Tokyo', 'Berlin'): 8940,
            ('Tokyo', 'Paris'): 9715,
            ('Tokyo', 'Sydney'): 7820,
            ('Tokyo', 'Dubai'): 7960,
            ('Tokyo', 'Hong Kong'): 2900,
            ('Singapore', 'Mumbai'): 4130,
            ('Singapore', 'Berlin'): 10310,
            ('Singapore', 'Paris'): 10750,
            ('Singapore', 'Sydney'): 6310,
            ('Singapore', 'Dubai'): 6010,
            ('Singapore', 'Hong Kong'): 2590,
            ('Mumbai', 'Berlin'): 6130,
            ('Mumbai', 'Paris'): 6650,
            ('Mumbai', 'Sydney'): 10360,
            ('Mumbai', 'Dubai'): 1940,
            ('Mumbai', 'Hong Kong'): 4390,
            ('Berlin', 'Paris'): 880,
            ('Berlin', 'Sydney'): 16090,
            ('Berlin', 'Dubai'): 4630,
            ('Berlin', 'Hong Kong'): 8970,
            ('Paris', 'Sydney'): 16960,
            ('Paris', 'Dubai'): 5250,
            ('Paris', 'Hong Kong'): 9620,
            ('Sydney', 'Dubai'): 12020,
            ('Sydney', 'Hong Kong'): 7375,
            ('Dubai', 'Hong Kong'): 5950,
        }
        
        # Maximum realistic travel speed (km/h) - commercial airplane
        self.max_speed = 900
    
    def parse_time(self, time_str):
        """Parse time string to datetime"""
        try:
            # Assuming format HH:MM
            parts = time_str.split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            
            # Use today's date for comparison
            now = datetime.now()
            return datetime(now.year, now.month, now.day, hour, minute)
        except:
            return datetime.now()
    
    def time_diff_minutes(self, time1_str, time2_str):
        """Calculate time difference in minutes"""
        try:
            t1 = self.parse_time(time1_str)
            t2 = self.parse_time(time2_str)
            diff = abs((t2 - t1).total_seconds() / 60)
            return diff
        except:
            return 999999  # Large number if parsing fails
    
    def time_diff_hours(self, time1_str, time2_str):
        """Calculate time difference in hours"""
        return self.time_diff_minutes(time1_str, time2_str) / 60
    
    def get_distance(self, location1, location2):
        """Get distance between two locations in km"""
        if location1 == location2:
            return 0
        
        # Try both orderings
        key1 = (location1, location2)
        key2 = (location2, location1)
        
        if key1 in self.city_distances:
            return self.city_distances[key1]
        elif key2 in self.city_distances:
            return self.city_distances[key2]
        else:
            # Unknown distance, assume far apart
            return 5000
    
    def check_rapid_logins(self, user_id, current_time, history, threshold_minutes=5, threshold_count=3):
        """
        Detect multiple logins within a short time window
        
        Args:
            user_id: User identifier
            current_time: Current login time string
            history: List of previous login logs
            threshold_minutes: Time window to check
            threshold_count: Number of logins to trigger alert
        
        Returns:
            (is_rapid, message)
        """
        if not history or len(history) == 0:
            return False, None
        
        recent_logins = []
        for log in history:
            time_diff = self.time_diff_minutes(log.get('login_time', '00:00'), current_time)
            if time_diff <= threshold_minutes:
                recent_logins.append(log)
        
        if len(recent_logins) >= threshold_count:
            return True, f"{len(recent_logins)} logins within {threshold_minutes} minutes"
        
        return False, None
    
    def check_impossible_travel(self, current_log, last_log):
        """
        Check if travel between locations is physically possible
        
        Args:
            current_log: Current login log
            last_log: Previous login log
        
        Returns:
            (is_impossible, message)
        """
        if not last_log:
            return False, None
        
        current_location = current_log.get('location', 'Unknown')
        last_location = last_log.get('location', 'Unknown')
        
        # Same location is always possible
        if current_location == last_location:
            return False, None
        
        # Calculate time difference
        time_diff = self.time_diff_hours(
            last_log.get('login_time', '00:00'),
            current_log.get('login_time', '00:00')
        )
        
        # If time difference is very small, likely impossible
        if time_diff < 0.1:  # Less than 6 minutes
            time_diff = 0.1  # Prevent division by zero
        
        # Get distance
        distance = self.get_distance(last_location, current_location)
        
        # Calculate required speed
        required_speed = distance / time_diff
        
        # Check if speed exceeds maximum realistic speed
        if required_speed > self.max_speed:
            return True, f"Impossible travel: {distance:.0f}km in {time_diff:.1f}h (requires {required_speed:.0f}km/h)"
        
        return False, None
    
    def check_concurrent_sessions(self, user_id, current_time, history, threshold_minutes=30):
        """
        Detect concurrent sessions from different locations
        
        Args:
            user_id: User identifier
            current_time: Current login time
            history: List of previous login logs
            threshold_minutes: Time window for concurrent sessions
        
        Returns:
            (has_concurrent, message)
        """
        if not history or len(history) == 0:
            return False, None
        
        # Find recent logins from different locations
        recent_locations = set()
        for log in history:
            time_diff = self.time_diff_minutes(log.get('login_time', '00:00'), current_time)
            if time_diff <= threshold_minutes:
                recent_locations.add(log.get('location', 'Unknown'))
        
        if len(recent_locations) > 1:
            return True, f"Concurrent sessions from {len(recent_locations)} locations: {', '.join(recent_locations)}"
        
        return False, None
    
    def perform_all_checks(self, current_log, user_history):
        """
        Perform all velocity checks
        
        Returns:
            {
                'has_alerts': bool,
                'alerts': list of alert messages,
                'severity': 'LOW' | 'MEDIUM' | 'HIGH'
            }
        """
        alerts = []
        severity = 'LOW'
        
        user_id = current_log.get('user_id', 'unknown')
        current_time = current_log.get('login_time', '00:00')
        
        # Check rapid logins
        is_rapid, rapid_msg = self.check_rapid_logins(user_id, current_time, user_history)
        if is_rapid:
            alerts.append(f"⚡ Rapid Login: {rapid_msg}")
            severity = 'MEDIUM'
        
        # Check impossible travel
        if user_history and len(user_history) > 0:
            last_log = user_history[-1]
            is_impossible, impossible_msg = self.check_impossible_travel(current_log, last_log)
            if is_impossible:
                alerts.append(f"✈️ Impossible Travel: {impossible_msg}")
                severity = 'HIGH'
        
        # Check concurrent sessions
        is_concurrent, concurrent_msg = self.check_concurrent_sessions(user_id, current_time, user_history)
        if is_concurrent:
            alerts.append(f"🔄 Concurrent Sessions: {concurrent_msg}")
            if severity != 'HIGH':
                severity = 'MEDIUM'
        
        return {
            'has_alerts': len(alerts) > 0,
            'alerts': alerts,
            'severity': severity
        }


# Global instance
velocity_checker = VelocityChecker()


if __name__ == "__main__":
    # Test the velocity checker
    print("Testing Velocity Checker...")
    
    # Test 1: Rapid logins
    print("\n=== Test 1: Rapid Logins ===")
    history = [
        {'login_time': '10:00', 'location': 'New York'},
        {'login_time': '10:02', 'location': 'New York'},
        {'login_time': '10:04', 'location': 'New York'},
    ]
    is_rapid, msg = velocity_checker.check_rapid_logins('user_001', '10:05', history)
    print(f"Rapid Login: {is_rapid} - {msg}")
    
    # Test 2: Impossible travel
    print("\n=== Test 2: Impossible Travel ===")
    last_log = {'login_time': '10:00', 'location': 'New York'}
    current_log = {'login_time': '10:30', 'location': 'Tokyo'}
    is_impossible, msg = velocity_checker.check_impossible_travel(current_log, last_log)
    print(f"Impossible Travel: {is_impossible} - {msg}")
    
    # Test 3: All checks
    print("\n=== Test 3: All Checks ===")
    current_log = {'user_id': 'user_001', 'login_time': '10:05', 'location': 'London'}
    result = velocity_checker.perform_all_checks(current_log, history)
    print(f"Has Alerts: {result['has_alerts']}")
    print(f"Severity: {result['severity']}")
    print(f"Alerts: {result['alerts']}")
