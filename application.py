

# from flask import Flask, render_template, jsonify, request
# from flask_cors import CORS
# import requests
# from datetime import datetime, timedelta
# import json
# import logging
# import boto3
# from collections import defaultdict
# import threading
# import time

# application = Flask(__name__)
# app = application
# CORS(app)

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # API endpoint
# API_URL = "https://83i550wn0g.execute-api.us-east-1.amazonaws.com/default/lambda-fetch-x25104683"

# # SNS Configuration
# SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:warehouse-alerts"  # Replace with your ARN
# sns_client = boto3.client('sns', region_name='us-east-1')

# # Track sent alerts to avoid duplicates
# sent_alerts = set()
# alert_cache_duration = 3600  # 1 hour

# # Cache for data
# data_cache = []
# cache_timestamp = None
# CACHE_DURATION = 30  # seconds

# def send_sns_alert(alert_data):
#     """Send SNS email notification for an alert"""
#     try:
#         # Create a unique key for this alert to avoid duplicates
#         alert_key = f"{alert_data.get('timestamp')}_{alert_data.get('warehouse_id')}"
        
#         # Check if we've already sent this alert
#         if alert_key in sent_alerts:
#             logger.info(f"Skipping duplicate alert: {alert_key}")
#             return False
        
#         # Format alert message
#         alerts_list = alert_data.get('alerts', [])
#         alert_severity = "CRITICAL" if len(alerts_list) >= 2 else "WARNING"
        
#         # Build email subject
#         subject = f" WAREHOUSE ALERT - {alert_severity} - {alert_data.get('warehouse_id')}"
        
#         # Build email message
#         message = f"""
# WAREHOUSE MONITORING ALERT - {alert_severity}

# Alert Details:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# • Warehouse ID: {alert_data.get('warehouse_id', 'Unknown')}
# • Timestamp: {alert_data.get('timestamp', 'Unknown')}
# • Severity: {alert_severity}

# Current Readings:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# • Temperature: {alert_data.get('temperature', 'N/A')}°C
# • Humidity: {alert_data.get('humidity', 'N/A')}%
# • Gas Level: {alert_data.get('gas_level', 'N/A')} ppm
# • Light Level: {alert_data.get('light_level', 'N/A')} lux
# • Vibration: {alert_data.get('vibration', 'N/A')} mm/s
# • Motion Detected: {'Yes' if alert_data.get('motion_detected') else 'No'}

# Alerts Triggered:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# {chr(10).join(f'• {alert}' for alert in alerts_list)}

# Recommended Actions:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# """
        
#         # Add specific recommendations based on alerts
#         recommendations = []
#         for alert in alerts_list:
#             if alert == "HIGH_TEMPERATURE":
#                 recommendations.append("• Check HVAC system and ventilation")
#             elif alert == "HIGH_HUMIDITY":
#                 recommendations.append("• Check for water leaks or condensation")
#             elif alert == "GAS_LEAK":
#                 recommendations.append("• IMMEDIATE ACTION: Evacuate area and check gas lines")
#             elif alert == "MOTION_DETECTED":
#                 recommendations.append("• Check security cameras for unauthorized access")
#             elif alert == "HIGH_VIBRATION":
#                 recommendations.append("• Inspect machinery for mechanical issues")
        
#         message += "\n".join(recommendations) if recommendations else "• Monitor situation closely"
        
#         message += f"""

# Action Required:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Please investigate this alert immediately.

# View dashboard: http://your-flask-app.com

# ---
# This is an automated alert from your Warehouse Monitoring System.
# """
        
#         # Send SNS notification
#         response = sns_client.publish(
#             TopicArn=SNS_TOPIC_ARN,
#             Subject=subject,
#             Message=message,
#             MessageAttributes={
#                 'alert_type': {
#                     'DataType': 'String',
#                     'StringValue': alert_severity
#                 },
#                 'warehouse_id': {
#                     'DataType': 'String',
#                     'StringValue': str(alert_data.get('warehouse_id', 'Unknown'))
#                 },
#                 'alert_count': {
#                     'DataType': 'Number',
#                     'StringValue': str(len(alerts_list))
#                 }
#             }
#         )
        
