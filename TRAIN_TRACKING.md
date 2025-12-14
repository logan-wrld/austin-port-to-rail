# Cargo Train Tracking Integration Guide

## Overview
Cargo train tracking has been integrated into your Port of Houston map. The system tracks **freight/cargo trains** that carry cargo from ships after they unload at port facilities.

## Important Notes

### What This Tracks
- **Cargo/Freight trains only** - Trains that transport cargo from port facilities
- **Positioned on actual rail infrastructure** - Trains appear at real rail node locations from your `railroad-nodes.csv` data
- **Near port facilities** - Trains are prioritized near port terminals where cargo is unloaded

### What This Does NOT Track
- Passenger trains (METRO light rail)
- Trains outside the Houston/Galveston area
- Trains in the ocean (coordinates are validated)

## Available APIs

### Freight Train APIs
- **Status**: No public real-time APIs available
- **Reason**: Union Pacific, BNSF, and other freight railroads don't provide public APIs for real-time train locations
- **Solution**: The system uses simulated cargo trains positioned on actual rail infrastructure nodes from your data files

## How to Use

### On the Map
1. Open `port-of-houston-map.html` in your browser
2. In the "Map Controls" panel, check **"🚂 Show Cargo Trains"**
3. Cargo trains will appear on the map:
   - 🚂 Orange markers = Cargo trains positioned on actual rail infrastructure
   - Trains are located at real rail node coordinates from your data

### API Endpoint
The backend API provides cargo train data at:
```
GET http://localhost:5000/api/trains
```

**Response Example:**
```json
{
  "success": true,
  "trains": [
    {
      "id": "CARGO_1",
      "type": "freight",
      "railroad": "UP",
      "lat": 29.7234,
      "lng": -95.0012,
      "heading": 45.0,
      "speed": 35.5,
      "status": "in_transit",
      "cars": 85,
      "destination": "Dallas",
      "origin_port": "Barbours Cut Container Terminal"
    }
  ],
  "count": 8,
  "timestamp": "2024-01-15T10:30:00",
  "note": "Cargo trains positioned on actual rail infrastructure nodes near port facilities."
}
```

## Features

### Automatic Refresh
- Cargo trains automatically refresh every 30 seconds when the layer is visible
- Click the checkbox again to stop auto-refresh

### Train Information
Click on any train marker to see:
- **Cargo Train Details**: ID, railroad, status, speed, number of cars, destination, origin port

### Integration with Existing Data
- Cargo trains are positioned on actual rail nodes from `railroad-nodes.csv`
- Trains are prioritized near port facilities where cargo is unloaded
- Different railroads (UP, BNSF, TCT, etc.) are represented
- Coordinates are validated to ensure trains don't appear in the ocean

## Current Limitations

1. **Cargo trains are simulated** - Real-time freight train data is not publicly available from railroads
2. **Train movement** - Trains appear at fixed positions (not animated movement along tracks)
3. **No real-time updates** - Train positions are simulated based on rail infrastructure data

## Future Enhancements

Possible improvements:
- Animate train movement along rail lines
- Historical train data visualization
- Integration with Train Watch for crossing status
- Real-time freight train data (if APIs become available from railroads)
- More accurate train positioning based on rail line segments

## Troubleshooting

**No trains showing?**
- Make sure the API server is running: `python api_server.py`
- Check browser console for errors
- Verify the "Show Cargo Trains" checkbox is checked
- Ensure `data/railroad-nodes.csv` exists and has valid data

**Trains appearing in ocean?**
- This should be fixed! The system now validates coordinates
- Trains are positioned on actual rail nodes from your data
- If you still see this, check that `railroad-nodes.csv` has valid Houston-area coordinates

**API errors?**
- The system will fall back to simulated trains using rail node data if the API fails
- Check that `http://localhost:5000/api/trains` is accessible
- Verify that `data/railroad-nodes.csv` and `data/railroad-lines.csv` exist

