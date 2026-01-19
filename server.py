"""
Flask API Server

Exposes simulation capabilities via REST API.
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os

# Add parent to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.simulator import create_simulator, run_water_spraying_analysis
from backend.insights import create_insights_generator
from backend.rankings import create_ranker
from backend.scenarios import get_scenario_list, get_all_scenarios
from backend.policies.base_policy import PolicyRegistry

# Import policies to register them
from backend.policies import delhi_policies, global_policies, experimental_policies


app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)


# ============================================================================
# Static File Serving
# ============================================================================

@app.route("/")
def serve_index():
    """Serve the main application."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    """Serve static files."""
    return send_from_directory(app.static_folder, path)


# ============================================================================
# API Endpoints
# ============================================================================

@app.route("/api/policies", methods=["GET"])
def get_policies():
    """Get list of all available policies."""
    policies = []
    for name, policy in PolicyRegistry.get_all().items():
        meta = policy.get_metadata()
        policies.append({
            "name": meta.name,
            "display_name": meta.display_name,
            "description": meta.description,
            "category": meta.category,
            "effectiveness_rating": meta.effectiveness_rating,
            "delhi_uses": meta.delhi_uses,
            "global_uses": meta.global_uses,
        })
    
    return jsonify({
        "policies": policies,
        "categories": ["delhi", "global", "experimental"],
    })


@app.route("/api/scenarios", methods=["GET"])
def get_scenarios():
    """Get list of pre-defined scenarios."""
    return jsonify({
        "scenarios": get_scenario_list(),
    })


@app.route("/api/simulate", methods=["POST"])
def run_simulation():
    """
    Run a simulation.
    
    Request body:
    {
        "scenario": "scenario_name" OR
        "policies": ["policy1", "policy2"],
        "weather": "default|stagnant|favorable|realistic",
        "days": 30
    }
    """
    data = request.get_json() or {}
    
    simulator = create_simulator()
    
    if "scenario" in data:
        # Run pre-defined scenario
        scenario_name = data["scenario"]
        try:
            result = simulator.run_scenario(scenario_name)
            return jsonify({
                "success": True,
                "result": result.to_dict(),
            })
        except ValueError as e:
            return jsonify({"success": False, "error": str(e)}), 400
    
    elif "policies" in data:
        # Run custom policy combination
        policies = data.get("policies", [])
        weather = data.get("weather", "default")
        days = data.get("days", 30)
        
        result = simulator.run_custom_scenario(policies, weather, min(60, max(7, days)))
        return jsonify({
            "success": True,
            "result": result.to_dict(),
        })
    
    else:
        return jsonify({
            "success": False,
            "error": "Must provide either 'scenario' or 'policies'"
        }), 400


@app.route("/api/compare", methods=["POST"])
def compare_scenarios():
    """
    Compare multiple scenarios.
    
    Request body:
    {
        "scenarios": ["scenario1", "scenario2", ...]
    }
    """
    data = request.get_json() or {}
    scenarios = data.get("scenarios", ["baseline", "delhi_current", "global_best"])
    
    simulator = create_simulator()
    comparison = simulator.compare_scenarios(scenarios)
    
    # Generate insights
    insights_gen = create_insights_generator(simulator)
    insights = insights_gen.generate_comparison_insights(comparison)
    
    return jsonify({
        "success": True,
        "comparison": comparison,
        "insights": insights,
    })


@app.route("/api/report", methods=["GET"])
def generate_report():
    """Generate a full analysis report."""
    simulator = create_simulator()
    insights_gen = create_insights_generator(simulator)
    
    report = insights_gen.generate_full_report()
    
    return jsonify({
        "success": True,
        "report": report,
    })


@app.route("/api/rankings", methods=["GET"])
def get_rankings():
    """Get policy rankings."""
    ranker = create_ranker()
    
    return jsonify({
        "rankings": ranker.get_rankings(),
        "by_category": ranker.get_rankings_by_category(),
        "comparison_matrix": ranker.get_comparison_matrix(),
        "top_recommendations": ranker.get_top_recommendations(5),
    })


@app.route("/api/water-analysis", methods=["GET"])
def get_water_analysis():
    """Get special analysis on water spraying effectiveness."""
    analysis = run_water_spraying_analysis()
    
    # Add deep dive content
    from backend.insights import create_insights_generator
    gen = create_insights_generator()
    deep_dive = gen.generate_water_spraying_deep_dive()
    
    return jsonify({
        "success": True,
        "analysis": analysis,
        "deep_dive": deep_dive,
    })


@app.route("/api/forecast", methods=["POST"])
def forecast_aqi():
    """
    ML-based AQI forecasting.
    
    Request body:
    {
        "current_pm25": 150,
        "current_pm10": 300,
        "wind_speed": 8,
        "temperature": 20,
        "humidity": 60,
        "is_inversion": false,
        "active_policies": ["water_spraying", "odd_even"]
    }
    """
    from backend.ml_forecaster import predict_aqi, get_forecaster
    
    data = request.get_json() or {}
    
    # Get prediction
    result = predict_aqi(
        current_pm25=data.get("current_pm25", 150),
        current_pm10=data.get("current_pm10", 300),
        wind_speed=data.get("wind_speed", 8),
        temperature=data.get("temperature", 20),
        humidity=data.get("humidity", 60),
        is_inversion=data.get("is_inversion", False),
        active_policies=data.get("active_policies", []),
    )
    
    return jsonify({
        "success": True,
        "forecast": result,
    })


@app.route("/api/forecast/model-info", methods=["GET"])
def get_model_info():
    """Get information about the ML model."""
    from backend.ml_forecaster import get_forecaster
    
    forecaster = get_forecaster()
    return jsonify({
        "success": True,
        "model": forecaster.get_model_info(),
    })


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Delhi Pollution Policy Simulator")
    print("=" * 60)
    print(f"Registered policies: {len(PolicyRegistry.get_all())}")
    print(f"Available scenarios: {len(get_all_scenarios())}")
    print("=" * 60)
    print("Starting server at http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host="0.0.0.0", port=5000)