#         # Add to sent alerts cache
#         sent_alerts.add(alert_key)
        
#         # Clean old alerts from cache periodically
#         if len(sent_alerts) > 1000:
#             sent_alerts.clear()
        
#         logger.info(f"SNS alert sent: {response['MessageId']}")
#         return True
        
#     except Exception as e:
#         logger.error(f"Failed to send SNS alert: {str(e)}")
#         return False







# def fetch_sensor_data(force_refresh=False):
#     """Fetch sensor data from the API with caching"""
#     global data_cache, cache_timestamp
    
#     current_time = datetime.now()
    
#     if not force_refresh and cache_timestamp and (current_time - cache_timestamp).seconds < CACHE_DURATION:
#         return data_cache
    
#     try:
#         response = requests.get(API_URL, timeout=10)
#         response.raise_for_status()
#         data = response.json()
        
#         # Sort data by timestamp
#         data.sort(key=lambda x: x['timestamp'])
        
#         # Convert timestamp strings to datetime objects for filtering
#         for record in data:
#             record['datetime'] = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
        
#         data_cache = data
#         cache_timestamp = current_time
#         return data
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching data: {e}")
#         return data_cache if data_cache else []

# def filter_data_by_date(data, start_date, end_date):
#     """Filter data by date range"""
#     if not start_date and not end_date:
#         return data
    
#     filtered = []
#     start = datetime.fromisoformat(start_date) if start_date else None
#     end = datetime.fromisoformat(end_date) if end_date else None
    
#     for record in data:
#         record_date = record['datetime']
#         if start and record_date < start:
#             continue
#         if end and record_date > end:
#             continue
#         filtered.append(record)
    
#     return filtered

# def calculate_statistics(data):
#     """Calculate comprehensive statistics"""
#     if not data:
#         return {}
    
#     df = pd.DataFrame(data)
    
#     stats = {
#         'current': {
#             'temperature': float(df['temperature'].iloc[-1]),
#             'humidity': float(df['humidity'].iloc[-1]),
#             'gas_level': float(df['gas_level'].iloc[-1]),
#             'light_level': int(df['light_level'].iloc[-1]),
#             'vibration': float(df['vibration'].iloc[-1]),
#             'motion_detected': int(df['motion_detected'].iloc[-1]),
#             'alert_flag': int(df['alert_flag'].iloc[-1]),
#             'alerts': df['alerts'].iloc[-1]
#         },
#         'statistics': {
#             'temperature': {
#                 'avg': float(df['temperature'].mean()),
#                 'min': float(df['temperature'].min()),
#                 'max': float(df['temperature'].max()),
#                 'std': float(df['temperature'].std())
#             },
#             'humidity': {
#                 'avg': float(df['humidity'].mean()),
#                 'min': float(df['humidity'].min()),
#                 'max': float(df['humidity'].max()),
#                 'std': float(df['humidity'].std())
#             },
#             'gas_level': {
#                 'avg': float(df['gas_level'].mean()),
#                 'min': float(df['gas_level'].min()),
#                 'max': float(df['gas_level'].max()),
#                 'std': float(df['gas_level'].std())
#             },
#             'vibration': {
#                 'avg': float(df['vibration'].mean()),
#                 'min': float(df['vibration'].min()),
#                 'max': float(df['vibration'].max()),
#                 'std': float(df['vibration'].std())
#             }
#         },
#         'alerts_summary': {
#             'total_alerts': int(df['alert_flag'].sum()),
#             'alert_rate': float(df['alert_flag'].mean() * 100),
#             'motion_events': int(df['motion_detected'].sum()),
#             'motion_rate': float(df['motion_detected'].mean() * 100)
#         },
#         'total_readings': len(data)
#     }
    
#     return stats

# @app.route('/')
# def dashboard():
#     """Render the dashboard"""
#     return render_template('dashboard.html')

# @app.route('/api/data')
# def get_data():
#     """API endpoint to get filtered sensor data"""
#     start_date = request.args.get('start_date')
#     end_date = request.args.get('end_date')
    
