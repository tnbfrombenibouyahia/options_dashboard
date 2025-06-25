import yfinance as yf
import streamlit as st

def list_expirations(ticker: str):
    try:
        t = yf.Ticker(ticker)
        return t.options
    except Exception as e:
        st.error(f"Erreur récupération des dates d'échéance : {e}")
        return []

def get_option_chain(ticker: str, exp: str):
    try:
        t = yf.Ticker(ticker)
        return t.option_chain(exp)
    except Exception as e:
        st.error(f"Erreur récupération de la chaîne d'options : {e}")
        return None