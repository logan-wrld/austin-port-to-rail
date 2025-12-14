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

@app.route('/api/rail-analysis', methods=['GET'])
def rail_analysis():
    """
    Analyze rail nodes with inbound freight forecasts using Ollama.
    Query params: ship_count, forecast_window (hours)
    Returns structured node status data.
    """
    try:
        # Get query parameters
        ship_count = request.args.get('ship_count', 15, type=int)
        forecast_window = request.args.get('forecast_window', 72, type=int)
        
        # Load rail data from CSV files
        import pandas as pd
        
        try:
            nodes_df = pd.read_csv('data/railroad-nodes.csv')
            lines_df = pd.read_csv('data/railroad-lines.csv')
            texas_rail_df = pd.read_csv('data/texas_rail_data.csv', sep='\t', on_bad_lines='skip')
        except Exception as e:
            # Fallback if files not found
            nodes_df = None
            lines_df = None
            texas_rail_df = None
        
        # Build context from rail data
        rail_context = ""
        
        if nodes_df is not None:
            # Get Texas nodes summary
            tx_nodes = nodes_df[nodes_df['STATE'] == 'TX'] if 'STATE' in nodes_df.columns else nodes_df
            node_count = len(tx_nodes)
            passenger_stations = len(tx_nodes[tx_nodes['PASSNGRSTN'].notna()]) if 'PASSNGRSTN' in tx_nodes.columns else 0
            boundary_nodes = len(tx_nodes[tx_nodes['BNDRY'] == 1]) if 'BNDRY' in tx_nodes.columns else 0
            
            rail_context += f"""
Railroad Nodes Summary (Texas):
- Total nodes: {node_count}
- Passenger stations: {passenger_stations}
- Boundary/interchange points: {boundary_nodes}

Sample node data (first 10):
{tx_nodes.head(10).to_string()}
"""
        
        if lines_df is not None:
            # Get Texas rail lines summary
            tx_lines = lines_df[lines_df['STATEAB'] == 'TX'] if 'STATEAB' in lines_df.columns else lines_df
            total_miles = tx_lines['MILES'].sum() if 'MILES' in tx_lines.columns else 0
            
            # Owner breakdown
            if 'RROWNER1' in tx_lines.columns:
                owner_counts = tx_lines['RROWNER1'].value_counts().head(10).to_dict()
            else:
                owner_counts = {}
            
            rail_context += f"""
Railroad Lines Summary (Texas):
- Total track miles: {total_miles:.1f}
- Rail owners: {owner_counts}

Sample line data (first 5):
{tx_lines.head(5).to_string()}
"""
        
        # Ship forecast context - distribute ships across time windows
        ships_per_window = ship_count // 3
        ships_0_24 = ships_per_window + (ship_count % 3)
        ships_24_48 = ships_per_window
        ships_48_72 = ships_per_window
        total_ships = ship_count
        
        forecast_context = f"""
Inbound Ship Forecast ({forecast_window}-hour window):
- 0-24 hours: {ships_0_24} ships
- 24-48 hours: {ships_24_48} ships  
- 48-72 hours: {ships_48_72} ships
- Total inbound: {total_ships} ships

Estimated freight conversion:
- Average TEU per ship: 2,500
- Average weight per TEU: 14,000 kg
- Total expected freight: {total_ships * 2500 * 14000:,.0f} kg over {forecast_window} hours
- Hourly inbound rate: {(total_ships * 2500 * 14000) / forecast_window:,.0f} kg/hour
"""
        
        # Build the analysis prompt
        analysis_prompt = f"""Analyze the following railroad and freight data. Return ONLY structured JSON data, no prose.

{rail_context}

{forecast_context}

For the top 15 rail nodes in Texas (prioritize nodes near Houston/Galveston):
1. Estimate inbound load pressure (kg/hour) based on ship forecast
2. Compare against inferred rail capacity from line density and node connectivity
3. Classify node status as: NORMAL, ELEVATED, STRESSED, or CRITICAL

Return JSON in this exact format:
{{
  "analysis_timestamp": "ISO timestamp",
  "total_inbound_freight_kg_per_hour": number,
  "nodes": [
    {{
      "node_id": "string",
      "location": "city/area name",
      "estimated_load_kg_per_hour": number,
      "capacity_utilization_pct": number,
      "status": "NORMAL|ELEVATED|STRESSED|CRITICAL",
      "connected_lines": number,
      "primary_railroad": "string"
    }}
  ],
  "summary": {{
    "critical_nodes": number,
    "stressed_nodes": number,
    "recommended_actions": ["string"]
  }}
}}"""

        # Call Ollama
        ollama_payload = {
            "model": OLLAMA_MODEL,
            "prompt": analysis_prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.3,
                "num_predict": 2000
            }
        }
        
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=ollama_payload,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            llm_response = result.get("response", "{}")
            
            # Try to parse as JSON
            try:
                analysis_data = json.loads(llm_response)
            except json.JSONDecodeError:
                # If not valid JSON, return raw response
                analysis_data = {"raw_response": llm_response, "parse_error": True}
            
            return jsonify({
                "success": True,
                "analysis": analysis_data,
                "model": OLLAMA_MODEL,
                "ship_count": ship_count,
                "forecast_window": forecast_window
            })
        else:
            return jsonify({
                "error": f"Ollama error: {response.status_code}",
                "details": response.text
            }), 500
            
    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "Cannot connect to Ollama",
            "hint": "Run 'ollama serve' to start the server"
        }), 503
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