#     data = fetch_sensor_data()
#     filtered_data = filter_data_by_date(data, start_date, end_date)
    
#     # Convert datetime objects back to strings for JSON
#     for record in filtered_data:
#         record['timestamp'] = record['timestamp']
#         if 'datetime' in record:
#             del record['datetime']
    
#     return jsonify(filtered_data)

# @app.route('/api/stats')
# def get_stats():
#     """API endpoint to get statistics"""
#     start_date = request.args.get('start_date')
#     end_date = request.args.get('end_date')
    
#     data = fetch_sensor_data()
#     filtered_data = filter_data_by_date(data, start_date, end_date)
#     stats = calculate_statistics(filtered_data)
    
#     return jsonify(stats)




# @app.route('/api/alerts')
# def get_alerts():
#     """API endpoint to get alerts only and optionally send SNS"""
#     start_date = request.args.get('start_date')
#     end_date = request.args.get('end_date')
#     send_email = request.args.get('send_email', 'false').lower() == 'true'
    
#     data = fetch_sensor_data()
#     filtered_data = filter_data_by_date(data, start_date, end_date)
#     alerts = [d for d in filtered_data if d.get('alert_flag') == 1]
    
#     # Send SNS for recent alerts if requested
#     if send_email and alerts:
#         # Send only the latest alert to avoid spam
#         latest_alert = alerts[-1] if alerts else None
#         if latest_alert:
#             send_sns_alert(latest_alert)
    
#     return jsonify(alerts)


# @app.route('/api/send-test-alert')
# def send_test_alert():
#     """Test endpoint to manually send an alert email"""
#     test_alert = {
#         'warehouse_id': 'WH-001',
#         'timestamp': datetime.now().isoformat(),
#         'temperature': 35.5,
#         'humidity': 85.0,
#         'gas_level': 750,
#         'light_level': 500,
#         'motion_detected': 1,
#         'vibration': 4.5,
#         'alerts': ['HIGH_TEMPERATURE', 'GAS_LEAK', 'MOTION_DETECTED'],
#         'alert_flag': 1
#     }
    
#     success = send_sns_alert(test_alert)
    
#     if success:
#         return jsonify({'message': 'Test alert sent successfully'})
#     else:
#         return jsonify({'error': 'Failed to send test alert'}), 500




# @app.route('/api/latest')
# def get_latest():
#     """API endpoint to get latest reading"""
#     data = fetch_sensor_data()
#     if data:
#         latest = data[-1].copy()
#         if 'datetime' in latest:
#             del latest['datetime']
#         return jsonify(latest)
#     return jsonify({})

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)



# #---------------------------------------------------------------



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

application = Flask(__name__)
app = application
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API endpoint
API_URL = "https://83i550wn0g.execute-api.us-east-1.amazonaws.com/default/lambda-fetch-x25104683"

# SNS Configuration
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:891377173915:sns-fog-x25104683"  # Replace with your ARN
sns_client = boto3.client('sns', region_name='us-east-1')

# Track consecutive alerts for each warehouse
consecutive_alerts = defaultdict(int)
last_alert_status = defaultdict(bool)
alert_sent_for_sequence = defaultdict(set)  # Track which sequences have triggered emails

# Cache for data
data_cache = []
cache_timestamp = None
CACHE_DURATION = 30  # seconds

