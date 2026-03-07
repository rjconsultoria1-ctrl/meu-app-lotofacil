import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from collections import Counter
import itertools
import os
import random
import threading
import math
import time
import heapq
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO E TRATAMENTO DE LOGIN
# ==========================================
st.set_page_config(page_title="Gerador VIP | SAP", page_icon="💎", layout="wide", initial_sidebar_state="collapsed")

if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "palpite_manual" not in st.session_state: st.session_state["palpite_manual"] = set()
if "df_diamante" not in st.session_state:
    for k in ["df_diamante", "df_frias", "df_geral", "df_reversa"]: st.session_state[k] = pd.DataFrame()

# ==========================================
# 2. CSS MASTER (LAYOUT FIORI BLINDADO)
# ==========================================
st.markdown("""
    <style>
        [data-testid="collapsedControl"] { display: none; }
        .block-container { padding-top: 0rem !important; max-width: 98% !important; }
        
        /* Header SAP */
        .fiori-header { background-color: #354A5F; color: white; padding: 12px 25px; display: flex; justify-content: space-between; align-items: center; position: fixed; top: 0; left: 0; width: 100%; z-index: 9999; box-shadow: 0 2px 8px rgba(0,0,0,0.3); font-family: 'Arial', sans-serif; }
        .header-spacer { margin-top: 70px; }
        
        /* Rankings Estilizados */
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] { background-color: #f0f2f6; border-radius: 4px 4px 0 0; padding: 8px 16px; }
        .stTabs [aria-selected="true"] { background-color: #5C2D91 !important; color: white !important; }

        /* Volante em Grid */
        .volante-grid-wrapper { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; max-width: 320px; margin: 0 auto; padding: 20px; background: #fff; border: 1px solid #ddd; border-radius: 8px; }
        
        /* Bolinhas de Resultado */
        .res-container { display: flex; gap: 6px; flex-wrap: wrap; justify-content: center; padding: 10px; }
        .bolinha-sap { background: #5C2D91; color: white; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 13px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
        
        /* Título Simulador */
        .sim-title { background: #5C2D91; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 8px 8px 0 0; margin-bottom: -1px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. OS 5 MOTORES MATEMÁTICOS (O CÉREBRO)
# ==========================================
ARQUIVO_BASE = "banco_dados.csv"
PASTA_CACHE = "memoria_calculos"

def executar_logica_completa(df_dados, n_dezenas, motor_id):
    """A inteligência real que você solicitou."""
    dezenas_cols = [c for c in df_dados.columns if "Dezena" in c] or df_dados.columns[-15:]
    past_draws = [frozenset(row) for row in df_dados[dezenas_cols].dropna().astype(int).values]
    ultimo_sorteio = past_draws[-1]
    
    # Filtros SAP
    primos, moldura, fibonacci = {2,3,5,7,11,13,17,19,23}, {1,2,3,4,5,6,10,11,15,16,20,21,22,23,24,25}, {1,2,3,5,8,13,21}
    h_diamante, h_frias, h_geral, h_reversa = [], [], [], []

    # Pre-cálculos por Motor
    counts = Counter([n for d in past_draws for n in d])
    if motor_id == 2: # Grafos
        matriz = [[0]*26 for _ in range(26)]
        for d in past_draws:
            l = list(d)
            for i, j in itertools.combinations(l, 2): matriz[i][j] += 1; matriz[j][i] += 1
    elif motor_id == 3: # Markov
        prob_m = {}
        for n in range(1,26):
            h = [1 if n in d else 0 for d in past_draws]
            t11 = sum(1 for i in range(len(h)-1) if h[i]==1 and h[i+1]==1)
            t01 = sum(1 for i in range(len(h)-1) if h[i]==0 and h[i+1]==1)
            prob_m[n] = (t11/h.count(1)*100) if (n in ultimo_sorteio and h.count(1)>0) else (t01/h.count(0)*100 if h.count(0)>0 else 0)
    elif motor_id == 4: # Entropia
        total = len(past_draws)
        probs = {d: counts.get(d, 0)/total for d in range(1,26)}
        def ent(c): return -sum(probs[d]*math.log2(probs[d]) for d in c if probs.get(d,0)>0)
        ent_ideal = sum(ent(d) for d in past_draws)/total
    elif motor_id == 5: # Genético
        recentes = past_draws[-30:]

    # Simulação de Alta Performance (Amostragem Inteligente)
    for _ in range(15000): 
        comb = tuple(sorted(random.sample(range(1, 26), n_dezenas)))
        f_comb = frozenset(comb)
        
        # Filtros Básicos
        impares = sum(1 for d in f_comb if d % 2 != 0)
        q_primos = sum(1 for d in f_comb if d in primos)
        repetidas = len(f_comb.intersection(ultimo_sorteio))
        
        # Cálculo de Score por Motor
        if motor_id == 1: sc = sum(counts[d] for d in f_comb) / 100
        elif motor_id == 2: sc = sum(matriz[comb[i]][comb[j]] for i, j in itertools.combinations(range(n_dezenas), 2)) / 10
        elif motor_id == 3: sc = sum(prob_m.get(d, 0) for d in f_comb)
        elif motor_id == 4: sc = 100 - abs(ent(f_comb) - ent_ideal)*60
        elif motor_id == 5: sc = sum((len(f_comb.intersection(p))-10)**3 for p in recentes if len(f_comb.intersection(p))>=11)
        
        entry = (sc, comb)
        # Ranking Diamante (Filtros Estritos)
        if 7 <= impares <= 9 and 4 <= q_primos <= 7:
            if len(h_diamante) < 500: heapq.heappush(h_diamante, entry)
            elif sc > h_diamante[0][0]: heapq.heappushpop(h_diamante, entry)
        
        # Outros Rankings
        if len(h_geral) < 500: heapq.heappush(h_geral, entry)
        elif sc > h_geral[0][0]: heapq.heappushpop(h_geral, entry)
        
        if repetidas in [8, 9, 10]:
            if len(h_reversa) < 500: heapq.heappush(h_reversa, entry)
            elif sc > h_reversa[0][0]: heapq.heappushpop(h_reversa, entry)

        if len(h_frias) < 500: heapq.heappush(h_frias, (-sc, comb))
        elif -sc > h_frias[0][0]: heapq.heappushpop(h_frias, (-sc, comb))

    def formatar(h):
        l = sorted(h, key=lambda x: x[0], reverse=True)
        return pd.DataFrame([{"Sel":False, "Rank":i+1, "Pts":round(abs(s),2), **{f"B{j+1}":f"{d:02d}" for j,d in enumerate(c)}} for i,(s,c) in enumerate(l)])
    
    return formatar(h_diamante), formatar(h_frias), formatar(h_geral), formatar(h_reversa)

# ==========================================
# 4. INTERFACE E VOLANTE FIORI
# ==========================================
if not st.session_state["logged_in"]:
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.form("login"):
            st.title("💎 Logon")
            p = st.text_input("Senha", type="password")
            if st.form_submit_button("Acessar") and p == "abap123":
                st.session_state["logged_in"] = True
                st.rerun()
    st.stop()

st.markdown("""<div class="fiori-header"><div><b>💎 Gerador VIP</b> | SAP Laboratory v5.0</div><div><a href="/?logout=true" style="color:white;text-decoration:none;">Sair</a></div></div><div class="header-spacer"></div>""", unsafe_allow_html=True)

if os.path.exists(ARQUIVO_BASE):
    df = pd.read_csv(ARQUIVO_BASE, sep=";")
    
    col_rank, col_vol = st.columns([1.6, 1], gap="medium")
    
    with col_rank:
        c1, c2, c3 = st.columns([1, 2, 1.2])
        n_dez = c1.selectbox("Dezenas", [15, 16, 17])
        mot_txt = c2.selectbox("Estratégia Matemática", ["1. Frequência Clássica", "2. Teoria dos Grafos", "3. Cadeias de Markov", "4. Entropia de Shannon", "5. Algoritmo Genético"])
        
        if c3.button("▶ CALCULAR MOTORES", use_container_width=True):
            with st.spinner("Processando algoritmos..."):
                mid = int(mot_txt[0])
                d, f, g, r = executar_logica_completa(df, n_dez, mid)
                st.session_state["df_diamante"], st.session_state["df_frias"] = d, f
                st.session_state["df_geral"], st.session_state["df_reversa"] = g, r
        
        tabs = st.tabs(["💎 Diamante", "❄️ Frias", "🔥 Geral", "🔄 Reversa"])
        for i, tab in enumerate(tabs):
            key = ["df_diamante", "df_frias", "df_geral", "df_reversa"][i]
            with tab: st.dataframe(st.session_state[key], hide_index=True, use_container_width=True)

    with col_vol:
        st.markdown('<div class="sim-title">SIMULADOR DE JOGO</div>', unsafe_allow_html=True)
        with st.container(border=True):
            # Construção do Volante Manual
            v_cols = st.columns(5)
            for i in range(1, 26):
                with v_cols[(i-1)%5]:
                    sel = i in st.session_state["palpite_manual"]
                    if st.button(f"{i:02d}", key=f"btn_{i}", type="primary" if sel else "secondary", use_container_width=True):
                        if i in st.session_state["palpite_manual"]: st.session_state["palpite_manual"].remove(i)
                        elif len(st.session_state["palpite_manual"]) < 15: st.session_state["palpite_manual"].add(i)
                        st.rerun()
            
            st.markdown(f"<h4 style='text-align:center'>Marcadas: {len(st.session_state['palpite_manual'])}/15</h4>", unsafe_allow_html=True)
            if st.button("🗑️ Limpar", use_container_width=True):
                st.session_state["palpite_manual"] = set()
                st.rerun()

    # Histórico no Rodapé
    st.markdown('<div class="faixa-resultados">Últimos Concursos Gravados</div>', unsafe_allow_html=True)
    u_cols = st.columns(3)
    ultimos = df.tail(3).iloc[::-1]
    for i, (idx, row) in enumerate(ultimos.iterrows()):
        with u_cols[i]:
            dzs = "".join([f'<div class="bolinha-sap">{int(n):02d}</div>' for n in row[-15:]])
            st.markdown(f"""<div style="border:1px solid #ddd; border-radius:8px; padding:10px; background:#f9f9f9;">
                <small>Concurso: {idx}</small><div class="res-container">{dzs}</div></div>""", unsafe_allow_html=True)
