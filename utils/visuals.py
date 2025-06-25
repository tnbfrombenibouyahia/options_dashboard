import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from scipy.stats import norm
from math import log, sqrt, exp

def plot_iv_smile(option_chain):
    calls = option_chain.calls.dropna(subset=['impliedVolatility', 'strike'])
    puts = option_chain.puts.dropna(subset=['impliedVolatility', 'strike'])

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=calls['strike'],
        y=calls['impliedVolatility'],
        mode='lines+markers',
        name='Calls IV'
    ))

    fig.add_trace(go.Scatter(
        x=puts['strike'],
        y=puts['impliedVolatility'],
        mode='lines+markers',
        name='Puts IV'
    ))

    fig.update_layout(
        title='Volatility Smile (Implied Volatility vs Strike)',
        xaxis_title='Strike',
        yaxis_title='Implied Volatility',
        template='plotly_white'
    )

    return fig

def plot_option_price_heatmap(df, option_type='call'):
    df = df.dropna(subset=['impliedVolatility', 'strike', 'lastPrice'])
    heatmap_data = df.pivot_table(index='impliedVolatility', columns='strike', values='lastPrice')
    heatmap_data = heatmap_data.sort_index(ascending=True)

    fig = px.imshow(
        heatmap_data.values,
        labels=dict(x='Strike', y='Implied Volatility', color='Prix'),
        x=heatmap_data.columns,
        y=np.round(heatmap_data.index, 2),
        aspect='auto',
        title=f'Heatmap des Prix {option_type.capitalize()} (Strike vs IV)'
    )

    return fig

def plot_payoff_chart(option_type, direction, strike, premium):
    import numpy as np
    import plotly.graph_objects as go

    prices = np.linspace(strike * 0.5, strike * 1.5, 200)
    
    if option_type == "call":
        intrinsic = np.maximum(prices - strike, 0)
    else:  # put
        intrinsic = np.maximum(strike - prices, 0)

    if direction == "achat":
        payoff = intrinsic - premium
    else:  # vente
        payoff = -intrinsic + premium

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=prices, y=payoff, mode='lines', name='Payoff Net'))
    fig.update_layout(
        title=f"Profil de Payoff - {direction.capitalize()} {option_type.capitalize()} Strike {strike}",
        xaxis_title="Prix à maturité (S_T)",
        yaxis_title="Profit / Perte",
        template="plotly_white",
        shapes=[{
            "type": "line",
            "x0": strike,
            "x1": strike,
            "y0": min(payoff),
            "y1": max(payoff),
            "line": {"color": "gray", "dash": "dot"}
        }]
    )
    return fig

def compute_greeks(df, S, T, r):
    result = []

    for _, row in df.dropna(subset=['strike', 'impliedVolatility']).iterrows():
        K = row['strike']
        sigma = row['impliedVolatility']
        if sigma == 0:
            continue
        d1 = (log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
        d2 = d1 - sigma * sqrt(T)

        delta = norm.cdf(d1)
        gamma = norm.pdf(d1) / (S * sigma * sqrt(T))
        vega = S * norm.pdf(d1) * sqrt(T) / 100
        theta = (-S * norm.pdf(d1) * sigma / (2 * sqrt(T)) - r * K * exp(-r * T) * norm.cdf(d2)) / 365
        rho = K * T * exp(-r * T) * norm.cdf(d2) / 100

        result.append({
            "Strike": K,
            "IV": sigma,
            "Delta": delta,
            "Gamma": gamma,
            "Vega": vega,
            "Theta": theta,
            "Rho": rho
        })

    return pd.DataFrame(result)


def plot_greek_heatmap(df, greek="Delta"):
    df = df.dropna(subset=["Strike", "IV", greek])
    df = df[df["IV"] > 0]

    heatmap_data = df.pivot_table(index="IV", columns="Strike", values=greek)

    fig = px.imshow(
        heatmap_data.values,
        labels=dict(x="Strike", y="IV", color=greek),
        x=heatmap_data.columns,
        y=[round(v, 3) for v in heatmap_data.index],
        aspect="auto",
        title=f"Heatmap du {greek} (Strike vs IV)"
    )

    return fig