"""
Configuration constants for Delhi Pollution Policy Simulator.
All parameters are based on research and can be adjusted for calibration.
"""

# =============================================================================
# TIME SETTINGS
# =============================================================================
HOURS_PER_DAY = 24
DEFAULT_SIMULATION_DAYS = 30

# =============================================================================
# BASELINE EMISSION RATES (µg/m³ per hour contributed to ambient air)
# =============================================================================
EMISSIONS = {
    "vehicles": {
        "pm25": 8.0,   # Cars, trucks, two-wheelers
        "pm10": 12.0,
        "diesel_share": 0.45,  # 45% of vehicle emissions from diesel
    },
    "construction": {
        "pm25": 5.0,
        "pm10": 25.0,  # Construction dust primarily PM10
    },
    "industry": {
        "pm25": 10.0,
        "pm10": 15.0,
    },
    "external": {  # Crop burning, regional pollution
        "pm25": 15.0,  # High during crop burning season
        "pm10": 20.0,
        "controllable": False,  # Delhi can't directly control this
    },
    "domestic": {  # Cooking, heating, waste burning
        "pm25": 4.0,
        "pm10": 6.0,
    },
}

# Total hourly emissions contribution
TOTAL_PM25_EMISSIONS = sum(e["pm25"] for e in EMISSIONS.values())
TOTAL_PM10_EMISSIONS = sum(e["pm10"] for e in EMISSIONS.values())

# =============================================================================
# WEATHER PARAMETERS
# =============================================================================
WEATHER_DEFAULTS = {
    "wind_speed": 8.0,  # km/h (low = worse dispersion)
    "wind_direction": 270,  # degrees (W -> E)
    "temperature": 18,  # °C
    "humidity": 60,  # %
    "inversion": False,  # Temperature inversion traps pollution
}

# Weather impact on dispersion (fraction of PM removed per hour)
DISPERSION_RATES = {
    "base_rate": 0.05,  # 5% natural dispersion per hour
    "wind_factor": 0.01,  # Additional per km/h wind speed
    "inversion_multiplier": 0.3,  # Inversion reduces dispersion by 70%
    "humidity_deposition": 0.005,  # High humidity helps deposition
}

# =============================================================================
# BACKGROUND / BASELINE AQI
# =============================================================================
BASELINE_PM = {
    "pm25": 80.0,  # µg/m³ - Typical Delhi "normal" level
    "pm10": 180.0,
}

# Severe pollution thresholds (GRAP stages)
AQI_THRESHOLDS = {
    "good": {"pm25": 30, "pm10": 50},
    "satisfactory": {"pm25": 60, "pm10": 100},
    "moderate": {"pm25": 90, "pm10": 250},
    "poor": {"pm25": 120, "pm10": 350},
    "very_poor": {"pm25": 250, "pm10": 430},
    "severe": {"pm25": 380, "pm10": 500},
}

# =============================================================================
# POLICY PARAMETERS
# =============================================================================

# Water Spraying Parameters
WATER_SPRAYING = {
    "pm10_reduction": 0.15,  # 15% initial reduction
    "pm25_reduction": 0.05,  # Only 5% for PM2.5 (too fine)
    "decay_hours": 4,  # Effect decays to near-zero in 4 hours
    "water_usage_liters": 50000,  # Per session
    "sessions_per_day": 3,
    "cost_per_session": 15000,  # INR
}

# Odd-Even Scheme
ODD_EVEN = {
    "vehicle_reduction": 0.12,  # 12% of total vehicle emissions
    "compliance_rate": 0.7,  # 70% compliance
    "effective_reduction": 0.084,  # 12% * 70%
}

# Construction Ban
CONSTRUCTION_BAN = {
    "pm25_reduction": 0.20,
    "pm10_reduction": 0.35,
    "economic_impact": "high",  # Job losses
}

