# -----------------------------
# Fiber2Go Restricted Access
# -----------------------------

import streamlit as st

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:

    st.title("Data2Go™ Restricted Access")

    st.warning(
        "This Data2Go™ prototype is provided by Fiber2Go Corporation "
        "for demonstration and testing purposes only. "
        "Access is restricted to authorized reviewers and partners."
    )

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == st.secrets["username"] and password == st.secrets["password"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.stop()

import math
import json

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt


st.set_page_config(
    page_title="Data2Go DCII Prototype",
    page_icon="🌐",
    layout="wide"
)


# -----------------------------
# Core calculation functions
# -----------------------------

@dataclass
class ScenarioInputs:
    total_mw: float
    node_count: int
    gas_share: float
    renewable_share: float
    grid_share: float
    bess_hours: float
    ccus_capture_rate: float
    transmission_loss_pct: float
    pue: float
    wue_l_per_kwh: float
    freshwater_share: float
    produced_water_share: float
    desalinated_water_share: float
    fiber_ring_miles: float
    communities_served: int
    broadband_population_served: int
    local_jobs_per_mw: float
    property_tax_per_mw: float
    hurricane_risk: float
    drought_risk: float
    heat_risk: float
    grid_outage_risk: float


def clamp(value, low=0, high=100):
    return max(low, min(high, value))


def annual_energy_mwh(total_mw: float, pue: float) -> float:
    return total_mw * 8760 * pue


def calculate_emissions(inputs: ScenarioInputs) -> Dict[str, float]:
    # Simplified emissions factors in metric tons CO2e/MWh.
    # These are placeholder assumptions for prototype demonstration only.
    gas_factor = 0.40
    grid_factor = 0.38
    renewable_factor = 0.02

    energy = annual_energy_mwh(inputs.total_mw, inputs.pue)

    gas_emissions = energy * inputs.gas_share * gas_factor
    grid_emissions = energy * inputs.grid_share * grid_factor
    renewable_emissions = energy * inputs.renewable_share * renewable_factor

    gross = gas_emissions + grid_emissions + renewable_emissions
    captured = gas_emissions * inputs.ccus_capture_rate

    avoided_loss_mwh = inputs.total_mw * 8760 * inputs.transmission_loss_pct
    avoided_loss_emissions = avoided_loss_mwh * grid_factor

    net = max(0, gross - captured - avoided_loss_emissions)
    carbon_intensity = net / energy if energy else 0

    net_zero_gap = net

    return {
        "Annual Energy (MWh)": energy,
        "Gross Emissions (tCO2e)": gross,
        "Captured CO2 (tCO2e)": captured,
        "Avoided T&D Loss Emissions (tCO2e)": avoided_loss_emissions,
        "Net Emissions (tCO2e)": net,
        "Carbon Intensity (tCO2e/MWh)": carbon_intensity,
        "Net-Zero Gap (tCO2e)": net_zero_gap,
    }


def calculate_water(inputs: ScenarioInputs) -> Dict[str, float]:
    energy_kwh = annual_energy_mwh(inputs.total_mw, inputs.pue) * 1000
    total_liters = energy_kwh * inputs.wue_l_per_kwh
    total_gallons = total_liters * 0.264172

    freshwater_gal = total_gallons * inputs.freshwater_share
    produced_gal = total_gallons * inputs.produced_water_share
    desal_gal = total_gallons * inputs.desalinated_water_share

    freshwater_avoidance = produced_gal + desal_gal

    return {
        "Annual Water Use (gal)": total_gallons,
        "Freshwater Use (gal)": freshwater_gal,
        "Produced Water Reuse (gal)": produced_gal,
        "Desalinated/Alternative Water (gal)": desal_gal,
        "Freshwater Avoided (gal)": freshwater_avoidance,
    }


def calculate_scores(inputs: ScenarioInputs, emissions: Dict[str, float], water: Dict[str, float]) -> Dict[str, float]:
    renewable_score = inputs.renewable_share * 100
    ccus_score = inputs.ccus_capture_rate * 100
    carbon_intensity = emissions["Carbon Intensity (tCO2e/MWh)"]

    net_zero_score = clamp(100 - carbon_intensity * 160)
    power_score = clamp(40 + renewable_score * 0.25 + ccus_score * 0.25 + inputs.bess_hours * 4 - inputs.grid_share * 20)

    water_alt_share = inputs.produced_water_share + inputs.desalinated_water_share
    water_score = clamp(100 - inputs.freshwater_share * 100 + water_alt_share * 40)

    distribution_score = clamp((inputs.node_count / 20) * 100)
    fiber_score = clamp(30 + min(inputs.fiber_ring_miles / 10, 50) + distribution_score * 0.2)

    risk_penalty = (inputs.hurricane_risk + inputs.drought_risk + inputs.heat_risk + inputs.grid_outage_risk) / 4
    resiliency_score = clamp(100 - risk_penalty * 100 + inputs.bess_hours * 5 + distribution_score * 0.25)

    community_score = clamp(
        20
        + min(inputs.communities_served * 5, 35)
        + min(inputs.broadband_population_served / 10000, 20)
        + min(inputs.local_jobs_per_mw * inputs.total_mw / 50, 15)
        + min(inputs.property_tax_per_mw * inputs.total_mw / 1_000_000, 10)
    )

    overall = (
        net_zero_score * 0.25
        + water_score * 0.15
        + resiliency_score * 0.20
        + community_score * 0.20
        + power_score * 0.10
        + fiber_score * 0.10
    )

    return {
        "Net-Zero Score": net_zero_score,
        "Power Architecture Score": power_score,
        "Water Sustainability Score": water_score,
        "Fiber Ring Score": fiber_score,
        "Climate Resiliency Score": resiliency_score,
        "Community Benefit Score": community_score,
        "Overall DCII Fit Score": clamp(overall),
    }


def architecture_recommendation(scores: Dict[str, float], inputs: ScenarioInputs) -> str:
    if scores["Overall DCII Fit Score"] >= 80:
        return "Strong candidate architecture for DCII demonstration: proceed with detailed engineering, partner outreach, and dataset validation."
    if inputs.node_count >= 10 and scores["Community Benefit Score"] >= 70:
        return "Promising distributed architecture: strengthen net-zero modeling, CCUS pathway, and climate-risk validation."
    if scores["Net-Zero Score"] < 60:
        return "Primary weakness is carbon performance: increase renewables, BESS, CCUS capture rate, or verified offsets/removals."
    if scores["Water Sustainability Score"] < 60:
        return "Primary weakness is water: reduce freshwater share through produced water reuse, desalination, recycling, or dry/hybrid cooling."
    return "Moderate fit: refine assumptions and compare against a traditional hyperscale baseline."


def create_default_scenarios(total_mw: float) -> pd.DataFrame:
    rows = [
        {
            "Scenario": "Traditional Hyperscale",
            "Nodes": 1,
            "Gas": 0.10,
            "Renewables": 0.25,
            "Grid": 0.65,
            "BESS Hours": 2,
            "CCUS": 0.00,
            "T&D Loss Avoided": 0.00,
            "PUE": 1.25,
            "WUE": 1.8,
            "Freshwater": 0.75,
            "Produced Water": 0.00,
            "Desal/Alt Water": 0.25,
            "Fiber Miles": 25,
            "Communities": 1,
            "Broadband Pop": 5000,
            "Jobs/MW": 0.30,
            "Tax/MW": 50000,
            "Hurricane": 0.45,
            "Drought": 0.50,
            "Heat": 0.55,
            "Grid Outage": 0.45,
        },
        {
            "Scenario": "Distributed Ring — Gas Hub + CCUS",
            "Nodes": 20,
            "Gas": 0.55,
            "Renewables": 0.35,
            "Grid": 0.10,
            "BESS Hours": 6,
            "CCUS": 0.85,
            "T&D Loss Avoided": 0.04,
            "PUE": 1.18,
            "WUE": 1.2,
            "Freshwater": 0.20,
            "Produced Water": 0.55,
            "Desal/Alt Water": 0.25,
            "Fiber Miles": 600,
            "Communities": 16,
            "Broadband Pop": 250000,
            "Jobs/MW": 0.45,
            "Tax/MW": 70000,
            "Hurricane": 0.35,
            "Drought": 0.40,
            "Heat": 0.45,
            "Grid Outage": 0.25,
        },
        {
            "Scenario": "Hybrid Architecture",
            "Nodes": 5,
            "Gas": 0.30,
            "Renewables": 0.45,
            "Grid": 0.25,
            "BESS Hours": 4,
            "CCUS": 0.55,
            "T&D Loss Avoided": 0.02,
            "PUE": 1.20,
            "WUE": 1.4,
            "Freshwater": 0.40,
            "Produced Water": 0.30,
            "Desal/Alt Water": 0.30,
            "Fiber Miles": 250,
            "Communities": 6,
            "Broadband Pop": 75000,
            "Jobs/MW": 0.38,
            "Tax/MW": 60000,
            "Hurricane": 0.40,
            "Drought": 0.42,
            "Heat": 0.50,
            "Grid Outage": 0.35,
        },
    ]

    df = pd.DataFrame(rows)
    df["Total MW"] = total_mw
    return df


def scenario_to_inputs(row) -> ScenarioInputs:
    return ScenarioInputs(
        total_mw=float(row["Total MW"]),
        node_count=int(row["Nodes"]),
        gas_share=float(row["Gas"]),
        renewable_share=float(row["Renewables"]),
        grid_share=float(row["Grid"]),
        bess_hours=float(row["BESS Hours"]),
        ccus_capture_rate=float(row["CCUS"]),
        transmission_loss_pct=float(row["T&D Loss Avoided"]),
        pue=float(row["PUE"]),
        wue_l_per_kwh=float(row["WUE"]),
        freshwater_share=float(row["Freshwater"]),
        produced_water_share=float(row["Produced Water"]),
        desalinated_water_share=float(row["Desal/Alt Water"]),
        fiber_ring_miles=float(row["Fiber Miles"]),
        communities_served=int(row["Communities"]),
        broadband_population_served=int(row["Broadband Pop"]),
        local_jobs_per_mw=float(row["Jobs/MW"]),
        property_tax_per_mw=float(row["Tax/MW"]),
        hurricane_risk=float(row["Hurricane"]),
        drought_risk=float(row["Drought"]),
        heat_risk=float(row["Heat"]),
        grid_outage_risk=float(row["Grid Outage"]),
    )


# -----------------------------
# UI
# -----------------------------

st.title("Data2Go™ AI Infrastructure Digital Twin Platform")
st.caption("Prototype for DCII: AI infrastructure simulation, digital twin modeling, power-water-fiber optimization, resiliency, and community benefit analysis.")

with st.sidebar:
    st.header("Scenario Builder")

    uploaded_file = st.file_uploader(
        "Load Scenario JSON",
        type=["json"]
    )

    uploaded_data = None
    loaded_inputs = {}

    if uploaded_file is not None:
        uploaded_data = json.load(uploaded_file)
        loaded_inputs = uploaded_data.get("inputs", {})

        st.success("Scenario loaded successfully.")

    total_mw_default = int(loaded_inputs.get("total_mw", 300))

    total_mw = st.slider(
        "Total AI Load (MW)",
        25,
        1500,
        total_mw_default,
        step=25
    )
    node_count_default = int(loaded_inputs.get("node_count", 12))

    node_count = st.slider(
        "Number of Compute Nodes",
        1,
        50,
        node_count_default
    )
hub_options = [
    "Waha / Permian",
    "Agua Dulce / South Texas",
    "Barnett / North Texas",
    "Huntsville / East Texas"
]

selected_hub_default = uploaded_data.get(
    "selected_hub",
    "Waha / Permian"
) if uploaded_data else "Waha / Permian"

selected_hub = st.selectbox(
    "Energy Hub Region",
    hub_options,
    index=hub_options.index(selected_hub_default)
)
    st.subheader("Power Mix")
    gas_share = st.slider("On-site Gas Share", 0, 100, 45) / 100
    renewable_share = st.slider("Renewables Share", 0, 100, 40) / 100
    grid_share = max(0.0, 1.0 - gas_share - renewable_share)
    st.write(f"Calculated Grid Share: **{grid_share:.0%}**")

    bess_hours = st.slider("BESS Duration (hours)", 0, 12, 6)
    ccus_capture_rate = st.slider("CCUS Capture Rate", 0, 95, 80) / 100
    transmission_loss_pct = st.slider("Avoided Transmission & Distribution Losses", 0.0, 8.0, 4.0, step=0.5) / 100

    st.subheader("Efficiency & Water")
    pue = st.slider("PUE", 1.05, 1.80, 1.18, step=0.01)
    wue_l_per_kwh = st.slider("WUE (liters/kWh)", 0.0, 3.0, 1.2, step=0.1)
    freshwater_share = st.slider("Freshwater Share", 0, 100, 20) / 100
    produced_water_share = st.slider("Produced Water Share", 0, 100, 50) / 100
    desalinated_water_share = max(0.0, 1.0 - freshwater_share - produced_water_share)
    st.write(f"Calculated Desalinated/Alternative Water Share: **{desalinated_water_share:.0%}**")

    st.subheader("Fiber & Community")
    fiber_ring_miles = st.slider("Fiber Ring Miles", 0, 1000, 600, step=25)
    communities_served = st.slider("Communities / Counties Served", 1, 50, 16)
    broadband_population_served = st.number_input("Population Benefiting from Broadband Expansion", 0, 2000000, 250000, step=5000)
    local_jobs_per_mw = st.slider("Local Jobs per MW", 0.0, 2.0, 0.45, step=0.05)
    property_tax_per_mw = st.number_input("Annual Local Tax Benefit per MW ($)", 0, 500000, 70000, step=5000)

    st.subheader("Climate Risks")
    hurricane_risk = st.slider("Hurricane Risk", 0, 100, 35) / 100
    drought_risk = st.slider("Drought Risk", 0, 100, 40) / 100
    heat_risk = st.slider("Heat Wave Risk", 0, 100, 45) / 100
    grid_outage_risk = st.slider("Grid Outage Risk", 0, 100, 25) / 100


inputs = ScenarioInputs(
    total_mw=total_mw,
    node_count=node_count,
    gas_share=gas_share,
    renewable_share=renewable_share,
    grid_share=grid_share,
    bess_hours=bess_hours,
    ccus_capture_rate=ccus_capture_rate,
    transmission_loss_pct=transmission_loss_pct,
    pue=pue,
    wue_l_per_kwh=wue_l_per_kwh,
    freshwater_share=freshwater_share,
    produced_water_share=produced_water_share,
    desalinated_water_share=desalinated_water_share,
    fiber_ring_miles=fiber_ring_miles,
    communities_served=communities_served,
    broadband_population_served=broadband_population_served,
    local_jobs_per_mw=local_jobs_per_mw,
    property_tax_per_mw=property_tax_per_mw,
    hurricane_risk=hurricane_risk,
    drought_risk=drought_risk,
    heat_risk=heat_risk,
    grid_outage_risk=grid_outage_risk,
)

emissions = calculate_emissions(inputs)
water = calculate_water(inputs)
scores = calculate_scores(inputs, emissions, water)
recommendation = architecture_recommendation(scores, inputs)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Executive Dashboard",
    "Scenario Comparison",
    "Net-Zero Engine",
    "Resiliency & Community",
    "DCII Summary"
])

