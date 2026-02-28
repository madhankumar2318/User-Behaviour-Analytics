"""
Behavior Profiler
Builds and analyzes user behavior profiles for personalized risk assessment
"""

from datetime import datetime
import json


class UserProfile:
    def __init__(self, user_id):
        self.user_id = user_id
        self.baseline = {
            'avg_login_hour': None,
            'std_login_hour': None,
            'common_locations': {},
            'avg_downloads': None,
            'std_downloads': None,
            'avg_failed_attempts': None,
            'typical_login_count': 0,
            'first_seen': None,
            'last_updated': None
        }
    
    def parse_time(self, time_str):
        """Parse time string to hour"""
        try:
            parts = time_str.split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            return hour + (minute / 60.0)  # Convert to decimal hours
        except:
            return 12.0  # Default to noon
    
    def calculate_statistics(self, values):
        """Calculate mean and standard deviation"""
        if not values or len(values) == 0:
            return 0, 0
        
        mean = sum(values) / len(values)
        
        if len(values) == 1:
            return mean, 0
        
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std = variance ** 0.5
        
        return mean, std
    
    def update_profile(self, logs):
        """Update profile based on user's activity logs"""
        if not logs or len(logs) == 0:
            return
        
        # Extract data
        login_hours = [self.parse_time(log.get('login_time', '12:00')) for log in logs]
        downloads = [log.get('downloads', 0) for log in logs]
        failed_attempts = [log.get('failed_attempts', 0) for log in logs]
        
        # Calculate averages and standard deviations
        self.baseline['avg_login_hour'], self.baseline['std_login_hour'] = \
            self.calculate_statistics(login_hours)
        
        self.baseline['avg_downloads'], self.baseline['std_downloads'] = \
            self.calculate_statistics(downloads)
        
        self.baseline['avg_failed_attempts'], _ = \
            self.calculate_statistics(failed_attempts)
        
        # Count location frequencies
        location_counts = {}
        for log in logs:
            location = log.get('location', 'Unknown')
            location_counts[location] = location_counts.get(location, 0) + 1
        
        # Store as percentages
        total = len(logs)
        self.baseline['common_locations'] = {
            loc: count / total for loc, count in location_counts.items()
        }
        
        # Update metadata
        self.baseline['typical_login_count'] = len(logs)
        self.baseline['last_updated'] = datetime.now().isoformat()
        
        if not self.baseline['first_seen']:
            self.baseline['first_seen'] = datetime.now().isoformat()
    
    def calculate_deviation_score(self, new_log):
        """
        Calculate how much new log deviates from user's baseline
        Returns score 0-100 (higher = more deviation)
        """
        if self.baseline['avg_login_hour'] is None:
            return 0  # No baseline yet
        
        score = 0
        reasons = []
        
        # 1. Login Time Deviation (0-30 points)
        new_hour = self.parse_time(new_log.get('login_time', '12:00'))
        hour_diff = abs(new_hour - self.baseline['avg_login_hour'])
        
        # Handle wraparound (e.g., 23:00 vs 01:00)
        if hour_diff > 12:
            hour_diff = 24 - hour_diff
        
        # If standard deviation exists, use it for scoring
        if self.baseline['std_login_hour'] and self.baseline['std_login_hour'] > 0:
            hour_score = min(30, (hour_diff / self.baseline['std_login_hour']) * 10)
        else:
            hour_score = min(30, hour_diff * 2.5)
        
        if hour_score > 15:
            score += hour_score
            reasons.append(f"Unusual login time ({new_hour:.1f}h vs avg {self.baseline['avg_login_hour']:.1f}h)")
        
        # 2. Location Deviation (0-30 points)
        new_location = new_log.get('location', 'Unknown')
        location_familiarity = self.baseline['common_locations'].get(new_location, 0)
        
        if location_familiarity == 0:
            # Completely new location
            score += 30
            reasons.append(f"New location: {new_location}")
        elif location_familiarity < 0.1:
            # Rare location
            score += 20
            reasons.append(f"Rare location: {new_location}")
        
        # 3. Download Deviation (0-25 points)
        new_downloads = new_log.get('downloads', 0)
        
        if self.baseline['avg_downloads'] and self.baseline['avg_downloads'] > 0:
            download_ratio = new_downloads / self.baseline['avg_downloads']
            
            if download_ratio > 2.0:
                download_score = min(25, (download_ratio - 2.0) * 10)
                score += download_score
                reasons.append(f"High downloads ({new_downloads} vs avg {self.baseline['avg_downloads']:.1f})")
        
        # 4. Failed Attempts Deviation (0-15 points)
        new_failed = new_log.get('failed_attempts', 0)
        
        if new_failed > self.baseline['avg_failed_attempts'] + 2:
            failed_score = min(15, (new_failed - self.baseline['avg_failed_attempts']) * 5)
            score += failed_score
            reasons.append(f"High failed attempts ({new_failed} vs avg {self.baseline['avg_failed_attempts']:.1f})")
        
        return min(100, score), reasons
    
    def to_dict(self):
        """Convert profile to dictionary"""
        return {
            'user_id': self.user_id,
            'baseline': self.baseline
        }
    
    def from_dict(self, data):
        """Load profile from dictionary"""
        self.user_id = data.get('user_id', self.user_id)
        self.baseline = data.get('baseline', self.baseline)