def check_consecutive_alerts(warehouse_id, current_alert_flag):
    """
    Check if there are 3 consecutive alerts
    Returns: (should_send_alert, consecutive_count)
    """
    global consecutive_alerts, last_alert_status, alert_sent_for_sequence
    
    if current_alert_flag == 1:
        # Current reading has alert
        if last_alert_status[warehouse_id]:
            # Previous was also alert - increment counter
            consecutive_alerts[warehouse_id] += 1
            logger.info(f"Warehouse {warehouse_id}: Consecutive alert count = {consecutive_alerts[warehouse_id]}")
        else:
            # First alert in a new sequence
            consecutive_alerts[warehouse_id] = 1
            logger.info(f"Warehouse {warehouse_id}: New alert sequence started - count = 1")
        
        last_alert_status[warehouse_id] = True
        
        # Check if we've reached 3 consecutive alerts
        if consecutive_alerts[warehouse_id] >= 3:
            # Create a sequence key to avoid sending multiple emails for same sequence
            sequence_key = f"{warehouse_id}_{datetime.now().strftime('%Y%m%d_%H')}"
            
            if sequence_key not in alert_sent_for_sequence[warehouse_id]:
                alert_sent_for_sequence[warehouse_id].add(sequence_key)
                logger.info(f"3 CONSECUTIVE ALERTS detected for warehouse {warehouse_id}! Sending SNS email...")
                return True, consecutive_alerts[warehouse_id]
            else:
                logger.info(f"Already sent alert for sequence {sequence_key}, skipping duplicate")
                return False, consecutive_alerts[warehouse_id]
        else:
            logger.info(f"Only {consecutive_alerts[warehouse_id]} consecutive alert(s), need 3 to send email")
            return False, consecutive_alerts[warehouse_id]
    else:
        # No alert - reset counter
        if last_alert_status[warehouse_id]:
            logger.info(f"Warehouse {warehouse_id}: Alert sequence broken at {consecutive_alerts[warehouse_id]} alerts")
        consecutive_alerts[warehouse_id] = 0
        last_alert_status[warehouse_id] = False
        return False, 0

# def send_sns_alert(alert_data, consecutive_count):
#     """Send SNS email notification for 3 consecutive alerts"""
#     try:
#         warehouse_id = alert_data.get('warehouse_id', 'Unknown')
        
#         # Format email subject
#         subject = f" CRITICAL ALERT - 3 Consecutive Alerts - Warehouse {warehouse_id}"
        
#         # Build detailed email message
#         alerts_list = alert_data.get('alerts', [])
#         alerts_text = "\n".join([f"  • {alert}" for alert in alerts_list]) if alerts_list else "  • Multiple threshold violations detected"
        
#         message = f"""
# ╔══════════════════════════════════════════════════════════════╗
# ║      CRITICAL: 3 CONSECUTIVE ALERTS DETECTED           ║
# ╚══════════════════════════════════════════════════════════════╝

# This alert has been triggered after 3 consecutive sensor readings 
# exceeded threshold limits, indicating a persistent issue.

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ALERT DETAILS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# • Warehouse ID: {warehouse_id}
# • Consecutive Alerts: {consecutive_count}
# • Timestamp: {alert_data.get('timestamp', 'Unknown')}
# • Severity: CRITICAL

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CURRENT READINGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# • Temperature: {alert_data.get('temperature', 'N/A')}°C 
#   [Threshold: > 30°C]
  
# • Humidity: {alert_data.get('humidity', 'N/A')}% 
#   [Threshold: > 70%]
  
# • Gas Level: {alert_data.get('gas_level', 'N/A')} ppm 
#   [Threshold: > 500 ppm]
  
# • Light Level: {alert_data.get('light_level', 'N/A')} lux
# • Vibration: {alert_data.get('vibration', 'N/A')} mm/s
# • Motion Detected: {'✓ YES' if alert_data.get('motion_detected') else '✗ NO'}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ALERTS TRIGGERED (3 Consecutive Times)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# {alerts_text}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RECOMMENDED ACTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# """

#         # Add specific recommendations
#         recommendations = []
#         for alert in alerts_list:
#             if alert == "HIGH_TEMPERATURE":
#                 recommendations.append("• Inspect HVAC system and cooling units")
#                 recommendations.append("• Check for overheating equipment")
#             elif alert == "HIGH_HUMIDITY":
#                 recommendations.append("• Check dehumidifiers and ventilation")
#                 recommendations.append("• Inspect for water leaks or condensation")
#             elif alert == "GAS_LEAK":
#                 recommendations.append("• IMMEDIATE: Evacuate area if necessary")
#                 recommendations.append("• Check gas lines and storage containers")
#             elif alert == "MOTION_DETECTED":
#                 recommendations.append("• Review security footage immediately")
#                 recommendations.append("• Dispatch security personnel")
#             elif alert == "HIGH_VIBRATION":
#                 recommendations.append("• Inspect machinery and equipment")
#                 recommendations.append("• Schedule maintenance check")
        