with tab1:
    st.subheader("Architecture Summary")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Energy Hub", selected_hub)
    k2.metric("Total AI Load", f"{total_mw:,.0f} MW")
    k3.metric("Compute Nodes", f"{node_count}")
    k4.metric("Overall DCII Fit", f"{scores['Overall DCII Fit Score']:.1f}/100")

    st.info(recommendation)

    score_df = pd.DataFrame({
        "Metric": list(scores.keys()),
        "Score": list(scores.values())
    })

    st.bar_chart(score_df.set_index("Metric"))

    st.subheader("Key Annual Outputs")
    c1, c2, c3 = st.columns(3)
    c1.metric("Net Emissions", f"{emissions['Net Emissions (tCO2e)']:,.0f} tCO₂e")
    c2.metric("Captured CO₂", f"{emissions['Captured CO2 (tCO2e)']:,.0f} tCO₂e")
    c3.metric("Freshwater Avoided", f"{water['Freshwater Avoided (gal)']/1_000_000:,.1f} M gal")

with tab2:
    st.subheader("Centralized vs Distributed vs Hybrid Scenario Comparison")
    base_df = create_default_scenarios(total_mw)

    results = []
    for _, row in base_df.iterrows():
        inp = scenario_to_inputs(row)
        em = calculate_emissions(inp)
        wa = calculate_water(inp)
        sc = calculate_scores(inp, em, wa)
        results.append({
            "Scenario": row["Scenario"],
            "Nodes": row["Nodes"],
            "Net Emissions tCO2e": em["Net Emissions (tCO2e)"],
            "Captured CO2 tCO2e": em["Captured CO2 (tCO2e)"],
            "Freshwater Use gal": wa["Freshwater Use (gal)"],
            "Freshwater Avoided gal": wa["Freshwater Avoided (gal)"],
            "Net-Zero Score": sc["Net-Zero Score"],
            "Resiliency Score": sc["Climate Resiliency Score"],
            "Community Score": sc["Community Benefit Score"],
            "Overall Score": sc["Overall DCII Fit Score"],
        })

    compare_df = pd.DataFrame(results)
    st.dataframe(compare_df, use_container_width=True)

    st.subheader("Overall Score Comparison")
    st.bar_chart(compare_df.set_index("Scenario")[["Overall Score", "Net-Zero Score", "Resiliency Score", "Community Score"]])