# ========== SHIP TRACKING ENDPOINTS ==========

SHIP_TRACKER_FILE = 'data/ship_tracker.json'

def load_ship_tracker():
    """Load ship tracker data from file"""
    try:
        if os.path.exists(SHIP_TRACKER_FILE):
            with open(SHIP_TRACKER_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading ship tracker: {e}")
    return {"vessels": {}, "history": [], "stats": {}}

def save_ship_tracker(data):
    """Save ship tracker data to file"""
    try:
        os.makedirs(os.path.dirname(SHIP_TRACKER_FILE), exist_ok=True)
        with open(SHIP_TRACKER_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving ship tracker: {e}")
        return False

@app.route('/api/ship-tracker', methods=['GET'])
def get_ship_tracker():
    """Get current ship tracking data"""
    data = load_ship_tracker()
    return jsonify(data)

@app.route('/api/ship-tracker', methods=['POST'])
def update_ship_tracker():
    """Update ship tracking data"""
    try:
        new_data = request.get_json()
        if not new_data:
            return jsonify({"error": "No data provided"}), 400
        
        # Merge with existing data or replace
        if new_data.get('merge'):
            existing = load_ship_tracker()
            # Merge vessels
            for mmsi, vessel in new_data.get('vessels', {}).items():
                existing['vessels'][mmsi] = vessel
            # Append history
            existing['history'].extend(new_data.get('history', []))
            # Keep last 1000 history entries
            existing['history'] = existing['history'][-1000:]
            # Update stats
            existing['stats'] = new_data.get('stats', existing.get('stats', {}))
            new_data = existing
        
        if save_ship_tracker(new_data):
            return jsonify({"success": True, "vessels_count": len(new_data.get('vessels', {}))})
        else:
            return jsonify({"error": "Failed to save data"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ship-tracker/vessels', methods=['GET'])
def get_tracked_vessels():
    """Get all tracked vessels with optional status filter"""
    # Always reload from file to get fresh data (no caching)
    data = load_ship_tracker()
    status_filter = request.args.get('status')
    
    vessels = list(data.get('vessels', {}).values())
    
    if status_filter:
        vessels = [v for v in vessels if v.get('status') == status_filter]
    
    return jsonify({"vessels": vessels, "count": len(vessels)})

@app.route('/api/ship-tracker/docked', methods=['GET'])
def get_docked_vessels():
    """Get vessels that are currently docked or unloading"""
    data = load_ship_tracker()
    vessels = list(data.get('vessels', {}).values())
    
    docked = [v for v in vessels if v.get('status') in ['docked', 'unloading']]
    
    return jsonify({
        "docked": docked,
        "count": len(docked),
        "by_terminal": _group_by_terminal(docked)
    })

def _group_by_terminal(vessels):
    """Group vessels by terminal"""
    terminals = {}
    for v in vessels:
        terminal = v.get('terminal', 'Unknown')
        if terminal not in terminals:
            terminals[terminal] = []
        terminals[terminal].append(v)
    return terminals

@app.route('/api/ship-tracker/history', methods=['GET'])
def get_tracker_history():
    """Get vessel status change history"""
    data = load_ship_tracker()
    limit = request.args.get('limit', 50, type=int)
    
    history = data.get('history', [])[-limit:]
    history.reverse()  # Most recent first
    
    return jsonify({"history": history, "count": len(history)})

@app.route('/api/ship-tracker/stats', methods=['GET'])
def get_tracker_stats():
    """Get tracking statistics"""
    data = load_ship_tracker()
    vessels = list(data.get('vessels', {}).values())
    
    stats = {
        "total_tracked": len(vessels),
        "by_status": {},
        "by_terminal": {},
        "last_updated": data.get('stats', {}).get('lastUpdated')
    }
    
    for v in vessels:
        status = v.get('status', 'unknown')
        stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        
        terminal = v.get('terminal')
        if terminal:
            stats['by_terminal'][terminal] = stats['by_terminal'].get(terminal, 0) + 1
    
    return jsonify(stats)

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
    print(f"  GET  /api/rail-analysis - Analyze rail nodes (?ship_count=N&forecast_window=H)")
    print(f"  GET  /api/ship-tracker - Get ship tracking data")
    print(f"  POST /api/ship-tracker - Update ship tracking data")
    print(f"  GET  /api/ship-tracker/docked - Get docked vessels")
    print(f"  GET  /api/ship-tracker/history - Get status change history")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
