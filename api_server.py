"""
API Server for Port-to-Rail Analytics
Bridges the frontend UI to Ollama for real-time logistics queries
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os
from datetime import datetime, timedelta
import random

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from frontend

# Ollama configuration
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")

# System prompt for port logistics analysis
SYSTEM_PROMPT = """You are an AI assistant specialized in port-to-rail logistics analysis for the Port of Houston. 
You analyze shipping data, rail network capacity, and freight flow patterns.

When asked about metrics, provide specific numbers and classifications based on realistic port operations:
- TEU (Twenty-foot Equivalent Units) is the standard container measurement
- Surge risk levels: LOW (0-30% above baseline), MEDIUM (30-60% above baseline), HIGH (60%+ above baseline)
- Use the 30-day rolling baseline for deviation calculations
- Consider time of day patterns (peak hours: 6AM-10AM and 2PM-6PM)

Always provide structured, actionable insights for port operators and logistics planners.
Format numerical data clearly and include risk classifications when relevant."""

# Simulated baseline data (in production, this would come from your database)
def get_current_metrics():
    """Generate current port metrics based on time of day and patterns"""
    now = datetime.now()
    hour = now.hour
    
    # Base TEU volume varies by hour (peak hours have higher volume)
    base_teu = 150  # baseline TEU per hour
    
    # Peak hour multipliers
    if 6 <= hour <= 10:  # Morning peak
        multiplier = 1.4 + random.uniform(-0.1, 0.2)
    elif 14 <= hour <= 18:  # Afternoon peak
        multiplier = 1.5 + random.uniform(-0.1, 0.2)
    elif 22 <= hour or hour <= 5:  # Night (low)
        multiplier = 0.6 + random.uniform(-0.1, 0.1)
    else:  # Normal hours
        multiplier = 1.0 + random.uniform(-0.1, 0.1)
    
    current_teu = int(base_teu * multiplier)
    baseline_30day = 145  # 30-day rolling average
    deviation = ((current_teu - baseline_30day) / baseline_30day) * 100
    
    # Surge risk classification
    if deviation < 30:
        surge_risk = "LOW"
    elif deviation < 60:
        surge_risk = "MEDIUM"
    else:
        surge_risk = "HIGH"
    
    return {
        "timestamp": now.isoformat(),
        "hour": hour,
        "current_teu_per_hour": current_teu,
        "baseline_30day_avg": baseline_30day,
        "percent_deviation": round(deviation, 1),
        "surge_risk": surge_risk,
        "vessels_in_channel": random.randint(15, 35),
        "vessels_at_berth": random.randint(8, 18),
        "rail_cars_waiting": random.randint(50, 200),
        "avg_dwell_time_hours": round(random.uniform(18, 36), 1)
    }

def get_hourly_forecast():
    """Generate 24-hour forecast of TEU volume and surge risk"""
    now = datetime.now()
    forecast = []
    
    for i in range(24):
        future_time = now + timedelta(hours=i)
        hour = future_time.hour
        
        # Pattern-based forecasting
        base_teu = 150
        if 6 <= hour <= 10:
            multiplier = 1.4
            risk = "MEDIUM"
        elif 14 <= hour <= 18:
            multiplier = 1.5
            risk = "HIGH" if i < 6 else "MEDIUM"  # Higher risk for near-term
        elif 22 <= hour or hour <= 5:
            multiplier = 0.6
            risk = "LOW"
        else:
            multiplier = 1.0
            risk = "LOW"
        
        forecast.append({
            "hour": hour,
            "time": future_time.strftime("%H:00"),
            "expected_teu": int(base_teu * multiplier),
            "deviation_from_baseline": round((multiplier - 1) * 100, 1),
            "surge_risk": risk
        })
    
    return forecast

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "ollama_url": OLLAMA_URL, "model": OLLAMA_MODEL})

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get current port metrics"""
    metrics = get_current_metrics()
    return jsonify(metrics)

@app.route('/api/forecast', methods=['GET'])
def get_forecast():
    """Get 24-hour forecast"""
    forecast = get_hourly_forecast()
    return jsonify({"forecast": forecast})

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Chat endpoint that forwards queries to Ollama
    Expects JSON: {"message": "your question here"}
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        # Get current metrics to include as context
        metrics = get_current_metrics()
        forecast = get_hourly_forecast()[:6]  # Next 6 hours
        
        # Build context with real-time data
        context = f"""
Current Port Metrics (as of {metrics['timestamp']}):
- Current TEU volume: {metrics['current_teu_per_hour']} TEU/hour
- 30-day baseline: {metrics['baseline_30day_avg']} TEU/hour
- Deviation from baseline: {metrics['percent_deviation']}%
- Surge Risk Level: {metrics['surge_risk']}
- Vessels in channel: {metrics['vessels_in_channel']}
- Vessels at berth: {metrics['vessels_at_berth']}
- Rail cars waiting: {metrics['rail_cars_waiting']}
- Avg dwell time: {metrics['avg_dwell_time_hours']} hours

Next 6-Hour Forecast:
"""
        for f in forecast:
            context += f"  {f['time']}: {f['expected_teu']} TEU, {f['surge_risk']} risk\n"
        
        # Prepare Ollama request
        prompt = f"{SYSTEM_PROMPT}\n\nCurrent Data:\n{context}\n\nUser Question: {user_message}\n\nResponse:"
        
        ollama_payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 500
            }
        }
        
        # Call Ollama API
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=ollama_payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                "response": result.get("response", "No response generated"),
                "metrics": metrics,
                "model": OLLAMA_MODEL
            })
        else:
            return jsonify({
                "error": f"Ollama error: {response.status_code}",
                "details": response.text
            }), 500
            
    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "Cannot connect to Ollama. Make sure it's running.",
            "hint": "Run 'ollama serve' to start the Ollama server"
        }), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/surge-analysis', methods=['GET'])
def surge_analysis():
    """Get detailed surge analysis for the next 24 hours"""
    forecast = get_hourly_forecast()
    metrics = get_current_metrics()
    
    # Analyze surge patterns
    high_risk_hours = [f for f in forecast if f['surge_risk'] == 'HIGH']
    medium_risk_hours = [f for f in forecast if f['surge_risk'] == 'MEDIUM']
    
    analysis = {
        "current_status": {
            "surge_risk": metrics['surge_risk'],
            "teu_per_hour": metrics['current_teu_per_hour'],
            "deviation": metrics['percent_deviation']
        },
        "next_24h_summary": {
            "high_risk_periods": len(high_risk_hours),
            "medium_risk_periods": len(medium_risk_hours),
            "peak_hours": [f['time'] for f in high_risk_hours[:3]],
            "recommended_action": "Increase rail dispatch frequency" if len(high_risk_hours) > 4 else "Normal operations"
        },
        "hourly_breakdown": forecast
    }
    
    return jsonify(analysis)

if __name__ == '__main__':
    print(f"Starting API server...")
    print(f"Ollama URL: {OLLAMA_URL}")
    print(f"Model: {OLLAMA_MODEL}")
    print(f"Endpoints:")
    print(f"  GET  /api/health - Health check")
    print(f"  GET  /api/metrics - Current port metrics")
    print(f"  GET  /api/forecast - 24-hour forecast")
    print(f"  GET  /api/surge-analysis - Detailed surge analysis")
    print(f"  POST /api/chat - Chat with AI (send JSON: {{\"message\": \"your question\"}})")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