#         message += "\n".join(set(recommendations)) if recommendations else "• Monitor situation closely and investigate root cause"
        
#         message += f"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ACTION REQUIRED
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# This is a critical alert requiring immediate attention due to 
# persistent threshold violations over 3 consecutive readings.

# Please investigate the warehouse conditions immediately.

# Dashboard: http://your-flask-app.com
# Alert ID: {warehouse_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}

# ---
# This is an automated alert from your Warehouse Monitoring System.
# """
        
#         # Send SNS notification
#         response = sns_client.publish(
#             TopicArn=SNS_TOPIC_ARN,
#             Subject=subject,
#             Message=message,
#             MessageAttributes={
#                 'alert_type': {
#                     'DataType': 'String',
#                     'StringValue': 'CRITICAL'
#                 },
#                 'warehouse_id': {
#                     'DataType': 'String',
#                     'StringValue': str(warehouse_id)
#                 },
#                 'consecutive_alerts': {
#                     'DataType': 'Number',
#                     'StringValue': str(consecutive_count)
#                 },
#                 'alert_count': {
#                     'DataType': 'Number',
#                     'StringValue': str(len(alerts_list))
#                 }
#             }
#         )
        
#         logger.info(f"SNS alert sent successfully for warehouse {warehouse_id} after {consecutive_count} consecutive alerts")
#         logger.info(f"Message ID: {response['MessageId']}")
#         return True
        
#     except Exception as e:
#         logger.error(f"Failed to send SNS alert: {str(e)}")
#         return False




def send_sns_alert(alert_data, consecutive_count):
    """Send SNS email notification for 3 consecutive alerts"""
    try:
        warehouse_id = alert_data.get('warehouse_id', 'Unknown')
        
        # Format email subject
        subject = f"CRITICAL ALERT - 3 Consecutive Alerts - Warehouse {warehouse_id}"
        
        # Build simple alert message
        alerts_list = alert_data.get('alerts', [])
        alerts_text = ", ".join(alerts_list) if alerts_list else "Multiple threshold violations"
        
        message = f"""
CRITICAL ALERT: 3 CONSECUTIVE ALERTS DETECTED

Warehouse: {warehouse_id}
Time: {alert_data.get('timestamp', 'Unknown')}
Consecutive Alerts: {consecutive_count}

Current Readings:
- Temperature: {alert_data.get('temperature', 'N/A')}°C
- Humidity: {alert_data.get('humidity', 'N/A')}%
- Gas Level: {alert_data.get('gas_level', 'N/A')} ppm
- Motion: {'Yes' if alert_data.get('motion_detected') else 'No'}

Alerts: {alerts_text}

Action Required: Investigate warehouse conditions immediately.

Dashboard: http://smartwarehouse.us-east-1.elasticbeanstalk.com/
"""
        
        # Send SNS notification
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message,
            MessageAttributes={
                'alert_type': {
                    'DataType': 'String',
                    'StringValue': 'CRITICAL'
                },
                'warehouse_id': {
                    'DataType': 'String',
                    'StringValue': str(warehouse_id)
                },
                'consecutive_alerts': {
                    'DataType': 'Number',
                    'StringValue': str(consecutive_count)
                }
            }
        )
        
        logger.info(f"SNS alert sent for warehouse {warehouse_id} after {consecutive_count} consecutive alerts")
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

