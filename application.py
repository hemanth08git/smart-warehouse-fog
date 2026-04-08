

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import json
import logging
import boto3
from collections import defaultdict
import threading
import time

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API endpoint
API_URL = "https://83i550wn0g.execute-api.us-east-1.amazonaws.com/default/lambda-fetch-x25104683"

# SNS Configuration
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:warehouse-alerts"  # Replace with your ARN
sns_client = boto3.client('sns', region_name='us-east-1')

# Track sent alerts to avoid duplicates
sent_alerts = set()
alert_cache_duration = 3600  # 1 hour

# Cache for data
data_cache = []
cache_timestamp = None
CACHE_DURATION = 30  # seconds

def send_sns_alert(alert_data):
    """Send SNS email notification for an alert"""
    try:
        # Create a unique key for this alert to avoid duplicates
        alert_key = f"{alert_data.get('timestamp')}_{alert_data.get('warehouse_id')}"
        
        # Check if we've already sent this alert
        if alert_key in sent_alerts:
            logger.info(f"Skipping duplicate alert: {alert_key}")
            return False
        
        # Format alert message
        alerts_list = alert_data.get('alerts', [])
        alert_severity = "CRITICAL" if len(alerts_list) >= 2 else "WARNING"
        
        # Build email subject
        subject = f"🚨 WAREHOUSE ALERT - {alert_severity} - {alert_data.get('warehouse_id')}"
        
        # Build email message
        message = f"""
WAREHOUSE MONITORING ALERT - {alert_severity}

Alert Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Warehouse ID: {alert_data.get('warehouse_id', 'Unknown')}
• Timestamp: {alert_data.get('timestamp', 'Unknown')}
• Severity: {alert_severity}

Current Readings:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Temperature: {alert_data.get('temperature', 'N/A')}°C
• Humidity: {alert_data.get('humidity', 'N/A')}%
• Gas Level: {alert_data.get('gas_level', 'N/A')} ppm
• Light Level: {alert_data.get('light_level', 'N/A')} lux
• Vibration: {alert_data.get('vibration', 'N/A')} mm/s
• Motion Detected: {'Yes' if alert_data.get('motion_detected') else 'No'}

Alerts Triggered:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{chr(10).join(f'• {alert}' for alert in alerts_list)}

Recommended Actions:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # Add specific recommendations based on alerts
        recommendations = []
        for alert in alerts_list:
            if alert == "HIGH_TEMPERATURE":
                recommendations.append("• Check HVAC system and ventilation")
            elif alert == "HIGH_HUMIDITY":
                recommendations.append("• Check for water leaks or condensation")
            elif alert == "GAS_LEAK":
                recommendations.append("• IMMEDIATE ACTION: Evacuate area and check gas lines")
            elif alert == "MOTION_DETECTED":
                recommendations.append("• Check security cameras for unauthorized access")
            elif alert == "HIGH_VIBRATION":
                recommendations.append("• Inspect machinery for mechanical issues")
        
        message += "\n".join(recommendations) if recommendations else "• Monitor situation closely"
        
        message += f"""

Action Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Please investigate this alert immediately.

View dashboard: http://your-flask-app.com