with tab3:
    st.subheader("Net-Zero Architecture Engine")
    st.write("This module estimates the annual carbon balance of the selected architecture using simplified prototype assumptions.")

    carbon_df = pd.DataFrame({
        "Component": [
            "Gross Emissions",
            "Captured CO2",
            "Avoided T&D Loss Emissions",
            "Net Emissions / Net-Zero Gap"
        ],
        "tCO2e": [
            emissions["Gross Emissions (tCO2e)"],
            emissions["Captured CO2 (tCO2e)"],
            emissions["Avoided T&D Loss Emissions (tCO2e)"],
            emissions["Net Emissions (tCO2e)"]
        ]
    })
    st.dataframe(carbon_df, use_container_width=True)
    st.bar_chart(carbon_df.set_index("Component"))

    st.markdown("""
    **CCUS pathway modeled:** capture CO₂ from on-site generation, compress it, move it through CO₂ pipeline infrastructure, and inject it into geological formations or use it for EOR where applicable.
    """)

with tab4:
    st.subheader("Climate Resiliency Engine")
    risk_df = pd.DataFrame({
        "Risk": ["Hurricane", "Drought", "Heat Wave", "Grid Outage"],
        "Risk Level": [hurricane_risk, drought_risk, heat_risk, grid_outage_risk]
    })
    st.dataframe(risk_df, use_container_width=True)
    st.bar_chart(risk_df.set_index("Risk"))

    st.subheader("Community Benefit Optimization Engine")
    community_df = pd.DataFrame({
        "Benefit": [
            "Communities Served",
            "Broadband Population Served",
            "Estimated Local Jobs",
            "Estimated Annual Tax Benefits",
            "Freshwater Avoided"
        ],
        "Value": [
            communities_served,
            broadband_population_served,
            local_jobs_per_mw * total_mw,
            property_tax_per_mw * total_mw,
            water["Freshwater Avoided (gal)"]
        ]
    })
    st.dataframe(community_df, use_container_width=True)

