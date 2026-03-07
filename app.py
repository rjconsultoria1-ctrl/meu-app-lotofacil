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
# 1. TRATAMENTO DO BOTÃO SAIR E CONFIG
# ==========================================
try:
    params = st.query_params
    if "logout" in params:
        st.session_state["logged_in"] = False
        st.query_params.clear()
        st.rerun()
except AttributeError:
    params = st.experimental_get_query_params()
    if "logout" in params:
        st.session_state["logged_in"] = False
        st.experimental_set_query_params()
        st.rerun()

st.set_page_config(page_title="Gerador VIP | SAP", page_icon="💎", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 2. CACHE INTELIGENTE (ANTI-TELA BRANCA)
# ==========================================
@st.cache_data(show_spinner=False)
def carregar_dados_cache(caminho):
    if os.path.exists(caminho):
        return pd.read_csv(caminho, sep=";")
    return pd.DataFrame()

def contar_progresso_real(pasta):
    if not os.path.exists(pasta): return 0
    return len([f for f in os.listdir(pasta) if f.endswith("_meta.txt")])

# ==========================================
# 3. CSS GLOBAL E ESTILIZAÇÃO FIORI
# ==========================================
st.markdown("""
    <style>
        [data-testid="collapsedControl"] { display: none; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        
        .block-container { padding-top: 0rem !important; padding-bottom: 2rem; max-width: 95% !important; padding-left: 1rem; padding-right: 1rem; }
        
        .fiori-header-bar { background-color: #354A5F; color: white; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; font-family: Arial, sans-serif; position: fixed; top: 0; left: 0; width: 100vw; z-index: 9999; box-shadow: 0 1px 4px rgba(0,0,0,0.2); }
        .header-left { display: flex; align-items: center; font-size: 15px; }
        .header-right { display: flex; align-items: center; gap: 20px; font-size: 15px; }
        .btn-sair-link { color: white !important; text-decoration: none !important; font-weight: bold; border: 1px solid rgba(255,255,255,0.5); padding: 5px 16px; border-radius: 4px; font-size: 13px; cursor: pointer; transition: 0.2s; }
        .btn-sair-link:hover { background-color: rgba(255,255,255,0.2); border-color: white; }
        .header-spacer { margin-top: 55px; }
        
        .page-title-section { padding: 10px 0; border-bottom: 1px solid #D9D9D9; margin-bottom: 15px; }
        .header-title { font-size: 22px; font-weight: bold; color: #32363A; }
        
        .simulador-header { background-color: #5C2D91; color: white; padding: 12px; font-weight: bold; text-align: center; font-size: 14px; border-radius: 8px 8px 0 0; margin-bottom: -15px; position: relative; z-index: 10; }
        .simulador-card-style { border-radius: 0 0 8px 8px !important; border: 1px solid #E0E0E0 !important; border-top: none !important; background-color: white !important; padding-top: 20px !important; box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important; }

        .volante-grid-perfect { display: grid !important; grid-template-columns: repeat(5, 1fr) !important; gap: 12px !important; justify-content: center !important; justify-items: center !important; max-width: 320px !important; margin: 0 auto !important; padding: 10px 0 !important; }
        .volante-grid-perfect .element-container button { border-radius: 50% !important; height: 44px !important; width: 44px !important; padding: 0 !important; font-size: 15px !important; font-weight: bold !important; display: flex !important; justify-content: center !important; align-items: center !important; box-shadow: 0 1px 3px rgba(0,0,0,0.15) !important; transition: 0.1s !important; margin: 0 !important; }
        .volante-grid-perfect .element-container button[kind="secondary"] { background-color: white !important; color: #5C2D91 !important; border: 2px solid #5C2D91 !important; }
        .volante-grid-perfect .element-container button[kind="primary"] { background-color: #5C2D91 !important; color: white !important; border: none !important; }
        
        .card-resultado { background-color: white; border: 1px solid #E0E0E0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); overflow: hidden; width: 100%; margin-bottom: 10px; }
        .card-resultado-header { background-color: #5C2D91; color: white; padding: 12px 18px; font-weight: bold; display: flex; justify-content: space-between; font-size: 14px; }
        .card-resultado-body { padding: 15px; display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; justify-items: center; }
        .bolinha-roxa { background-color: #5C2D91; color: white; width: 35px; height: 35px; display: flex; align-items: center; justify-content: center; border-radius: 50%; font-weight: bold; font-size: 13px; }
        
        .faixa-resultados { background-color: #D9D9D9; padding: 10px 20px; font-weight: bold; color: #333; margin-top: 30px; margin-bottom: 15px; border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. LÓGICA DE NEGÓCIO E MOTORES
# ==========================================
ARQUIVO_BASE = "banco_dados.csv"
ARQUIVO_PERFORMANCE = "performance_motores.csv"
PASTA_CACHE = "memoria_calculos"

if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "palpite_manual" not in st.session_state: st.session_state["palpite_manual"] = set()
if "df_diamante" not in st.session_state:
    for k in ["df_diamante", "df_frias", "df_geral", "df_reversa"]: st.session_state[k] = pd.DataFrame()

def toggle_dezena(dezena):
    if dezena in st.session_state["palpite_manual"]: st.session_state["palpite_manual"].remove(dezena)
    elif len(st.session_state["palpite_manual"]) < 15: st.session_state["palpite_manual"].add(dezena)

def limpar_volante(): st.session_state["palpite_manual"] = set()

def executar_logica_motora(df_dados, n_dezenas, motor_id):
    dezenas_cols = [col for col in df_dados.columns if "Dezena" in col]
    if not dezenas_cols: dezenas_cols = df_dados.columns[-15:]
    past_draws = [frozenset(row) for row in df_dados[dezenas_cols].dropna().astype(int).values]
    ultimo_sorteio = past_draws[-1]
    total_draws = len(past_draws)
    
    # Filtros Matemáticos Padrão SAP
    primos, moldura, fibonacci = {2,3,5,7,11,13,17,19,23}, {1,2,3,4,5,6,10,11,15,16,20,21,22,23,24,25}, {1,2,3,5,8,13,21}
    LIMIT = 5000
    h_diamante, h_frias, h_geral, h_reversa = [], [], [], []

    # Setup Específico do Motor
    counts = Counter([n for d in past_draws for n in d])
    if motor_id == 2:
        matriz = [[0]*26 for _ in range(26)]
        for d in past_draws:
            l = list(d)
            for i in range(len(l)):
                for j in range(i+1, len(l)): matriz[l[i]][l[j]] += 1; matriz[l[j]][l[i]] += 1
    elif motor_id == 3:
        prob_m = {}
        for n in range(1,26):
            h = [1 if n in d else 0 for d in past_draws]
            t11 = sum(1 for i in range(len(h)-1) if h[i]==1 and h[i+1]==1)
            t01 = sum(1 for i in range(len(h)-1) if h[i]==0 and h[i+1]==1)
            prob_m[n] = (t11/h.count(1)*100) if (n in ultimo_sorteio and h.count(1)>0) else (t01/h.count(0)*100 if h.count(0)>0 else 0)
    elif motor_id == 4:
        probs = {d: counts.get(d, 0)/total_draws for d in range(1,26)}
        def calc_ent(c): return -sum(probs[d]*math.log2(probs[d]) for d in c if probs.get(d,0)>0)
        ent_ideal = sum(calc_ent(d) for d in past_draws)/total_draws
    elif motor_id == 5:
        recentes = past_draws[-30:]

    # Loop de Simulação
    for idx, comb in enumerate(itertools.combinations(range(1, 26), n_dezenas)):
        if idx > 1000000: break # Break de segurança
        f_comb = frozenset(comb)
        
        # Filtros
        impares = sum(1 for d in f_comb if d % 2 != 0)
        qtd_primos = sum(1 for d in f_comb if d in primos)
        soma = sum(f_comb)
        repetidas = len(f_comb.intersection(ultimo_sorteio))
        
        # Scoring por Motor
        if motor_id == 1: score = sum(counts[d] for d in f_comb) / 100
        elif motor_id == 2: score = sum(matriz[comb[i]][comb[j]] for i in range(n_dezenas) for j in range(i+1, n_dezenas)) / 10
        elif motor_id == 3: score = sum(prob_m[d] for d in f_comb)
        elif motor_id == 4: score = 100 - abs(calc_ent(f_comb) - ent_ideal)*50
        elif motor_id == 5: 
            score = sum((len(f_comb.intersection(p))-10)**3 for p in recentes if len(f_comb.intersection(p))>=11)

        # Categorização
        entry = (score, comb)
        if 7 <= impares <= 9 and 4 <= qtd_primos <= 7 and 170 <= soma <= 220:
            if len(h_diamante) < 500: heapq.heappush(h_diamante, entry)
            elif score > h_diamante[0][0]: heapq.heappushpop(h_diamante, entry)
        
        if len(h_geral) < 500: heapq.heappush(h_geral, entry)
        elif score > h_geral[0][0]: heapq.heappushpop(h_geral, entry)
        
        if repetidas in [8, 9, 10]:
            if len(h_reversa) < 500: heapq.heappush(h_reversa, entry)
            elif score > h_reversa[0][0]: heapq.heappushpop(h_reversa, entry)

        if len(h_frias) < 500: heapq.heappush(h_frias, (-score, comb))
        elif -score > h_frias[0][0]: heapq.heappushpop(h_frias, (-score, comb))

    # Formatação Final
    def fmt(h, inv=False):
        l = sorted(h, key=lambda x: x[0], reverse=True)
        return pd.DataFrame([{"Sel":False, "Rank":i+1, "Pts":round(abs(s),2), **{f"B{j+1}":f"{d:02d}" for j,d in enumerate(c)}} for i,(s,c) in enumerate(l)])
    
    return fmt(h_diamante), fmt(h_frias, True), fmt(h_geral), fmt(h_reversa)

def worker_fantasma(df, tamanho):
    if not os.path.exists(PASTA_CACHE): os.makedirs(PASTA_CACHE)
    for mid in [1, 2, 3, 4, 5]:
        for n in [15, 16, 17]:
            pref = f"{PASTA_CACHE}/M{mid}_{n}"
            if not os.path.exists(f"{pref}_meta.txt"):
                d, f, g, r = executar_logica_motora(df, n, mid)
                d.to_csv(f"{pref}_dia.csv", sep=";", index=False)
                f.to_csv(f"{pref}_fri.csv", sep=";", index=False)
                g.to_csv(f"{pref}_ger.csv", sep=";", index=False)
                r.to_csv(f"{pref}_rev.csv", sep=";", index=False)
                with open(f"{pref}_meta.txt", "w") as m: m.write(str(tamanho))

# ==========================================
# 5. INTERFACE (UI)
# ==========================================
if not st.session_state.get("logged_in"):
    with st.form("login"):
        st.title("💎 Gerador VIP Logon")
        u = st.text_input("Usuário", value="consultor.sd")
        p = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar") and p == "abap123":
            st.session_state["logged_in"] = True
            st.rerun()
    st.stop()

st.markdown("""<div class="fiori-header-bar"><div class="header-left"><b>💎 Gerador VIP</b> | SAP Laboratory</div><div class="header-right"><a href="/?logout=true" target="_self" class="btn-sair-link">Sair</a></div></div><div class="header-spacer"></div>""", unsafe_allow_html=True)

df = carregar_dados_cache(ARQUIVO_BASE)
if not df.empty:
    # Radar
    total_concluido = contar_progresso_real(PASTA_CACHE)
    st.progress(total_concluido/15, text=f"📡 Radar de Memória: {total_concluido}/15 concluídos")
    
    col_esq, col_dir = st.columns([1.2, 1], gap="large")
    
    with col_esq:
        c1, c2, c3 = st.columns([1, 2, 1])
        n_dez = c1.radio("Dezenas:", [15, 16, 17], horizontal=True)
        motor_txt = c2.selectbox("Motor:", ["1. Frequência", "2. Grafos", "3. Markov", "4. Entropia", "5. Genético"])
        if c3.button("▶ Gerar", use_container_width=True):
            mid = int(motor_txt[0])
            pref = f"{PASTA_CACHE}/M{mid}_{n_dez}"
            if os.path.exists(f"{pref}_meta.txt"):
                st.session_state["df_diamante"] = pd.read_csv(f"{pref}_dia.csv", sep=";")
                st.session_state["df_frias"] = pd.read_csv(f"{pref}_fri.csv", sep=";")
                st.session_state["df_geral"] = pd.read_csv(f"{pref}_ger.csv", sep=";")
                st.session_state["df_reversa"] = pd.read_csv(f"{pref}_rev.csv", sep=";")
            else:
                d, f, g, r = executar_logica_motora(df, n_dez, mid)
                st.session_state["df_diamante"], st.session_state["df_frias"] = d, f
                st.session_state["df_geral"], st.session_state["df_reversa"] = g, r
            
            threading.Thread(target=worker_fantasma, args=(df.copy(), len(df)), daemon=True).start()
            st.rerun()

        tabs = st.tabs(["💎 Diamante", "❄️ Frias", "🔥 Geral", "🔄 Reversa"])
        for i, t in enumerate(tabs):
            key = ["df_diamante", "df_frias", "df_geral", "df_reversa"][i]
            with t: st.data_editor(st.session_state[key], hide_index=True, use_container_width=True, key=f"editor_{key}")

    with col_dir:
        st.markdown('<div class="simulador-header">SIMULADOR DE VOLANTE</div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown('<div id="marker-volante"></div>', unsafe_allow_html=True)
            for i in range(1, 26):
                tipo = "primary" if i in st.session_state["palpite_manual"] else "secondary"
                st.button(f"{i:02d}", key=f"v_{i}", type=tipo, on_click=toggle_dezena, args=(i,))
            
            st.markdown(f"<p style='text-align:center'>Selecionadas: {len(st.session_state['palpite_manual'])}/15</p>", unsafe_allow_html=True)
            if st.button("Limpar Volante", use_container_width=True): limpar_volante(); st.rerun()

    # Rodapé com últimos resultados
    st.markdown('<div class="faixa-resultados">Últimos Resultados</div>', unsafe_allow_html=True)
    ultimos = df.tail(3).iloc[::-1]
    cols_rodape = st.columns(3)
    for i, (idx, row) in enumerate(ultimos.iterrows()):
        dzs = "".join([f'<div class="bolinha-roxa">{int(n):02d}</div>' for n in row[-15:]])
        cols_rodape[i].markdown(f'<div class="card-resultado"><div class="card-resultado-header">Sorteio {idx}</div><div class="card-resultado-body">{dzs}</div></div>', unsafe_allow_html=True)

# Injeção para o Grid do Volante
components.html("<script>const g=window.parent.document.getElementById('marker-volante');if(g){const p=g.closest('.element-container').parentNode;p.classList.add('volante-grid-perfect');}</script>", height=0)