@app.route('/api/alerts')
def get_alerts():
    """API endpoint to get alerts only"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    data = fetch_sensor_data()
    filtered_data = filter_data_by_date(data, start_date, end_date)
    alerts = [d for d in filtered_data if d.get('alert_flag') == 1]
    
    return jsonify(alerts)

@app.route('/api/check-consecutive-alerts')
def check_consecutive_alerts_endpoint():
    """Endpoint to check consecutive alerts and trigger SNS if needed"""
    data = fetch_sensor_data(force_refresh=True)
    
    if not data:
        return jsonify({'message': 'No data available'})
    
    # Get latest reading for each warehouse
    warehouse_readings = {}
    for record in data:
        warehouse_id = record.get('warehouse_id', 'WH-001')
        warehouse_readings[warehouse_id] = record
    
    alerts_sent = []
    for warehouse_id, latest_reading in warehouse_readings.items():
        alert_flag = latest_reading.get('alert_flag', 0)
        
        # Check if we have 3 consecutive alerts
        should_send, consecutive_count = check_consecutive_alerts(warehouse_id, alert_flag)
        
        if should_send:
            # Send SNS alert
            success = send_sns_alert(latest_reading, consecutive_count)
            if success:
                alerts_sent.append({
                    'warehouse_id': warehouse_id,
                    'consecutive_alerts': consecutive_count,
                    'timestamp': latest_reading.get('timestamp')
                })
    
    return jsonify({
        'message': f'Processed {len(warehouse_readings)} warehouses',
        'alerts_sent': alerts_sent,
        'consecutive_alert_counts': dict(consecutive_alerts)
    })

@app.route('/api/latest')
def get_latest():
    """API endpoint to get latest reading and check for consecutive alerts"""
    data = fetch_sensor_data(force_refresh=True)
    
    if not data:
        return jsonify({})
    
    # Get latest reading for each warehouse
    warehouse_readings = {}
    for record in data:
        warehouse_id = record.get('warehouse_id', 'WH-001')
        warehouse_readings[warehouse_id] = record
    
    # Check for consecutive alerts and send SNS if needed
    alerts_triggered = []
    for warehouse_id, latest_reading in warehouse_readings.items():
        alert_flag = latest_reading.get('alert_flag', 0)
        
        # Check consecutive alerts
        should_send, consecutive_count = check_consecutive_alerts(warehouse_id, alert_flag)
        
        if should_send:
            success = send_sns_alert(latest_reading, consecutive_count)
            if success:
                alerts_triggered.append({
                    'warehouse_id': warehouse_id,
                    'consecutive_alerts': consecutive_count,
                    'timestamp': latest_reading.get('timestamp')
                })
        
        # Add consecutive count to response
        latest_reading['consecutive_alerts_count'] = consecutive_count
    
    # Get the most recent reading for display
    latest_reading = list(warehouse_readings.values())[-1] if warehouse_readings else {}
    
    # Remove datetime field for JSON
    if 'datetime' in latest_reading:
        del latest_reading['datetime']
    
    latest_reading['alerts_triggered'] = alerts_triggered
    
    return jsonify(latest_reading)

@app.route('/api/reset-alerts/<warehouse_id>')
def reset_alerts(warehouse_id):
    """Reset consecutive alert counter for a warehouse"""
    global consecutive_alerts, last_alert_status
    
    consecutive_alerts[warehouse_id] = 0
    last_alert_status[warehouse_id] = False
    
    return jsonify({
        'message': f'Alert counter reset for warehouse {warehouse_id}',
        'consecutive_alerts': consecutive_alerts[warehouse_id]
    })

@app.route('/api/alert-status')
def get_alert_status():
    """Get current consecutive alert status for all warehouses"""
    return jsonify({
        'consecutive_alerts': dict(consecutive_alerts),
        'alert_status': dict(last_alert_status)
    })

@app.route('/api/stats')
def get_stats():
    """API endpoint to get statistics"""
    data = fetch_sensor_data()
    
    if not data:
        return jsonify({})
    
    # Calculate statistics
    import pandas as pd
    df = pd.DataFrame(data)
    
    stats = {
        'total_readings': len(data),
        'alert_count': int(df['alert_flag'].sum()) if 'alert_flag' in df else 0,
        'alert_rate': float(df['alert_flag'].mean() * 100) if 'alert_flag' in df else 0,
        'motion_events': int(df['motion_detected'].sum()) if 'motion_detected' in df else 0,
        'avg_temperature': float(df['temperature'].mean()) if 'temperature' in df else 0,
        'avg_humidity': float(df['humidity'].mean()) if 'humidity' in df else 0,
        'avg_gas': float(df['gas_level'].mean()) if 'gas_level' in df else 0
    }
    
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)