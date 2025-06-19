import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from utils.black_scholes import black_scholes_price

# -----------------------------
# CONFIGURATION
# -----------------------------
st.set_page_config(page_title="Options Dashboard", layout="wide")
st.title("📈 Options Analytics Dashboard")
st.markdown("""
Explorez l'analyse d'options avec des visualisations interactives :
- Surface de volatilité implicite
- Heatmap de prix (Call / Put)
- Visualiseur de payoff simple
""")

# -----------------------------
# NAVIGATION
# -----------------------------
menu = st.sidebar.radio("📊 Choisir un module :", [
    "🔷 Surface de Volatilité",
    "🌈 Heatmap Prix Call/Put",
    "📊 Visualiseur de Payoff"
])

# -----------------------------
# MODULE 1 – Volatility Surface
# -----------------------------
if menu == "🔷 Surface de Volatilité":
    st.header("🔷 Surface de Volatilité Implicite (exemple)")

    spot = st.number_input("💰 Spot Price", 50.0, 500.0, 100.0)
    maturities = np.linspace(0.05, 2, 20)
    moneyness = np.linspace(0.8, 1.2, 30)

    vol_surface = np.array([
        [20 + 50 * np.exp(-((m - 1)**2 + (t - 0.3)**2) * 8) for t in maturities]
        for m in moneyness
    ])

    fig = go.Figure(data=[go.Surface(z=vol_surface, x=maturities, y=moneyness, colorscale='Viridis')])
    fig.update_layout(
        title="Volatility Surface (Fake Data)",
        scene=dict(
            xaxis_title='Time to Expiration (years)',
            yaxis_title='Moneyness (Strike / Spot)',
            zaxis_title='Implied Volatility (%)'
        )
    )
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# MODULE 2 – Heatmap Call/Put
# -----------------------------
elif menu == "🌈 Heatmap Prix Call/Put":
    st.header("🌈 Heatmap des Prix d’Options Black-Scholes")

    strike = st.number_input("🎯 Strike", 10.0, 500.0, 100.0)
    T = st.slider("⏳ Maturité (années)", 0.01, 2.0, 1.0)
    r = st.slider("🏦 Taux sans risque", 0.0, 0.2, 0.01)

    spot_range = np.linspace(70, 130, 20)
    vol_range = np.linspace(0.05, 1.0, 20)

    call_prices = np.array([
        [black_scholes_price(S, strike, T, r, vol, "call") for S in spot_range]
        for vol in vol_range
    ])
    put_prices = np.array([
        [black_scholes_price(S, strike, T, r, vol, "put") for S in spot_range]
        for vol in vol_range
    ])

    st.subheader("📈 Prix Call")
    st.dataframe(pd.DataFrame(call_prices, index=np.round(vol_range, 2), columns=np.round(spot_range, 2)))

    st.subheader("📉 Prix Put")
    st.dataframe(pd.DataFrame(put_prices, index=np.round(vol_range, 2), columns=np.round(spot_range, 2)))

# -----------------------------
# MODULE 3 – Payoff Visualizer
# -----------------------------
elif menu == "📊 Visualiseur de Payoff":
    st.header("📊 Visualiseur de Payoff – Call / Put")

    option_type = st.selectbox("Type d’option", ["Call", "Put"])
    K = st.slider("🎯 Strike", 50, 150, 100)
    premium = st.slider("💸 Prime (prix payé)", 0.0, 50.0, 10.0)

    prices = np.linspace(40, 160, 200)
    if option_type == "Call":
        payoff = np.maximum(prices - K, 0) - premium
    else:
        payoff = np.maximum(K - prices, 0) - premium

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=prices, y=payoff, mode='lines', name='Payoff'))
    fig.update_layout(title="Profil de payoff", xaxis_title="Prix à maturité", yaxis_title="Profit / Perte")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("Développé par Théo – Projet pédagogique options 🧠")