---
This is an automated alert from your Warehouse Monitoring System.
"""
        
        # Send SNS notification
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message,
            MessageAttributes={
                'alert_type': {
                    'DataType': 'String',
                    'StringValue': alert_severity
                },
                'warehouse_id': {
                    'DataType': 'String',
                    'StringValue': str(alert_data.get('warehouse_id', 'Unknown'))
                },
                'alert_count': {
                    'DataType': 'Number',
                    'StringValue': str(len(alerts_list))
                }
            }
        )
        
        # Add to sent alerts cache
        sent_alerts.add(alert_key)
        
        # Clean old alerts from cache periodically
        if len(sent_alerts) > 1000:
            sent_alerts.clear()
        
        logger.info(f"SNS alert sent: {response['MessageId']}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send SNS alert: {str(e)}")
        return False







def fetch_sensor_data(force_refresh=False):
    """Fetch sensor data from the API with caching"""
    global data_cache, cache_timestamp
    
    current_time = datetime.now()
    
    if not force_refresh and cache_timestamp and (current_time - cache_timestamp).seconds < CACHE_DURATION:
        return data_cache
    
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Sort data by timestamp
        data.sort(key=lambda x: x['timestamp'])
        
        # Convert timestamp strings to datetime objects for filtering
        for record in data:
            record['datetime'] = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
        
        data_cache = data
        cache_timestamp = current_time
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return data_cache if data_cache else []

def filter_data_by_date(data, start_date, end_date):
    """Filter data by date range"""
    if not start_date and not end_date:
        return data
    
    filtered = []
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    for record in data:
        record_date = record['datetime']
        if start and record_date < start:
            continue
        if end and record_date > end:
            continue
        filtered.append(record)
    
    return filtered

def calculate_statistics(data):
    """Calculate comprehensive statistics"""
    if not data:
        return {}
    
    df = pd.DataFrame(data)
    
    stats = {
        'current': {
            'temperature': float(df['temperature'].iloc[-1]),
            'humidity': float(df['humidity'].iloc[-1]),
            'gas_level': float(df['gas_level'].iloc[-1]),
            'light_level': int(df['light_level'].iloc[-1]),
            'vibration': float(df['vibration'].iloc[-1]),
            'motion_detected': int(df['motion_detected'].iloc[-1]),
            'alert_flag': int(df['alert_flag'].iloc[-1]),
            'alerts': df['alerts'].iloc[-1]
        },
        'statistics': {
            'temperature': {
                'avg': float(df['temperature'].mean()),
                'min': float(df['temperature'].min()),
                'max': float(df['temperature'].max()),
                'std': float(df['temperature'].std())
            },
            'humidity': {
                'avg': float(df['humidity'].mean()),
                'min': float(df['humidity'].min()),
                'max': float(df['humidity'].max()),
                'std': float(df['humidity'].std())
            },
            'gas_level': {
                'avg': float(df['gas_level'].mean()),
                'min': float(df['gas_level'].min()),
                'max': float(df['gas_level'].max()),
                'std': float(df['gas_level'].std())
            },
            'vibration': {
                'avg': float(df['vibration'].mean()),
                'min': float(df['vibration'].min()),
                'max': float(df['vibration'].max()),
                'std': float(df['vibration'].std())
            }
        },
        'alerts_summary': {
            'total_alerts': int(df['alert_flag'].sum()),
            'alert_rate': float(df['alert_flag'].mean() * 100),
            'motion_events': int(df['motion_detected'].sum()),
            'motion_rate': float(df['motion_detected'].mean() * 100)
        },
        'total_readings': len(data)
    }
    
    return stats

@app.route('/')
def dashboard():
    """Render the dashboard"""
    return render_template('dashboard.html')

@app.route('/api/data')
def get_data():
    """API endpoint to get filtered sensor data"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    data = fetch_sensor_data()
    filtered_data = filter_data_by_date(data, start_date, end_date)
    
    # Convert datetime objects back to strings for JSON
    for record in filtered_data:
        record['timestamp'] = record['timestamp']
        if 'datetime' in record:
            del record['datetime']
    
    return jsonify(filtered_data)

@app.route('/api/stats')
def get_stats():
    """API endpoint to get statistics"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    data = fetch_sensor_data()
    filtered_data = filter_data_by_date(data, start_date, end_date)
    stats = calculate_statistics(filtered_data)
    
    return jsonify(stats)




@app.route('/api/alerts')
def get_alerts():
    """API endpoint to get alerts only and optionally send SNS"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    send_email = request.args.get('send_email', 'false').lower() == 'true'
    
    data = fetch_sensor_data()
    filtered_data = filter_data_by_date(data, start_date, end_date)
    alerts = [d for d in filtered_data if d.get('alert_flag') == 1]
    
    # Send SNS for recent alerts if requested
    if send_email and alerts:
        # Send only the latest alert to avoid spam
        latest_alert = alerts[-1] if alerts else None
        if latest_alert:
            send_sns_alert(latest_alert)
    
    return jsonify(alerts)


@app.route('/api/send-test-alert')
def send_test_alert():
    """Test endpoint to manually send an alert email"""
    test_alert = {
        'warehouse_id': 'WH-001',
        'timestamp': datetime.now().isoformat(),
        'temperature': 35.5,
        'humidity': 85.0,
        'gas_level': 750,
        'light_level': 500,
        'motion_detected': 1,
        'vibration': 4.5,
        'alerts': ['HIGH_TEMPERATURE', 'GAS_LEAK', 'MOTION_DETECTED'],
        'alert_flag': 1
    }
    
    success = send_sns_alert(test_alert)
    
    if success:
        return jsonify({'message': 'Test alert sent successfully'})
    else:
        return jsonify({'error': 'Failed to send test alert'}), 500




@app.route('/api/latest')
def get_latest():
    """API endpoint to get latest reading"""
    data = fetch_sensor_data()
    if data:
        latest = data[-1].copy()
        if 'datetime' in latest:
            del latest['datetime']
        return jsonify(latest)
    return jsonify({})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)



#---------------------------------------------------------------
