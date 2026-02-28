"""
Slack and Microsoft Teams Integration
Sends notifications to team collaboration platforms
"""

import requests
import json
from datetime import datetime

class TeamNotificationService:
    def __init__(self):
        self.slack_webhook = None
        self.teams_webhook = None
    
    def configure_slack(self, webhook_url):
        """Configure Slack webhook URL"""
        self.slack_webhook = webhook_url
    
    def configure_teams(self, webhook_url):
        """Configure Microsoft Teams webhook URL"""
        self.teams_webhook = webhook_url
    
    def send_slack_notification(self, message, title="User Behavior Analytics Alert", color="#dc2626"):
        """Send notification to Slack"""
        if not self.slack_webhook:
            print("Slack webhook not configured")
            return False
        
        try:
            payload = {
                "attachments": [{
                    "color": color,
                    "title": title,
                    "text": message,
                    "footer": "User Behavior Analytics",
                    "ts": int(datetime.now().timestamp())
                }]
            }
            
            response = requests.post(
                self.slack_webhook,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                print("Slack notification sent successfully")
                return True
            else:
                print(f"Failed to send Slack notification: {response.status_code}")
                return False
        except Exception as e:
            print(f"Error sending Slack notification: {e}")
            return False
    
    def send_teams_notification(self, message, title="User Behavior Analytics Alert"):
        """Send notification to Microsoft Teams"""
        if not self.teams_webhook:
            print("Teams webhook not configured")
            return False
        
        try:
            payload = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": title,
                "themeColor": "DC2626",
                "title": title,
                "sections": [{
                    "text": message
                }]
            }
            
            response = requests.post(
                self.teams_webhook,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                print("Teams notification sent successfully")
                return True
            else:
                print(f"Failed to send Teams notification: {response.status_code}")
                return False
        except Exception as e:
            print(f"Error sending Teams notification: {e}")
            return False
    
    def send_high_risk_alert(self, user_id, risk_score, location, slack=True, teams=True):
        """Send high-risk alert to configured platforms"""
        message = f"""
🚨 **High Risk Activity Detected**

**User ID:** {user_id}
**Risk Score:** {risk_score}
**Location:** {location}
**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please review this activity immediately.
        """
        
        results = {}
        
        if slack:
            results['slack'] = self.send_slack_notification(message)
        
        if teams:
            results['teams'] = self.send_teams_notification(message)
        
        return results

# Global instance
team_notification_service = TeamNotificationService()
