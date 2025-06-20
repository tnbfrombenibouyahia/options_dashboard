import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from utils.black_scholes import black_scholes_price
from scipy.stats import norm
from streamlit_option_menu import option_menu

st.set_page_config(page_title="Options Dashboard", layout="wide")
st.title("📈 Options Analytics Dashboard")


menu = option_menu(
    menu_title=None,
    options = [
    "💥 Surface de Volatilité",
    "🌡️ Heatmap Prix Call/Put",
    "👁️ Visualiseur de Payoff",
    "🤹‍♂️ Stratégies Combinées",
    "🧮 Greeks – Valeurs et Heatmap",
    "📡 Données Réelles (yfinance)",
    "🕵️ À propos / Aide"
],
    orientation="horizontal"
)

if menu == "📡 Données Réelles (yfinance)":
    st.header("📡 Données d'Options Réelles via yfinance")

    symbol = st.text_input("Ticker (ex: SPY, AAPL)", value="SPY")
    ticker = yf.Ticker(symbol)

    try:
        expirations = ticker.options
        selected_exp = st.selectbox("Choisir une échéance", expirations)
        chain = ticker.option_chain(selected_exp)

        calls = chain.calls.copy()
        puts = chain.puts.copy()

        st.subheader("📈 Options Call disponibles")
        st.dataframe(calls[['contractSymbol', 'strike', 'lastPrice', 'impliedVolatility', 'openInterest']])

        st.subheader("📉 Options Put disponibles")
        st.dataframe(puts[['contractSymbol', 'strike', 'lastPrice', 'impliedVolatility', 'openInterest']])

        spot_price = ticker.history(period="1d")['Close'].iloc[-1]
        r = 0.01
        maturity_years = (pd.to_datetime(selected_exp) - pd.Timestamp.today()).days / 365.0

        # SMILE IV CALLS
        df_smile_calls = calls[['strike', 'impliedVolatility']].dropna().sort_values('strike')
        fig_smile_calls = go.Figure()
        fig_smile_calls.add_trace(go.Scatter(
            x=df_smile_calls['strike'],
            y=df_smile_calls['impliedVolatility'] * 100,
            mode='lines+markers',
            name='IV Call (%)',
            line=dict(color='orange')
        ))
        fig_smile_calls.update_layout(
            title="Smile IV – Calls", xaxis_title="Strike", yaxis_title="IV (%)",
            template="plotly_white", height=400
        )

        # SMILE IV PUTS
        df_smile_puts = puts[['strike', 'impliedVolatility']].dropna().sort_values('strike')
        fig_smile_puts = go.Figure()
        fig_smile_puts.add_trace(go.Scatter(
            x=df_smile_puts['strike'],
            y=df_smile_puts['impliedVolatility'] * 100,
            mode='lines+markers',
            name='IV Put (%)',
            line=dict(color='green')
        ))
        fig_smile_puts.update_layout(
            title="Smile IV – Puts", xaxis_title="Strike", yaxis_title="IV (%)",
            template="plotly_white", height=400
        )

        # COMPARAISON BSM CALLS
        call_comp = calls[['strike', 'lastPrice', 'impliedVolatility']].dropna().copy()
        call_comp['BSM'] = call_comp.apply(
            lambda row: black_scholes_price(spot_price, row['strike'], maturity_years, r, row['impliedVolatility'], 'call'), axis=1
        )
        fig_comp_calls = go.Figure()
        fig_comp_calls.add_trace(go.Scatter(x=call_comp['strike'], y=call_comp['lastPrice'], mode='lines+markers', name='Marché'))
        fig_comp_calls.add_trace(go.Scatter(x=call_comp['strike'], y=call_comp['BSM'], mode='lines+markers', name='BSM'))
        fig_comp_calls.update_layout(
            title="Prix Marché vs. BSM – Calls", xaxis_title="Strike", yaxis_title="Prix",
            template="plotly_white", height=400
        )

        # COMPARAISON BSM PUTS
        put_comp = puts[['strike', 'lastPrice', 'impliedVolatility']].dropna().copy()
        put_comp['BSM'] = put_comp.apply(
            lambda row: black_scholes_price(spot_price, row['strike'], maturity_years, r, row['impliedVolatility'], 'put'), axis=1
        )
        fig_comp_puts = go.Figure()
        fig_comp_puts.add_trace(go.Scatter(x=put_comp['strike'], y=put_comp['lastPrice'], mode='lines+markers', name='Marché'))
        fig_comp_puts.add_trace(go.Scatter(x=put_comp['strike'], y=put_comp['BSM'], mode='lines+markers', name='BSM'))
        fig_comp_puts.update_layout(
            title="Prix Marché vs. BSM – Puts", xaxis_title="Strike", yaxis_title="Prix",
            template="plotly_white", height=400
        )

        # --- AFFICHAGE EN GRILLE 2x2 ---
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_smile_calls, use_container_width=True)
        with col2:
            st.plotly_chart(fig_smile_puts, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            st.plotly_chart(fig_comp_calls, use_container_width=True)
        with col4:
            st.plotly_chart(fig_comp_puts, use_container_width=True)

    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")

# Ajout des fonctions Greeks

def black_scholes_greeks(S, K, T, r, sigma, option_type="call"):
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    delta = norm.cdf(d1) if option_type == "call" else -norm.cdf(-d1)
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    vega = S * norm.pdf(d1) * np.sqrt(T)
    theta = (
        -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
        - r * K * np.exp(-r * T) * norm.cdf(d2 if option_type == "call" else -d2)
    )
    return delta, gamma, vega / 100, theta / 365

# --- MODULE GREKS ---
if menu == "📐 Greeks – Valeurs et Heatmap":
    st.header("📐 Analyse des Greeks : Delta, Gamma, Vega, Theta")
    sub_mode = st.radio("Choisir le mode d'analyse :", ["Valeurs instantanées", "Heatmap Delta"])

    if sub_mode == "Valeurs instantanées":
        st.subheader("🧮 Greeks pour une option spécifique")
        opt_type = st.selectbox("Type d’option", ["call", "put"])
        S = st.slider("💰 Spot", 50, 150, 100)
        K = st.slider("🎯 Strike", 50, 150, 100)
        T = st.slider("⏳ Maturité (années)", 0.01, 2.0, 1.0)
        r = st.slider("🏦 Taux sans risque", 0.0, 0.2, 0.01)
        sigma = st.slider("📈 Volatilité", 0.05, 1.0, 0.2)

        delta, gamma, vega, theta = black_scholes_greeks(S, K, T, r, sigma, opt_type)

        st.metric("Delta", f"{delta:.4f}")
        st.metric("Gamma", f"{gamma:.4f}")
        st.metric("Vega (pour 1% vol)", f"{vega:.4f}")
        st.metric("Theta (par jour)", f"{theta:.4f}")

    elif sub_mode == "Heatmap Delta":
        st.subheader("🌈 Heatmap du Delta (option Call)")
        K = st.slider("Strike (fixe)", 80, 120, 100)
        T = st.slider("Maturité (fixe)", 0.01, 2.0, 1.0)
        r = st.slider("Taux sans risque", 0.0, 0.1, 0.01)
        spot_range = np.linspace(70, 130, 30)
        vol_range = np.linspace(0.05, 1.0, 30)

        delta_matrix = np.array([
            [black_scholes_greeks(S, K, T, r, sigma, "call")[0] for S in spot_range]
            for sigma in vol_range
        ])

        df_delta = pd.DataFrame(delta_matrix, index=np.round(vol_range, 2), columns=np.round(spot_range, 2))
        st.dataframe(df_delta.style.background_gradient(cmap="RdYlGn"))
        fig = go.Figure(data=go.Heatmap(
            z=delta_matrix,
            x=np.round(spot_range, 2),
            y=np.round(vol_range, 2),
            colorscale='RdYlGn',
            colorbar=dict(title='Delta')
        ))
        fig.update_layout(title="Heatmap du Delta (option Call)", xaxis_title="Spot", yaxis_title="Volatilité")
        st.plotly_chart(fig, use_container_width=True)

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

# --- MODULE : Stratégies combinées ---
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

st.markdown("""
<p style='text-align: center'>
Développé par Théo Naïm – 
<a href="https://github.com/tnbfrombenibouyahia" target="_blank">GitHub</a> | 
<a href="https://www.linkedin.com/in/th%C3%A9o-na%C3%AFm-benhellal-56bb6218a/" target="_blank">LinkedIn</a>
</p>
""", unsafe_allow_html=True)