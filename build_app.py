import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

APP = """import streamlit as st

import yfinance as yf
import math
import plotly.graph_objects as go

st.set_page_config(page_title="Alpha Alocação", layout="wide", page_icon="📊")
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
.stApp{background-color:#0F172A;font-family:'Inter',sans-serif;}
[data-testid="stSidebar"]{background-color:#1E293B;border-right:1px solid #334155;}
[data-testid="stSidebar"] *{color:#CBD5E1 !important;}
html,body,[class*="css"],p,span,div{color:#E2E8F0;}
h1{color:#F1F5F9 !important;font-size:1.6rem !important;font-weight:700 !important;}
h2,h3{color:#93C5FD !important;font-weight:600 !important;font-size:1.05rem !important;}
div[data-testid="metric-container"]{background-color:#1E293B;border:1px solid #334155;border-radius:10px;padding:18px 20px;box-shadow:0 2px 8px rgba(0,0,0,0.3);}
div[data-testid="metric-container"]:hover{border-color:#3B82F6;transition:border-color 0.2s ease;}
div[data-testid="stMetricLabel"]>div{color:#94A3B8 !important;font-size:0.82rem;font-weight:500;}
div[data-testid="stMetricValue"]{color:#F1F5F9 !important;font-size:1.5rem !important;font-weight:700;}
.stTabs [data-baseweb="tab-list"]{background-color:#1E293B;border-radius:8px;padding:4px;gap:4px;border:1px solid #334155;}
.stTabs [data-baseweb="tab"]{background-color:transparent;border-radius:6px;color:#94A3B8 !important;font-weight:500;font-size:0.88rem;padding:8px 18px;}
.stTabs [aria-selected="true"]{background-color:#3B82F6 !important;color:#FFFFFF !important;}
.stTabs [data-baseweb="tab-panel"]{padding-top:20px;}
.stTextInput input,.stNumberInput input,.stTextArea textarea{background-color:#1E293B !important;border:1px solid #334155 !important;border-radius:8px !important;color:#F1F5F9 !important;font-size:0.9rem;}
.stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus{border-color:#3B82F6 !important;box-shadow:0 0 0 2px rgba(59,130,246,0.2) !important;}
.stTextInput label,.stNumberInput label,.stTextArea label{color:#94A3B8 !important;font-size:0.82rem;font-weight:500;}
.stButton>button{background-color:#3B82F6;color:#FFFFFF;border:none;border-radius:8px;padding:10px 22px;font-weight:600;font-size:0.88rem;transition:background-color 0.2s ease,transform 0.1s ease;}
.stButton>button:hover{background-color:#2563EB;transform:translateY(-1px);}
.stRadio label{color:#CBD5E1 !important;font-size:0.88rem;}
hr{border-color:#334155 !important;}
[data-testid="stFileUploader"]{background-color:#1E293B;border:1px dashed #334155;border-radius:10px;padding:8px;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-track{background:#0F172A;}
::-webkit-scrollbar-thumb{background:#334155;border-radius:3px;}
::-webkit-scrollbar-thumb:hover{background:#3B82F6;}
</style>''', unsafe_allow_html=True)

st.title("Alpha Alocação")
st.write("Bem-vindo ao sistema de sugestão de alocação!")
"""

with open(r"C:\Users\Felip\OneDrive\Área de Trabalho\Projeto pessoal\Sugestao_Alocacao\alocacaoautomatica.py", "w", encoding="utf-8") as f:
    f.write(APP)
print("done")
