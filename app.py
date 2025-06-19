import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from utils.black_scholes import black_scholes_price
from scipy.stats import norm

st.set_page_config(page_title="Options Dashboard", layout="wide")
st.title("📈 Options Analytics Dashboard")
st.markdown("""
Explorez l'analyse d'options avec des visualisations interactives :
- Surface de volatilité implicite
- Heatmap de prix (Call / Put)
- Visualiseur de payoff simple
- Stratégies combinées et Greeks dynamiques
""")

menu = st.sidebar.radio("📊 Choisir un module :", [
    "🔷 Surface de Volatilité",
    "🌈 Heatmap Prix Call/Put",
    "📊 Visualiseur de Payoff",
    "♻️ Stratégies Combinées",
    "📋 À propos / Aide"
])

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
    df_call = pd.DataFrame(call_prices, index=np.round(vol_range, 2), columns=np.round(spot_range, 2))
    st.dataframe(df_call)
    st.subheader("📉 Prix Put")
    df_put = pd.DataFrame(put_prices, index=np.round(vol_range, 2), columns=np.round(spot_range, 2))
    st.dataframe(df_put)
    st.download_button("📥 Télécharger les prix Call (CSV)", data=df_call.to_csv(index=False), file_name="call_prices.csv", mime="text/csv")
    st.download_button("📥 Télécharger les prix Put (CSV)", data=df_put.to_csv(index=False), file_name="put_prices.csv", mime="text/csv")

elif menu == "📊 Visualiseur de Payoff":
    st.header("📊 Visualiseur de Payoff – Call / Put")
    option_type = st.selectbox("Type d’option", ["Call", "Put"])
    K = st.slider("🎯 Strike", 50, 150, 100)
    premium = st.slider("💸 Prime (prix payé)", 0.0, 50.0, 10.0)
    prices = np.linspace(40, 160, 200)
    payoff = np.maximum(prices - K, 0) - premium if option_type == "Call" else np.maximum(K - prices, 0) - premium
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=prices, y=payoff, mode='lines', name='Payoff'))
    fig.update_layout(title="Profil de payoff", xaxis_title="Prix à maturité", yaxis_title="Profit / Perte")
    st.plotly_chart(fig, use_container_width=True)

elif menu == "♻️ Stratégies Combinées":
    st.header("♻️ Simulateur de stratégies combinées")
    strategy = st.selectbox("Choisir une stratégie :", ["Straddle", "Strangle", "Bull Call Spread", "Bear Put Spread"])
    S = st.slider("💰 Spot Price", 50, 150, 100)
    r = st.slider("🏦 Taux sans risque", 0.0, 0.2, 0.01)
    T = st.slider("⏳ Maturité (années)", 0.01, 2.0, 1.0)
    sigma = st.slider("📈 Volatilité implicite", 0.05, 1.0, 0.2)
    K1 = st.slider("Strike 1", 50, 150, 90)
    K2 = st.slider("Strike 2 (si applicable)", 50, 150, 110)
    prices = np.linspace(40, 160, 300)

    def compute_payoff(price):
        if strategy == "Straddle":
            return np.maximum(price - K1, 0) + np.maximum(K1 - price, 0) - 2 * black_scholes_price(S, K1, T, r, sigma, 'call')
        elif strategy == "Strangle":
            return (np.maximum(price - K2, 0) + np.maximum(K1 - price, 0) -
                    black_scholes_price(S, K1, T, r, sigma, 'put') -
                    black_scholes_price(S, K2, T, r, sigma, 'call'))
        elif strategy == "Bull Call Spread":
            return np.maximum(price - K1, 0) - np.maximum(price - K2, 0) - \
                (black_scholes_price(S, K1, T, r, sigma, 'call') - black_scholes_price(S, K2, T, r, sigma, 'call'))
        elif strategy == "Bear Put Spread":
            return np.maximum(K2 - price, 0) - np.maximum(K1 - price, 0) - \
                (black_scholes_price(S, K2, T, r, sigma, 'put') - black_scholes_price(S, K1, T, r, sigma, 'put'))
        return np.zeros_like(price)

    total_payoff = compute_payoff(prices)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=prices, y=total_payoff, mode='lines', name='Total Payoff'))
    fig.update_layout(title=f"Payoff de la stratégie : {strategy}", xaxis_title="Prix à maturité", yaxis_title="Profit / Perte")
    st.plotly_chart(fig, use_container_width=True)

elif menu == "❓ À propos / Aide":
    st.header("❓ À propos de cette application")
    st.markdown("""
Cette application permet d'explorer le pricing des options avec des outils interactifs pédagogiques :

### 📈 Modules disponibles :
- **Surface de volatilité** : Vue 3D des IV selon le moneyness et l'échéance
- **Heatmap prix d'options** : Affiche les prix Call/Put selon spot & volatilité
- **Visualiseur de payoff** : Simule le payoff net d'un Call ou Put acheté
- **Stratégies combinées** : Visualise les profils de gain de stratégies comme le straddle ou le spread

### ⚙️ Méthode utilisée :
- Modèle Black-Scholes-Merton pour les options européennes
- Les paramètres sont : 
    - `Spot` = prix actuel de l'actif sous-jacent
    - `Strike` = prix d'exercice de l'option
    - `T` = temps restant jusqu’à l’échéance (en années)
    - `r` = taux sans risque
    - `σ` = volatilité implicite (ou estimée)

### 🧮 Formules :
$$
C = S\Phi(d_1) - Ke^{-rT}\Phi(d_2) \\
P = Ke^{-rT}\Phi(-d_2) - S\Phi(-d_1)
$$

Avec :
$$
d_1 = \frac{\ln(S/K) + (r + \sigma^2/2)T}{\sigma \sqrt{T}} \\
d_2 = d_1 - \sigma \sqrt{T}
$$

Tu peux maintenant explorer librement les options financières 😉
    """)

st.markdown("---")
st.caption("Développé par Théo – Projet pédagogique options 🧠")