class ProfileManager:
    def __init__(self):
        self.profiles = {}  # user_id -> UserProfile
    
    def get_profile(self, user_id):
        """Get or create user profile"""
        if user_id not in self.profiles:
            self.profiles[user_id] = UserProfile(user_id)
        return self.profiles[user_id]
    
    def update_profile(self, user_id, logs):
        """Update user profile with new logs"""
        profile = self.get_profile(user_id)
        profile.update_profile(logs)
        return profile
    
    def calculate_deviation(self, user_id, new_log):
        """Calculate deviation score for new log"""
        profile = self.get_profile(user_id)
        return profile.calculate_deviation_score(new_log)
    
    def get_all_profiles(self):
        """Get all user profiles"""
        return {uid: profile.to_dict() for uid, profile in self.profiles.items()}
    
    def save_profiles(self, filepath='user_profiles.json'):
        """Save all profiles to file"""
        try:
            data = self.get_all_profiles()
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Saved {len(data)} profiles to {filepath}")
        except Exception as e:
            print(f"❌ Error saving profiles: {e}")
    
    def load_profiles(self, filepath='user_profiles.json'):
        """Load profiles from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            for user_id, profile_data in data.items():
                profile = UserProfile(user_id)
                profile.from_dict(profile_data)
                self.profiles[user_id] = profile
            
            print(f"✅ Loaded {len(data)} profiles from {filepath}")
        except FileNotFoundError:
            print(f"ℹ️ No profile file found at {filepath}")
        except Exception as e:
            print(f"❌ Error loading profiles: {e}")


# Global instance
profile_manager = ProfileManager()


if __name__ == "__main__":
    # Test the behavior profiler
    print("Testing Behavior Profiler...")
    
    # Sample user history
    user_history = [
        {'login_time': '09:00', 'downloads': 5, 'failed_attempts': 0, 'location': 'New York'},
        {'login_time': '09:15', 'downloads': 7, 'failed_attempts': 0, 'location': 'New York'},
        {'login_time': '09:30', 'downloads': 6, 'failed_attempts': 0, 'location': 'New York'},
        {'login_time': '10:00', 'downloads': 8, 'failed_attempts': 1, 'location': 'New York'},
        {'login_time': '10:30', 'downloads': 5, 'failed_attempts': 0, 'location': 'London'},
    ]
    
    # Update profile
    print("\n=== Building User Profile ===")
    profile = profile_manager.update_profile('user_001', user_history)
    print(f"Average login hour: {profile.baseline['avg_login_hour']:.2f}")
    print(f"Average downloads: {profile.baseline['avg_downloads']:.2f}")
    print(f"Common locations: {profile.baseline['common_locations']}")
    
    # Test deviation detection
    print("\n=== Testing Deviation Detection ===")
    
    # Normal activity
    normal_log = {'login_time': '09:45', 'downloads': 6, 'failed_attempts': 0, 'location': 'New York'}
    score, reasons = profile.calculate_deviation_score(normal_log)
    print(f"\nNormal Activity:")
    print(f"  Score: {score:.2f}")
    print(f"  Reasons: {reasons}")
    
    # Anomalous activity
    anomalous_log = {'login_time': '23:00', 'downloads': 50, 'failed_attempts': 5, 'location': 'Tokyo'}
    score, reasons = profile.calculate_deviation_score(anomalous_log)
    print(f"\nAnomalous Activity:")
    print(f"  Score: {score:.2f}")
    print(f"  Reasons: {reasons}")