with tab5:
    st.subheader("DCII Demonstration Summary")
    summary = f"""
    **Project:** Data2Go™ Net-Zero AI Infrastructure Digital Twin Platform

    **Purpose:** Demonstrate a software platform that enables data center developers, hyperscalers, utilities, and communities to simulate and optimize AI infrastructure architectures before construction.

    **Selected Hub:** {selected_hub}

    **Architecture Tested:** {node_count} distributed compute node(s), {total_mw:,.0f} MW total AI load.

    **Core Innovation:** The platform compares centralized hyperscale, distributed ring, and hybrid architectures across power, water, fiber, carbon capture, climate resiliency, and community benefit dimensions.

    **Net-Zero Strategy:** On-site generation, renewables, BESS, CCUS, avoided transmission losses, and alternative water sources.

    **DCII Relevance:** Lower emissions, lower freshwater consumption, improved resiliency, reduced community impact, and faster evaluation before capital deployment.

    **Prototype Result:** Overall DCII Fit Score = {scores['Overall DCII Fit Score']:.1f}/100.
    """
    st.markdown(summary)

    export = {
        "selected_hub": selected_hub,
        "inputs": inputs.__dict__,
        "emissions": emissions,
        "water": water,
        "scores": scores,
        "recommendation": recommendation,
    }
    st.download_button(
        "Download Scenario JSON",
        data=json.dumps(export, indent=2),
        file_name="data2go_dcii_scenario.json",
        mime="application/json"
    )

st.caption("Prototype only. Assumptions are simplified and should be replaced with validated engineering, utility, GIS, climate, water, and emissions datasets for formal DCII submission.")
