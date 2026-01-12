from plyer import notification
import time

print("Testing notification...")
try:
    notification.notify(
        title="Test Notification",
        message="Dies is a test from Moti-Mate",
        app_name="Motivation Mate",
        timeout=5
    )
    print("Notification sent.")
except Exception as e:
    print(f"Error: {e}")