# GRAP (Graded Response Action Plan)
GRAP = {
    "stage1": {
        "trigger_pm25": 120,
        "actions": ["water_spraying", "dust_control"],
        "effectiveness": 0.10,
    },
    "stage2": {
        "trigger_pm25": 250,
        "actions": ["construction_ban", "odd_even_advisory"],
        "effectiveness": 0.15,
    },
    "stage3": {
        "trigger_pm25": 350,
        "actions": ["vehicle_restrictions", "industry_shutdown"],
        "effectiveness": 0.25,
    },
    "stage4": {
        "trigger_pm25": 450,
        "actions": ["school_closure", "work_from_home", "emergency_measures"],
        "effectiveness": 0.30,
    },
}

# =============================================================================
# GLOBAL POLICY BENCHMARKS
# =============================================================================
GLOBAL_POLICIES = {
    "source_elimination": {
        "description": "Relocate/close polluting industries",
        "pm25_reduction": 0.50,
        "pm10_reduction": 0.45,
        "sustainability": "permanent",
        "implementation_time": "years",
    },
    "industrial_scrubbers": {
        "description": "Mandate emission control equipment",
        "pm25_reduction": 0.40,
        "pm10_reduction": 0.35,
        "sustainability": "permanent",
        "implementation_time": "months",
    },
    "congestion_pricing": {
        "description": "Dynamic tolls based on AQI",
        "pm25_reduction": 0.25,
        "pm10_reduction": 0.25,
        "sustainability": "sustained",
        "revenue_positive": True,
    },
    "low_emission_zones": {
        "description": "Ban high-polluting vehicles in core areas",
        "pm25_reduction": 0.30,
        "pm10_reduction": 0.28,
        "sustainability": "sustained",
    },
    "regional_coordination": {
        "description": "NCR-wide pollution control",
        "pm25_reduction": 0.35,
        "pm10_reduction": 0.30,
        "affects_external": True,
    },
}

# =============================================================================
# EXPERIMENTAL POLICIES
# =============================================================================
EXPERIMENTAL_POLICIES = {
    "source_weighted": {
        "description": "Target top 20% emitters only",
        "pm25_reduction": 0.40,
        "pm10_reduction": 0.35,
        "cost_efficiency": "high",
    },
    "night_truck_ban": {
        "description": "Ban trucks 10PM - 6AM in city",
        "pm25_reduction": 0.18,
        "pm10_reduction": 0.22,
        "sustainability": "sustained",
    },
    "weather_aware_construction": {
        "description": "Halt construction during inversions",
        "pm25_reduction": 0.15,
        "pm10_reduction": 0.25,
        "sustainability": "sustained",
    },
    "aqi_dynamic_pricing": {
        "description": "Vehicle entry fees based on real-time AQI",
        "pm25_reduction": 0.28,
        "pm10_reduction": 0.26,
        "revenue_positive": True,
    },
    "predictive_triggering": {
        "description": "Act 3-5 days before predicted smog",
        "pm25_reduction": 0.30,
        "pm10_reduction": 0.28,
        "proactive": True,
    },
}

# =============================================================================
# POLICY COMPARISON MATRIX (Hard-coded truth table)
# =============================================================================
POLICY_COMPARISON = {
    "water_spraying": {
        "delhi_uses": True,
        "global_uses": False,
        "effectiveness": "very_low",
        "rating": 1,
    },
    "blanket_bans": {
        "delhi_uses": True,
        "global_uses": "rare",
        "effectiveness": "medium",
        "rating": 3,
    },
    "source_elimination": {
        "delhi_uses": "limited",
        "global_uses": True,
        "effectiveness": "high",
        "rating": 5,
    },
    "economic_penalties": {
        "delhi_uses": "weak",
        "global_uses": True,
        "effectiveness": "high",
        "rating": 5,
    },
    "predictive_triggers": {
        "delhi_uses": False,
        "global_uses": True,
        "effectiveness": "high",
        "rating": 5,
    },
}
