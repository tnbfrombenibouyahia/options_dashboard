import streamlit as st
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

from utils.yf_data import get_option_chain, list_expirations
from utils.visuals import plot_iv_smile, plot_option_price_heatmap

st.set_page_config(page_title="Options Dashboard", layout="wide")
st.title("Δ Options Analytics Dashboard")

col1, col2 = st.columns([1, 1])

with col1:
    ticker = st.text_input("Ticker (ex: AAPL, GOOGL, TSLA, AMZN, NVDA, MSFT, SPY and more...)", value="AAPL")

with col2:
    if ticker:
        expirations = list_expirations(ticker)
        selected_exp_str = st.selectbox("Choisis une date d'échéance", expirations)
    else:
        selected_exp_str = None

if selected_exp_str:

    if selected_exp_str:
        chain = get_option_chain(ticker, selected_exp_str)
        spot = float(yf.Ticker(ticker).history(period="1d")["Close"].iloc[-1])

        if chain is not None:
            calls = chain.calls.dropna(subset=["strike", "impliedVolatility", "lastPrice"])
            puts = chain.puts.dropna(subset=["strike", "impliedVolatility", "lastPrice"])

            iv_mean = calls["impliedVolatility"].mean()
            atm_strike = calls.iloc[(calls['strike'] - spot).abs().argsort()].iloc[0]['strike']

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                with st.container(border=True):
                    st.metric("\U0001F4C9 Spot", f"${spot:.2f}")
            with col2:
                with st.container(border=True):
                    st.metric("\U0001F4CA IV moyenne (Calls)", f"{iv_mean:.2%}")
            with col3:
                with st.container(border=True):
                    st.metric("\U0001F4CE Nombre de strikes", f"{len(chain.calls)}")
            with col4:
                with st.container(border=True):
                    st.metric("\U0001F3AF Strike ATM", f"{atm_strike:.1f}")

            st.subheader("Smile de Volatilité Implicite")
            fig = plot_iv_smile(chain)
            st.plotly_chart(fig, use_container_width=True)

            # Analyse automatique du smile
            call_min, call_max = calls['impliedVolatility'].min(), calls['impliedVolatility'].max()
            put_min, put_max = puts['impliedVolatility'].min(), puts['impliedVolatility'].max()

            skew_call = "croissante (skew baissier)" if call_max > call_min else "décroissante (skew haussier)"
            skew_put = "croissante (skew baissier)" if put_max > put_min else "décroissante (skew haussier)"

            with st.expander("✨ Analyse automatique du Smile -  Click to open", expanded=False):
                st.markdown("""
                - Les **Calls** ont une vol. *{}*, allant de **{:.2%}** à **{:.2%}**.  
                - Les **Puts** ont une vol. *{}*, allant de **{:.2%}** à **{:.2%}**.

                > Cela suggère que le marché anticipe une {} pour les Calls,  
                > et une {} pour les Puts. Ces asymétries peuvent révéler des biais directionnels dans les anticipations du marché.
                """.format(
                    skew_call, call_min, call_max,
                    skew_put, put_min, put_max,
                    "plus forte probabilité de décote violente (protection à la baisse demandée)" if "croissante" in skew_call else "anticipation modérée de hausse",
                    "forte demande de protection contre les hausses" if "croissante" in skew_put else "biais baissier implicite"
                ))

            st.markdown("---")

            colL, colR = st.columns(2)
            with colL:
                st.subheader("Heatmap des Prix d'Options Call")
                fig_heatmap_call = plot_option_price_heatmap(calls, option_type='call')
                st.plotly_chart(fig_heatmap_call, use_container_width=True)
            with colR:
                st.subheader("Heatmap des Prix d'Options Put")
                fig_heatmap_put = plot_option_price_heatmap(puts, option_type='put')
                st.plotly_chart(fig_heatmap_put, use_container_width=True)
            
            with st.expander("🔥 Analyse automatique - Click to open", expanded=False):
                st.markdown(f"""
                Les **heatmaps ci-dessus représentent la répartition des prix des options Call et Put** en fonction des strikes disponibles à l’échéance sélectionnée.

                - On observe que **les primes Call les plus élevées** se concentrent sur les strikes autour de **{calls['strike'][calls['lastPrice'].idxmax()]:.0f}**, avec une prime maximale de **${calls['lastPrice'].max():.2f}**.
                - Côté Put, le pic de prime est situé autour de **{puts['strike'][puts['lastPrice'].idxmax()]:.0f}**, avec un maximum de **${puts['lastPrice'].max():.2f}**.

                Cela peut indiquer une **anticipation de mouvement important** ou une **forte demande de couverture** sur ces niveaux spécifiques.

                - Les **Calls OTM (out-of-the-money)** sont moins demandés (primes faibles), sauf sur des strikes populaires (niveaux ronds ou tech).
                - Les **Puts ITM** (in-the-money) montrent souvent une prime élevée, signalant une protection recherchée en cas de correction.

                > **Conclusion :** Ces zones de concentration des primes peuvent refléter :
                > - Des zones de **support/résistance implicites**.
                > - Une **peur de forte variation du sous-jacent**.
                > - Une opportunité pour structurer des stratégies comme le Strangle, le Straddle ou les Spreads.

                Une analyse dynamique de ces cartes permet ainsi d’anticiper les points de tension ou d’intérêt du marché sur cette échéance.
                """)

            st.markdown("---")

            st.subheader("Visualiseur de Payoff")

            strategies = [
                "Long Call", "Long Put", "Short Call", "Short Put",
                "Bull Call Spread", "Strangle", "Covered Call",
                "Bear Call Spread", "Bear Put Spread", "Bull Put Spread"
            ]

            strategy = st.selectbox("Strat\u00e9gie", strategies)
            quantity = st.slider("Quantit\u00e9 de contrats", 1, 10, 1)
            x = np.linspace(spot * 0.5, spot * 1.5, 200)
            payoff = np.zeros_like(x)

            def get_price(option_df, strike):
                return option_df[option_df['strike'] == strike]['lastPrice'].values[0]

            available_call_strikes = sorted(calls['strike'].unique())
            available_put_strikes = sorted(puts['strike'].unique())

            if strategy == "Bull Call Spread":
                strike_long = st.select_slider("Strike Long Call", options=available_call_strikes, value=available_call_strikes[0])
                strike_short = st.select_slider("Strike Short Call", options=available_call_strikes, value=available_call_strikes[-1])
                premium_long = get_price(calls, strike_long)
                premium_short = get_price(calls, strike_short)
                premium = premium_long - premium_short
                payoff = quantity * ((np.maximum(x - strike_long, 0) - premium_long) - (np.maximum(x - strike_short, 0) - premium_short))
                breakeven = strike_long + premium

            elif strategy == "Strangle":
                strike_call = st.select_slider("Strike Call (achat)", options=available_call_strikes)
                strike_put = st.select_slider("Strike Put (achat)", options=available_put_strikes)
                premium_call = get_price(calls, strike_call)
                premium_put = get_price(puts, strike_put)
                premium = premium_call + premium_put
                payoff = quantity * ((np.maximum(x - strike_call, 0) + np.maximum(strike_put - x, 0)) - premium)
                breakeven = (strike_put - premium, strike_call + premium)

            elif strategy == "Covered Call":
                strike_call = st.select_slider("Strike Call (vente)", options=available_call_strikes)
                premium = get_price(calls, strike_call)
                payoff = quantity * ((x - spot) + (premium - np.maximum(x - strike_call, 0)))
                breakeven = spot - premium

            elif strategy == "Bear Call Spread":
                strike_short = st.select_slider("Strike Call (vente)", options=available_call_strikes)
                strike_long = st.select_slider("Strike Call (achat)", options=available_call_strikes)
                premium_short = get_price(calls, strike_short)
                premium_long = get_price(calls, strike_long)
                premium = premium_short - premium_long
                payoff = quantity * ((premium_short - np.maximum(x - strike_short, 0)) - (np.maximum(x - strike_long, 0) - premium_long))
                breakeven = strike_short + premium

            elif strategy == "Bear Put Spread":
                strike_long = st.select_slider("Strike Put (achat)", options=available_put_strikes)
                strike_short = st.select_slider("Strike Put (vente)", options=available_put_strikes)
                premium_long = get_price(puts, strike_long)
                premium_short = get_price(puts, strike_short)
                premium = premium_long - premium_short
                payoff = quantity * ((np.maximum(strike_long - x, 0) - premium_long) - (np.maximum(strike_short - x, 0) - premium_short))
                breakeven = strike_long - premium

            elif strategy == "Bull Put Spread":
                strike_short = st.select_slider("Strike Put (vente)", options=available_put_strikes)
                strike_long = st.select_slider("Strike Put (achat)", options=available_put_strikes)
                premium_short = get_price(puts, strike_short)
                premium_long = get_price(puts, strike_long)
                premium = premium_short - premium_long
                payoff = quantity * ((premium_short - np.maximum(strike_short - x, 0)) - (np.maximum(strike_long - x, 0) - premium_long))
                breakeven = strike_short - premium

            else:
                strikes_df = calls if "Call" in strategy else puts
                available_strikes = sorted(strikes_df['strike'].unique())
                strike = st.select_slider("Strike", options=available_strikes, value=available_strikes[len(available_strikes)//2])
                premium = get_price(strikes_df, strike)

                if strategy == "Long Call":
                    payoff = quantity * (np.maximum(x - strike, 0) - premium)
                    breakeven = strike + premium
                elif strategy == "Short Call":
                    payoff = quantity * (premium - np.maximum(x - strike, 0))
                    breakeven = strike + premium
                elif strategy == "Long Put":
                    payoff = quantity * (np.maximum(strike - x, 0) - premium)
                    breakeven = strike - premium
                elif strategy == "Short Put":
                    payoff = quantity * (premium - np.maximum(strike - x, 0))
                    breakeven = strike - premium

            pnl_max = np.max(payoff)
            pnl_min = np.min(payoff)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x, y=payoff, fill='tozeroy', mode='lines'))
            fig.update_layout(title="Payoff \u00e0 l'\u00e9ch\u00e9ance", xaxis_title="Prix du sous-jacent", yaxis_title="Profit / Perte ($)")
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("📊 Analyse automatique du Payoff - Click to open", expanded=False):
                direction = "haussière" if "Call" in strategy or "Bull" in strategy else "baissière"
                sens = "hausse" if "Call" in strategy or "Bull" in strategy else "baisse"
                position = "acheteur" if "Long" in strategy else "vendeur"
                risque_limité = "Oui" if "Long" in strategy or "Spread" in strategy else "Non"
                gain_limité = "Oui" if "Spread" in strategy or "Short" in strategy else "Non"

                # Ligne strike dynamique
                if strategy in ["Long Call", "Short Call", "Long Put", "Short Put"]:
                    ligne_strike = f"- **Strike :** `${strike:.2f}` | **Prime payée :** `${premium:.2f}`"
                elif strategy == "Strangle":
                    ligne_strike = f"- **Strikes :** Call = `${strike_call:.2f}`, Put = `${strike_put:.2f}` | **Prime totale :** `${premium:.2f}`"
                elif strategy == "Covered Call":
                    ligne_strike = f"- **Strike du Call vendu :** `${strike_call:.2f}` | **Prime reçue :** `${premium:.2f}`"
                elif strategy == "Bull Call Spread":
                    ligne_strike = f"- **Strikes :** Long = `${strike_long:.2f}`, Short = `${strike_short:.2f}` | **Prime nette :** `${premium:.2f}`"
                elif strategy == "Bear Call Spread":
                    ligne_strike = f"- **Strikes :** Short = `${strike_short:.2f}`, Long = `${strike_long:.2f}` | **Prime nette :** `${premium:.2f}`"
                elif strategy == "Bear Put Spread":
                    ligne_strike = f"- **Strikes :** Long = `${strike_long:.2f}`, Short = `${strike_short:.2f}` | **Prime nette :** `${premium:.2f}`"
                elif strategy == "Bull Put Spread":
                    ligne_strike = f"- **Strikes :** Short = `${strike_short:.2f}`, Long = `${strike_long:.2f}` | **Prime nette :** `${premium:.2f}`"
                else:
                    ligne_strike = ""

                st.markdown(f"""
                - **Stratégie sélectionnée :** `{strategy}` sur {quantity} contrat(s)  
                - **Direction anticipée :** `{direction}` (profite d'une {sens} du sous-jacent)  
                {ligne_strike}  
                - **Seuil de rentabilité (break-even) :** `{breakeven}`

                **Analyse du profil de risque :**

                - **Perte maximale :** `${pnl_min:.2f}`  
                - **Gain potentiel max :** `${pnl_max:.2f}`  
                - **Risque limité ?** `{risque_limité}` | **Gain limité ?** `{gain_limité}`

                > 👉 Cette stratégie est adaptée si tu anticipes une **forte {sens}** d'ici l’échéance.  
                > Le payoff est **{('illimité' if pnl_max > 1e5 else 'limité')}** tandis que la perte est **{('limitée à la prime' if pnl_min < 0 else 'potentiellement élevée')}**.  
                > Le break-even te donne un repère : en dessous, tu perds, au-dessus, tu gagnes.
                """)

            colA, colB, colC, colD = st.columns(4)
            with colA:
                with st.container(border=True):
                    if isinstance(breakeven, tuple):
                        st.metric("\U0001F3AF Break-even", f"${breakeven[0]:.2f} / ${breakeven[1]:.2f}")
                    else:
                        st.metric("\U0001F3AF Break-even", f"${breakeven:.2f}")
            with colB:
                with st.container(border=True):
                    st.metric("\U0001F4B0 PnL Max", f"${pnl_max:.2f}")
            with colC:
                with st.container(border=True):
                    st.metric("\U0001F53B PnL Min", f"${pnl_min:.2f}")
            with colD:
                with st.container(border=True):
                    st.metric("\U0001F4B5 Prime r\u00e9elle", f"${premium:.2f}")

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; padding-top: 20px; font-size: 0.9em; color: gray;'>
        made by tnb</strong><br>
        <a href="https://github.com/tnbfrombenibouyahia" target="_blank">🔗 GitHub</a> | 
        <a href="https://www.linkedin.com/in/th%C3%A9o-na%C3%AFm-benhellal-56bb6218a/" target="_blank">💼 LinkedIn</a>
    </div>
    """,
    unsafe_allow_html=True
)