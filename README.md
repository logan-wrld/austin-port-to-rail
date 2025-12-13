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