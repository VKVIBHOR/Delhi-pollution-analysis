# 🌫️ Delhi Pollution Analysis & Policy Simulator

An interactive web app for comparing Delhi's air-pollution control policies under identical conditions. It combines an hourly pollution dynamics engine with a Random Forest forecasting module, policy scenarios, rankings and plain-language insights.

📄 **Policy brief:** *Treating causes, not symptoms: rebalancing Delhi's winter air-quality response* (September 2026) summarises the findings alongside published evidence. <!-- add link to the brief on your portfolio -->

## Features
- 📊 **Policy simulation**: 30-day hourly simulation of PM2.5 and PM10 from source emissions (vehicles, construction, industry, household, regional), weather-driven dispersion and policy effects that build up or fade
- ⚖️ **Fair comparison**: every scenario runs under the same weather sequence
- 🔮 **ML forecasting**: Random Forest models predict next-period PM2.5/PM10, with per-prediction feature importance
- 📈 **Rankings & insights**: policy scores and plain-language explanations
- 🌐 **Interactive dashboard**: Flask API with a JavaScript front end

## Key results (default winter weather, 30 days)

Reduction in average PM2.5 compared with no intervention:

| Scenario | PM2.5 reduction |
|---|---|
| Global best practices (industry controls, pricing, low-emission zones, regional coordination) | 31.9% |
| Hybrid (global + targeted + predictive) | 31.2% |
| Delhi intensive (GRAP IV, construction ban, spraying, odd-even) | 26.8% |
| Delhi current (daily spraying, odd-even, GRAP II) | 15.4% |
| Experimental (targeted emitters, pricing, night truck ban) | 13.8% |
| Water spraying only | 4.3% |

Under stagnant weather (low wind, inversion), average PM2.5 was about 93% *higher* than the normal-weather baseline even with GRAP IV and a construction ban in force: weather can outweigh policy.

## Limitations — please read

This is a **scenario model, not a calibrated forecast**.

- Emission rates and each policy's effect size are **assumptions** informed by published studies (see `backend/config.py`), not values estimated from Delhi monitoring data. The ranking above therefore largely reflects those assumptions. The model's value is in showing, transparently, how measures combine, fade and interact with weather.
- Results should be read as **relative**, not absolute. Baseline concentrations are not calibrated to observed levels.
- The weather sequences are synthetic.
- The forecasting module is trained on **synthetic data** generated from rules in `ml_forecaster.py`. Its high test scores (R² ≈ 0.96) show it learns those rules, not that it predicts real Delhi air quality.
- The night truck ban is modelled as a percentage cut to all vehicle emissions at night, not by vehicle class, so its small simulated effect should not be read as evidence about real truck restrictions.

### Roadmap
1. Calibrate emissions and dispersion with CPCB continuous monitoring (CAAQMS) data
2. Train the forecaster on historical observations instead of synthetic data
3. Model freight and truck restrictions by vehicle class and time of day
4. Add uncertainty ranges to every result

## Installation

```bash
# Clone the repository
git clone https://github.com/VKVIBHOR/Delhi-pollution-analysis.git
cd Delhi-pollution-analysis

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 💻 Usage

```bash
python server.py
```

The server starts at `http://localhost:5000`. Open it in your browser to use the dashboard.

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/policies` | All available policies |
| GET | `/api/scenarios` | Pre-defined scenarios |
| POST | `/api/simulate` | Run a simulation |
| POST | `/api/compare` | Compare multiple scenarios |
| GET | `/api/report` | Full analysis report |
| GET | `/api/rankings` | Policy rankings |
| GET | `/api/water-analysis` | Water spraying vs source-based measures |
| POST | `/api/forecast` | Predict next-period PM2.5/PM10 |
| GET | `/api/forecast/model-info` | ML model information |

### Example: run a simulation

```bash
curl -X POST http://localhost:5000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{"scenario": "delhi_current"}'
```

### Example: forecast

```bash
curl -X POST http://localhost:5000/api/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "current_pm25": 150,
    "current_pm10": 300,
    "wind_speed": 8,
    "temperature": 20,
    "humidity": 60,
    "is_inversion": false,
    "active_policies": ["water_spraying", "odd_even"]
  }'
```

## 🤖 ML Forecasting

Random Forest regression predicts next-period PM2.5 and PM10 using current pollution levels, weather (wind, temperature, humidity, inversion), time features (hour, day of week, month, winter flag) and binary flags for active policies. It returns predicted levels, an AQI category, a confidence score, feature importance and recommendations. It is trained on synthetic data; see Limitations.

## Project structure

```
backend/
  config.py              # Emission rates, weather and policy effect assumptions
  pollution_engine.py    # Hourly PM dynamics: emissions + transport - dispersion - policy effects
  data_layer.py          # Emission sources and weather scenarios
  policies/              # Delhi, global and experimental policy modules
  scenarios.py           # Pre-defined scenarios for fair comparison
  simulator.py           # Runs and compares scenarios
  ml_forecaster.py       # Random Forest forecasting (synthetic training data)
  rankings.py, insights.py
frontend/                # Dashboard (HTML, CSS, JS)
server.py                # Flask API
```

## 🤝 Contributing

Contributions are welcome, especially calibration with real monitoring data. Fork the repo, create a feature branch and open a pull request.

## References
- PIB (Jan 2026): Delhi annual PM2.5/PM10, 2018–2025
- CREA (Jan 2026): *Tracing the Hazy Air 2026*, NCAP progress report
- CEEW (Nov 2025): *Are anti-smog guns the solution to Delhi's air pollution problem?*
- EPIC, University of Chicago: evaluation of Delhi's odd-even scheme (2016)
- CAQM: Graded Response Action Plan (revised Dec 2024)
