# austin-port-to-rail

# plan

direction of ships travel-- 
distance 

NVIDIA CuOPT: https://docs.nvidia.com/cuopt/user-guide/latest/introduction.html#routing-tsp-vrp-and-pdp

Port - To Truck - To Rail 

## Overarching Features

### Surge Prediction
  Search(Major Events)
  Weather(CLI Data)
  Shipment Time vs Exectation Calculation

## Dragage Time(Port to Truck Shipping)
  Visualization(Estimated Shipment Time + Notification

## Unified real-time visualization of freight flow from port to truck to rail
- Integrates port, truck, and rail datasets
- Forecasts congestion and inbound surges
- Identifies rail nodes that are likely to face chokepoints
- Recommends optimal rail movement time windows
- Flags anomalies across port, road, or rail network activity
- Presents a clear dashboard illustrating multimodal flow dynamics_

## Datasets

    ### PortWatch – Daily Port Activity (IMF)
        Metrics: vessel arrivals, departures, cargo volumes, time-in-port
        Purpose: detect port congestion and forecast inbound surges
        Dataset: https://portwatch.imf.org/pages/data-and-methodology
            Were using this data to give us information about the houston port and number of boats

    ### North American Rail Network (USDOT/FRA)
        Rail Lines: https://geodata.bts.gov/datasets/usdot::north-american-rail-network-lines/about 
        Rail Nodes: https://data-usdot.opendata.arcgis.com/datasets/usdot::north-american-rail-network-nodes/about 

    ### County-to-County Truck Travel Times (BTS/ATRI)
        Metrics: median and percentile drayage travel times
        Purpose: detect first-mile cycle-time stress and road-induced delays
        Dataset: https://rosap.ntl.bts.gov/view/dot/85073 

    2d. Logistics Fleet Data (Kaggle)
        Metrics: vehicle-level freight, cost, operational characteristics
        Purpose: model drayage pressure and analyze fleet-level behavior and delays
        Dataset: https://www.kaggle.com/datasets/syednaveed05/logistics-fleet-data/data 


6. Expected Deliverables

- A forecasting model (24–72 hour prediction window)
- An optimization engine for rail utilization and scheduling
- A real-time or simulated dashboard
- Visualizations of port → truck → rail activity


The Scoring Breakdown (100 Points Total)
1. Technical Execution & Completeness (30 Points)
Did they actually build a working, complex system?

15 pts - Completeness: Does the system successfully complete the full data workflow without crashing?
15 pts - Technical Depth: Is there significant engineering "under the hood"? Did they build a complex pipeline (e.g., Simulation, RAG, Fine-Tuning, or Custom Logic) rather than just a simple static dashboard or basic API wrapper?
2. NVIDIA Ecosystem & Spark Utility (30 Points)

Did they leverage the unique hardware and software provided?

15 pts - The Stack: Did they use at least one major NVIDIA library/tool? (e.g., NIMs, RAPIDS, cuOpt, Modulus, NeMo Models). Note: Merely calling GPT-4 via API gets 0 points here.

15 pts - The "Spark Story": Can they articulate why this runs better on a DGX Spark?
Examples: "We used the 128GB Unified Memory to hold the video buffer and the LLM context simultaneously" or "We ran inference locally to ensure privacy/latency."

3. Value & Impact (20 Points)
Is the solution actually useful?

10 pts - Insight Quality: Is the insight non-obvious and valuable? (e.g., "Traffic jams happen at 5 PM" is obvious. "Rain causes specific stalls on this specific ramp" is valuable).

10 pts - Usability: Could a real Fire Chief, City Planner, or Factory Foreman actually use this tool to make a decision tomorrow?

4. The "Frontier" Factor (20 Points)

Did they push the boundaries?

10 pts - Creativity: Did they combine data or models in a novel way? (e.g., Using vision models to "read" traffic maps).

10 pts - Performance: Did they optimize the system for speed or scale? (e.g., "We optimized the simulation to run at 50x real-time speed").



Steps to run:

User Interface: 
`python3 -m http.server 8000`

```bash
python3 -m venv .venv
source .venv/bin/activate 
pip install -r requirements.txt
python indexing.py # index the db and put all the data in chroma, RUN ONCE  
python query.py # run the model with the data
```