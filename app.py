import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from collections import Counter
import itertools
import os
import random
import threading
import math
from datetime import datetime

# ==========================================
# 1. TRATAMENTO DO BOTÃO SAIR
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

# ==========================================
# 2. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Gerador VIP | SAP", page_icon="💎", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 3. CSS GLOBAL E BLINDAGEM DE LAYOUT
# ==========================================
st.markdown("""
    <style>
        [data-testid="collapsedControl"] { display: none; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        .block-container { padding-top: 0rem !important; padding-bottom: 2rem; max-width: 95% !important; padding-left: 1rem; padding-right: 1rem; }
        [data-testid="stForm"] { border: none !important; padding: 0 !important; }
        .fiori-header-bar { background-color: #354A5F; color: white; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; font-family: Arial, sans-serif; position: fixed; top: 0; left: 0; width: 100vw; z-index: 9999; box-shadow: 0 1px 4px rgba(0,0,0,0.2); }
        .header-left { display: flex; align-items: center; font-size: 15px; }
        .header-right { display: flex; align-items: center; gap: 20px; font-size: 15px; }
        .btn-sair-link { color: white !important; text-decoration: none !important; font-weight: bold; border: 1px solid rgba(255,255,255,0.5); padding: 5px 16px; border-radius: 4px; font-size: 13px; cursor: pointer; transition: 0.2s; }
        .btn-sair-link:hover { background-color: rgba(255,255,255,0.2); border-color: white; }
        .header-spacer { margin-top: 55px; }
        .page-title-section { padding: 10px 0; border-bottom: 1px solid #D9D9D9; margin-bottom: 15px; }
        .header-title { font-size: 22px; font-weight: bold; color: #32363A; }
        .header-subtitle { font-size: 14px; color: #6A6D70; }
        .simulador-header { background-color: #5C2D91; color: white; padding: 12px; font-weight: bold; text-align: center; font-size: 14px; border-radius: 8px 8px 0 0; margin-bottom: -15px; position: relative; z-index: 10; }
        div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 0 0 8px 8px !important; border: 1px solid #E0E0E0 !important; border-top: none !important; background-color: white !important; padding-top: 20px !important; box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important; }
        .volante-grid-perfect { display: grid !important; grid-template-columns: repeat(5, 1fr) !important; gap: 12px !important; justify-content: center !important; justify-items: center !important; max-width: 320px !important; margin: 0 auto !important; padding: 10px 0 !important; }
        .volante-grid-perfect .element-container button { border-radius: 50% !important; height: 44px !important; width: 44px !important; padding: 0 !important; font-size: 15px !important; font-weight: bold !important; display: flex !important; justify-content: center !important; align-items: center !important; box-shadow: 0 1px 3px rgba(0,0,0,0.15) !important; transition: 0.1s !important; margin: 0 !important; }
        .volante-grid-perfect .element-container button[kind="secondary"] { background-color: white !important; color: #5C2D91 !important; border: 2px solid #5C2D91 !important; }
        .volante-grid-perfect .element-container button[kind="primary"] { background-color: #5C2D91 !important; color: white !important; border: none !important; }
        .stButton>button { border-radius: 4px; font-weight: bold; }
        .stButton>button[kind="primary"] { background-color: #5C2D91; border-color: #5C2D91; color: white; }
        .stButton>button[kind="primary"]:hover { background-color: #4A1E7A; border-color: #4A1E7A; }
        .faixa-resultados { background-color: #D9D9D9; padding: 10px 20px; font-weight: bold; color: #333; margin-top: 30px; margin-bottom: 15px; border-radius: 4px; }
        .card-resultado { background-color: white; border: 1px solid #E0E0E0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); overflow: hidden; width: 100%; }
        .card-resultado-header { background-color: #5C2D91; color: white; padding: 12px 18px; font-weight: bold; display: flex; justify-content: space-between; font-size: 14px; text-transform: uppercase; }
        .card-resultado-body { padding: 15px; display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; justify-items: center; }
        .bolinha-roxa { background-color: #5C2D91; color: white; width: 38px; height: 38px; display: flex; align-items: center; justify-content: center; border-radius: 50%; font-weight: bold; font-size: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.15); }
    </style>
""", unsafe_allow_html=True)

ARQUIVO_BASE = "banco_dados.csv"
ARQUIVO_PERFORMANCE = "performance_motores.csv"

# ==========================================
# 4. CONTROLE DE SESSÃO
# ==========================================
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "palpite_manual" not in st.session_state: st.session_state["palpite_manual"] = set()

if "df_diamante" not in st.session_state:
    cols_vazias = ["Sel", "Rank", "Pts"] + [f"B{i}" for i in range(1, 16)]
    df_vazio = pd.DataFrame(columns=cols_vazias)
    st.session_state["df_diamante"] = df_vazio
    st.session_state["df_frias"] = df_vazio
    st.session_state["df_geral"] = df_vazio
    st.session_state["df_reversa"] = df_vazio
    st.session_state["gerado"] = False
    st.session_state["MOTOR_GERADO"] = "N/A"

def toggle_dezena(dezena):
    palpite = st.session_state["palpite_manual"]
    if dezena in palpite: palpite.remove(dezena)
    elif len(palpite) < 15: palpite.add(dezena)
    st.session_state["palpite_manual"] = palpite

def limpar_volante():
    st.session_state["palpite_manual"] = set()

# ==========================================
# 5. TELA DE LOGIN 
# ==========================================
if not st.session_state["logged_in"]:
    st.markdown("""
        <style>
            .stApp { background: radial-gradient(circle at 50% 40%, #E2EDF8 0%, #9CBBE0 100%); }
            .main .block-container { display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; padding: 0 !important; }
            [data-testid="stForm"] { background-color: white !important; padding: 45px 35px !important; border-radius: 12px !important; box-shadow: 0 10px 30px rgba(0,20,50,0.15) !important; border: none !important; width: 100% !important; max-width: 420px !important; margin: 0 auto !important; }
            .stSelectbox>div { background-color: white !important; }
        </style>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        st.markdown("<h2 style='text-align:center; color:#0070F2; margin-top:0;'>💎 Logon</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#556B82; font-size: 14px; margin-bottom: 25px;'>Gerador VIP Lotofácil</p>", unsafe_allow_html=True)
        usuario = st.text_input("Usuário", value="consultor.sd", placeholder="Digite seu usuário")
        senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        st.caption("Idioma")
        st.selectbox("", ["PT - Português", "EN - English", "ES - Español"], label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("Logon", use_container_width=True, type="secondary"):
            if senha == "abap123":
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("Falha na autenticação.")
    st.markdown("<p style='text-align:center; font-size:12px; color:#0070F2; margin-top:15px; cursor:pointer;'>Modificar senha / Ajuda</p>", unsafe_allow_html=True)
    st.stop() 

# ==========================================
# 6. O APLICATIVO E MOTORES MATEMÁTICOS
# ==========================================
st.markdown("""
    <div class="fiori-header-bar">
        <div class="header-left"><span style="color:#6CB2EB; font-weight:bold;">💎 Gerador VIP</span> &nbsp;|&nbsp; Simulador Lotofácil</div>
        <div class="header-right"><span>🔍 🔔 ⚙️</span><a href="/?logout=true" target="_self" class="btn-sair-link">Sair</a></div>
    </div><div class="header-spacer"></div>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="page-title-section">
        <span class="header-title">Cockpit Simulador VIP LotoFácil</span>
        <span class="header-subtitle" style="margin-left: 15px;">Otimização combinatória baseada em histórico e regras matemáticas.</span>
    </div>
""", unsafe_allow_html=True)

# ------------------------------------------
# LÓGICAS DOS MOTORES (1 a 4)
# ------------------------------------------
def executar_logica_motora(df_dados, n_dezenas, motor_id):
    dezenas_cols = [col for col in df_dados.columns if "Dezena" in col]
    if not dezenas_cols: dezenas_cols = df_dados.columns[-15:]
    past_draws = [frozenset(row) for row in df_dados[dezenas_cols].dropna().astype(int).values]
    ultimo_sorteio = past_draws[-1]
    total_draws = len(past_draws)
    
    if n_dezenas == 15: imp_d = [7, 8]; pri_d = [4, 5, 6]; mol_d = [9, 10, 11]; fib_d = [3, 4, 5]; soma_d = [180, 210]
    elif n_dezenas == 16: imp_d = [8, 9]; pri_d = [5, 6, 7]; mol_d = [10, 11]; fib_d = [4, 5]; soma_d = [195, 220]
    else: imp_d = [8, 9, 10]; pri_d = [5, 6, 7, 8]; mol_d = [11, 12, 13]; fib_d = [4, 5, 6]; soma_d = [210, 250]
    primos = {2, 3, 5, 7, 11, 13, 17, 19, 23}
    moldura = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
    fibonacci = {1, 2, 3, 5, 8, 13, 21}
    lista_geral, lista_frias, lista_diamante, lista_reversa = [], [], [], []

    # Setup Motores
    if motor_id == 1:
        all_numbers = df_dados[dezenas_cols].dropna().astype(int).values.flatten()
        counts = Counter(all_numbers)
    elif motor_id == 2:
        matriz_afinidade = [[0] * 26 for _ in range(26)]
        for draw in past_draws:
            lst = list(draw)
            for i in range(len(lst)):
                for j in range(i+1, len(lst)):
                    matriz_afinidade[lst[i]][lst[j]] += 1
                    matriz_afinidade[lst[j]][lst[i]] += 1
    elif motor_id == 3:
        prob_markov = {}
        for num in range(1, 26):
            hist_num = [1 if num in draw else 0 for draw in past_draws]
            t_1_1, t_1_0, t_0_1, t_0_0 = 0, 0, 0, 0
            for i in range(len(hist_num) - 1):
                if hist_num[i] == 1 and hist_num[i+1] == 1: t_1_1 += 1
                elif hist_num[i] == 1 and hist_num[i+1] == 0: t_1_0 += 1
                elif hist_num[i] == 0 and hist_num[i+1] == 1: t_0_1 += 1
                elif hist_num[i] == 0 and hist_num[i+1] == 0: t_0_0 += 1
            total_1, total_0 = t_1_1 + t_1_0, t_0_1 + t_0_0
            p_1_to_1 = (t_1_1 / total_1) if total_1 > 0 else 0
            p_0_to_1 = (t_0_1 / total_0) if total_0 > 0 else 0
            prob_markov[num] = (p_1_to_1 * 100) if num in ultimo_sorteio else (p_0_to_1 * 100)
    elif motor_id == 4:
        # MOTOR 4: ENTROPIA DE SHANNON
        all_numbers = df_dados[dezenas_cols].dropna().astype(int).values.flatten()
        counts = Counter(all_numbers)
        prob_entropia = {d: counts.get(d, 0) / total_draws for d in range(1, 26)}
        
        def calc_entropia(combinacao):
            return -sum(prob_entropia[d] * math.log2(prob_entropia[d]) for d in combinacao if prob_entropia.get(d, 0) > 0)
            
        # Descobre a "Assinatura Natural" histórica
        hist_entropias = [calc_entropia(draw) for draw in past_draws]
        entropia_ideal = sum(hist_entropias) / len(hist_entropias) if hist_entropies else 0

    for comb in itertools.combinations(range(1, 26), n_dezenas):
        f_comb = frozenset(comb)
        impares = sum(1 for d in f_comb if d % 2 != 0)
        
        if impares not in imp_d:
            if random.random() > 0.05: continue
            
        qtd_primos = sum(1 for d in f_comb if d in primos)
        qtd_moldura = sum(1 for d in f_comb if d in moldura)
        qtd_fibo = sum(1 for d in f_comb if d in fibonacci)
        soma_total = sum(f_comb)
        repetidas_do_ultimo = len(f_comb.intersection(ultimo_sorteio))
        
        eh_valido_basico = (impares in imp_d) and (pri_d[0] <= qtd_primos <= pri_d[-1])
        eh_ouro = eh_valido_basico and (mol_d[0] <= qtd_moldura <= mol_d[-1]) and (fib_d[0] <= qtd_fibo <= fib_d[-1]) and (soma_d[0] <= soma_total <= soma_d[1])

        # Pontuações
        if motor_id == 1:
            score = sum(counts[d] for d in f_comb)
            score_frias_val = (50000 - score) / 100.0
            score_val = score / 100.0
            if impares in imp_d: score_frias_val += 50; score_val += 50
            if qtd_primos in pri_d: score_frias_val += 30; score_val += 30
        elif motor_id == 2:
            score_val = sum(matriz_afinidade[comb[i]][comb[j]] for i in range(n_dezenas) for j in range(i+1, n_dezenas))
            score_frias_val = score_val
        elif motor_id == 3:
            score_val = sum(prob_markov[d] for d in f_comb)
            score_frias_val = score_val
        elif motor_id == 4:
            H_comb = calc_entropia(f_comb)
            # Aproximação da Entropia Ideal (100 pts é a perfeição)
            distancia = abs(H_comb - entropia_ideal)
            score_val = max(0, 100.0 - (distancia * 50.0)) 
            score_frias_val = score_val

        if eh_ouro: lista_diamante.append((score_val, list(comb)))
        if eh_valido_basico: lista_frias.append((score_frias_val, list(comb)))
        lista_geral.append((score_val, list(comb)))
        
        alvo_repetidas = 9 if n_dezenas == 15 else (10 if n_dezenas == 16 else 11)
        if repetidas_do_ultimo in [alvo_repetidas, alvo_repetidas+1]:
            lista_reversa.append((score_val, list(comb)))

    lista_diamante.sort(key=lambda x: x[0], reverse=True)
    lista_geral.sort(key=lambda x: x[0], reverse=True) 
    lista_reversa.sort(key=lambda x: x[0], reverse=True)  
    lista_frias.sort(key=lambda x: x[0], reverse=(motor_id in [1, 4])) # No M1 e M4 frias inverte

    def formatar(lista): 
        fator = 10.0 if motor_id == 2 else 1.0
        return [{"Sel": False, "Rank": r, "Pts": round(s/fator, 2), **{f"B{i+1}": f"{d:02d}" for i, d in enumerate(c)}} for r, (s, c) in enumerate(lista, 1)]
    
    return pd.DataFrame(formatar(lista_diamante[:5000])), pd.DataFrame(formatar(lista_frias[:5000])), pd.DataFrame(formatar(lista_geral[:5000])), pd.DataFrame(formatar(lista_reversa[:5000]))

# ------------------------------------------
# TRABALHADOR FANTASMA & RADAR
# ------------------------------------------
def worker_fantasma_calcula_tudo(df_dados, tamanho_banco_atual):
    pasta_cache = "memoria_calculos"
    if not os.path.exists(pasta_cache): os.makedirs(pasta_cache)
    # AGORA COM 4 MOTORES
    for motor_id in [1, 2, 3, 4]:
        for n_dez in [15, 16, 17]:
            arq_meta = f"{pasta_cache}/M{motor_id}_{n_dez}_meta.txt"
            prefixo_csv = f"{pasta_cache}/M{motor_id}_{n_dez}"
            precisa_calcular = True
            if os.path.exists(arq_meta):
                with open(arq_meta, "r") as f:
                    try:
                        if int(f.read().strip()) == tamanho_banco_atual: precisa_calcular = False 
                    except: pass
            if precisa_calcular:
                try:
                    dia, fri, ger, rev = executar_logica_motora(df_dados, n_dez, motor_id)
                    dia.to_csv(f"{prefixo_csv}_dia.csv", sep=";", index=False)
                    fri.to_csv(f"{prefixo_csv}_fri.csv", sep=";", index=False)
                    ger.to_csv(f"{prefixo_csv}_ger.csv", sep=";", index=False)
                    rev.to_csv(f"{prefixo_csv}_rev.csv", sep=";", index=False)
                    with open(arq_meta, "w") as f: f.write(str(tamanho_banco_atual))
                except: pass

def processar_com_memoria(df_dados, n_dezenas, motor_selecionado):
    if "1." in motor_selecionado: motor_id = 1
    elif "2." in motor_selecionado: motor_id = 2
    elif "3." in motor_selecionado: motor_id = 3
    elif "4." in motor_selecionado: motor_id = 4
    else:
        cols_vazias = ["Sel", "Rank", "Pts"] + [f"B{i}" for i in range(1, n_dezenas+1)]
        return pd.DataFrame(columns=cols_vazias), pd.DataFrame(columns=cols_vazias), pd.DataFrame(columns=cols_vazias), pd.DataFrame(columns=cols_vazias)

    pasta_cache = "memoria_calculos"
    if not os.path.exists(pasta_cache): os.makedirs(pasta_cache)
    arq_meta = f"{pasta_cache}/M{motor_id}_{n_dezenas}_meta.txt"
    prefixo_csv = f"{pasta_cache}/M{motor_id}_{n_dezenas}"
    tamanho_banco_atual = len(df_dados)

    if os.path.exists(arq_meta):
        with open(arq_meta, "r") as f: tamanho_salvo = int(f.read().strip())
        if tamanho_salvo == tamanho_banco_atual:
            try:
                return pd.read_csv(f"{prefixo_csv}_dia.csv", sep=";"), pd.read_csv(f"{prefixo_csv}_fri.csv", sep=";"), pd.read_csv(f"{prefixo_csv}_ger.csv", sep=";"), pd.read_csv(f"{prefixo_csv}_rev.csv", sep=";")
            except: pass 

    dia, fri, ger, rev = executar_logica_motora(df_dados, n_dezenas, motor_id)
    dia.to_csv(f"{prefixo_csv}_dia.csv", sep=";", index=False)
    fri.to_csv(f"{prefixo_csv}_fri.csv", sep=";", index=False)
    ger.to_csv(f"{prefixo_csv}_ger.csv", sep=";", index=False)
    rev.to_csv(f"{prefixo_csv}_rev.csv", sep=";", index=False)
    with open(arq_meta, "w") as f: f.write(str(tamanho_banco_atual))
    return dia, fri, ger, rev

# ------------------------------------------
df = None
if os.path.exists(ARQUIVO_BASE):
    try: df = pd.read_csv(ARQUIVO_BASE, sep=';', encoding='utf-8')
    except:
        try: df = pd.read_csv(ARQUIVO_BASE, sep=',', encoding='latin-1')
        except: pass

with st.expander("⚙️ Gestão de Base de Dados (Master Data)"):
    if df is not None: st.info(f"Status do Banco: CONECTADO | {len(df)} sorteios.")
    arquivo_upado = st.file_uploader("Upload de novo Master Data:", type=["csv", "xlsx"])
    if arquivo_upado is not None:
        if arquivo_upado.name.endswith('.csv'): df_novo = pd.read_csv(arquivo_upado, sep=';', encoding='utf-8')
        else: df_novo = pd.read_excel(arquivo_upado)
        df_novo.to_csv(ARQUIVO_BASE, index=False, sep=';')
        st.cache_data.clear()
        st.success("Sincronização concluída. As memórias dos motores serão resetadas!")
        if os.path.exists("memoria_calculos"):
            for f in os.listdir("memoria_calculos"): os.remove(os.path.join("memoria_calculos", f))
        st.rerun()

st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

# ------------------------------------------
# RADAR DO FANTASMA (DASHBOARD VISUAL)
# ------------------------------------------
pasta_cache = "memoria_calculos"
TOTAL_TAREFAS = 12 # 4 motores * 3 tipos de dezenas
tarefas_concluidas = len([f for f in os.listdir(pasta_cache) if f.endswith("_meta.txt")]) if os.path.exists(pasta_cache) else 0
progresso_perc = min(tarefas_concluidas / TOTAL_TAREFAS, 1.0)
st.progress(progresso_perc, text=f"📡 Radar de Processos em Fila: Cofre de Memória {tarefas_concluidas}/{TOTAL_TAREFAS} concluído ({(progresso_perc*100):.0f}%)")

# ==========================================
# DIVISÃO DA TELA E O SIMULADOR BLINDADO
# ==========================================
if df is not None:
    col_esq, col_dir = st.columns([1.2, 1], gap="large")

    with col_esq:
        c_radio, c_motor, c_btn = st.columns([1.5, 2.5, 1.5])
        with c_radio:
            N_DEZENAS = st.radio("Dezenas:", [15, 16, 17], horizontal=True)
        with c_motor:
            lista_motores = [
                "1. Frequência Clássica (Atual)",
                "2. Teoria dos Grafos (Conexões)",
                "3. Cadeias de Markov (Inércia)",
                "4. Entropia de Shannon (Caos)",
                "5. Algoritmo Genético (Mutação)"
            ]
            MOTOR_ESCOLHIDO = st.selectbox("Estratégia de Cálculo:", lista_motores, label_visibility="collapsed")
        
        with c_btn:
            if st.button("▶ Gerar", use_container_width=True, type="secondary"):
                with st.spinner(f"Acessando Memória / Processando {MOTOR_ESCOLHIDO}..."):
                    dia, fri, ger, rev = processar_com_memoria(df, N_DEZENAS, MOTOR_ESCOLHIDO)
                    
                    tamanho_db = len(df)
                    fantasma = threading.Thread(target=worker_fantasma_calcula_tudo, args=(df.copy(), tamanho_db))
                    fantasma.daemon = True 
                    fantasma.start()
                    
                    if dia.empty: st.warning(f"O motor '{MOTOR_ESCOLHIDO}' está em desenvolvimento.")
                    else: st.toast("✅ Motor carregado! (Trabalhador Fantasma operando em background...)")
                    
                    st.session_state["df_diamante"] = dia.head(500) if not dia.empty else dia
                    st.session_state["df_reversa"] = rev.head(500) if not rev.empty else rev
                    st.session_state["df_frias"] = fri.head(500) if not fri.empty else fri
                    st.session_state["df_geral"] = ger.head(500) if not ger.empty else ger
                    st.session_state["N_GERADO"] = N_DEZENAS
                    st.session_state["gerado"] = True
                    st.session_state["MOTOR_GERADO"] = MOTOR_ESCOLHIDO
                    # Força uma atualização leve na tela para o Radar avançar mais rápido
                    st.rerun()

        cfg_col = {"Sel": st.column_config.CheckboxColumn("Sel", default=False)}
        a1, a2, a3, a4 = st.tabs(["💎 Ranking Diamante", "❄️ Ranking Elite", "🔥 Ranking Geral", "🔄 Ranking Reversa"])
        with a1: df_dia_ed = st.data_editor(st.session_state["df_diamante"], column_config=cfg_col, hide_index=True, key="e1", use_container_width=True)
        with a2: df_fri_ed = st.data_editor(st.session_state["df_frias"], column_config=cfg_col, hide_index=True, key="e2", use_container_width=True)
        with a3: df_ger_ed = st.data_editor(st.session_state["df_geral"], column_config=cfg_col, hide_index=True, key="e3", use_container_width=True)
        with a4: df_rev_ed = st.data_editor(st.session_state["df_reversa"], column_config=cfg_col, hide_index=True, key="e4", use_container_width=True)

    with col_dir:
        st.markdown("<h3 style='text-align:center; color:#5C2D91; margin-top:0;'>Simulador da LOTOFÁCIL</h3>", unsafe_allow_html=True)
        
        c_volante, c_resumo = st.columns([1, 1], gap="medium")
        
        with c_volante:
            st.markdown('<div class="simulador-header">EU TERIA GANHO ALGUM PRÊMIO?</div>', unsafe_allow_html=True)
            with st.container(border=True):
                with st.container():
                    st.markdown('<div id="marker-volante"></div>', unsafe_allow_html=True)
                    for num in range(1, 26):
                        selecionada = num in st.session_state["palpite_manual"]
                        tipo_btn = "primary" if selecionada else "secondary"
                        st.button(f"{num:02d}", key=f"btn_{num}", type=tipo_btn, on_click=toggle_dezena, args=(num,))
                    components.html("""
                        <script>
                            const marker = window.parent.document.getElementById('marker-volante');
                            if(marker){
                                const verticalBlock = marker.closest('div[data-testid="stVerticalBlock"]');
                                if(verticalBlock) verticalBlock.classList.add('volante-grid-perfect');
                            }
                        </script>
                    """, height=0, width=0)
                
                selecionadas = sorted(list(st.session_state["palpite_manual"]))
                st.markdown(f"<p style='text-align:center; font-size:13px; color:#6A6D70; padding-top: 15px; border-top: 1px solid #E0E0E0;'>Números selecionados: <b>{len(selecionadas)}/15</b></p>", unsafe_allow_html=True)
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1: verificar = st.button("Verificar Histórico", use_container_width=True, type="primary")
                with c_btn2: validar_listas = st.button("Validar nas Listas", use_container_width=True)
                
                c_btn3, c_btn4 = st.columns([4, 1])
                with c_btn3: salvar_db = st.button("💾 Gravar no Banco", use_container_width=True)
                with c_btn4: st.button("🗑️", on_click=limpar_volante, help="Limpar volante")

        with c_resumo:
            st.markdown("<h5 style='text-align:center; color:#32363A; margin-top:0;'>Resumo do Palpite</h5>", unsafe_allow_html=True)
            
            if verificar and len(selecionadas) == 15:
                dezenas_cols = [c for c in df.columns if "Dezena" in c]
                if not dezenas_cols: dezenas_cols = df.columns[-15:]
                set_palpite = set(selecionadas)
                acertos_hist = {15: 0, 14: 0, 13: 0, 12: 0, 11: 0}
                for _, row in df.iterrows():
                    jogo_hist = set(row[dezenas_cols].dropna().astype(int).values)
                    acertos = len(set_palpite.intersection(jogo_hist))
                    if acertos >= 11: acertos_hist[acertos] += 1
                total_premios = sum(acertos_hist.values())
                st.success(f"Você teria ganhado prêmios em **{total_premios} concurso(s)** ao longo da história!")
                st.markdown(f"""
                <div style='background-color: white; border: 1px solid #7B2CBF; border-radius: 8px; padding: 15px;'>
                    <ul style='font-size: 14px; color:#5C2D91; margin:0;'>
                        <li>🚀 **15 dezenas**: {acertos_hist[15]} concursos.</li>
                        <li>💥 **14 dezenas**: {acertos_hist[14]} concursos.</li>
                        <li>✅ **13 dezenas**: {acertos_hist[13]} concursos.</li>
                        <li>✅ **12 dezenas**: {acertos_hist[12]} concursos.</li>
                        <li>✅ **11 dezenas**: {acertos_hist[11]} concursos.</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            elif validar_listas and len(selecionadas) == 15:
                set_sorteadas = set(selecionadas)
                n_gerado = st.session_state.get('N_GERADO', 15)
                colunas_b = [f"B{i+1}" for i in range(n_gerado)]
                resultados_duelo = {}
                nomes_motores = {1: "Frequência Clássica", 2: "Teoria dos Grafos", 3: "Cadeias de Markov", 4: "Entropia de Shannon"}
                
                for motor_id in [1, 2, 3, 4]:
                    prefixo = f"memoria_calculos/M{motor_id}_{n_gerado}"
                    secoes = [("💎 Diamante", f"{prefixo}_dia.csv"), ("❄️ Elite", f"{prefixo}_fri.csv"), 
                              ("🔥 Geral", f"{prefixo}_ger.csv"), ("🔄 Reversa", f"{prefixo}_rev.csv")]
                    melhor_acerto_motor, msg_motor = 0, ""
                    for nome_lista, caminho_csv in secoes:
                        if os.path.exists(caminho_csv):
                            df_lista = pd.read_csv(caminho_csv, sep=';')
                            for index, row in df_lista.iterrows():
                                jogo = set([int(row[col]) for col in colunas_b])
                                acertos = len(set_sorteadas.intersection(jogo))
                                if acertos > melhor_acerto_motor:
                                    melhor_acerto_motor, msg_motor = acertos, f"Linha #{int(row['Rank'])} ({nome_lista})"
                    if melhor_acerto_motor > 0: resultados_duelo[motor_id] = {"acertos": melhor_acerto_motor, "msg": msg_motor}

                if resultados_duelo:
                    melhor_geral = max([res["acertos"] for res in resultados_duelo.values()])
                    if melhor_geral >= 14: st.success(f"🎉 **CRUZAMENTO PERFEITO!** Máximo de {melhor_geral} acertos.")
                    elif melhor_geral >= 11: st.info(f"👍 **CRUZAMENTO POSITIVO:** Máximo de {melhor_geral} acertos.")
                    else: st.error(f"📉 **FALHA:** Nenhuma estratégia passou de {melhor_geral} acertos.")
                    
                    st.markdown("**🛡️ Raio-X contra todas as Estratégias:**")
                    for mid, res in resultados_duelo.items():
                        icone = "✅" if res['acertos'] >= 11 else "❌"
                        st.markdown(f"- {icone} **{nomes_motores[mid]}**: {res['acertos']} pts [{res['msg']}]")
                        
                        if res['acertos'] >= 11:
                            novo_registro_perf = pd.DataFrame([{
                                "Data_Validacao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                "Motor_Utilizado": nomes_motores[mid],
                                "Lista_Origem": res['msg'].split("(")[1].replace(")", ""),
                                "Acertos": res['acertos'],
                                "Dezenas": ", ".join([f"{d:02d}" for d in selecionadas])
                            }])
                            if os.path.exists(ARQUIVO_PERFORMANCE):
                                df_perf = pd.read_csv(ARQUIVO_PERFORMANCE, sep=';', encoding='utf-8')
                                df_perf = pd.concat([df_perf, novo_registro_perf], ignore_index=True)
                            else: df_perf = novo_registro_perf
                            df_perf.to_csv(ARQUIVO_PERFORMANCE, index=False, sep=';')
                    st.caption("📊 *Scores gravados no banco de dados com sucesso!*")
                else: st.warning("Gere os motores ao menos uma vez para criar a Memória do Sistema antes de validar!")

            elif salvar_db and len(selecionadas) == 15:
                dezenas_cols = [c for c in df.columns if "Dezena" in c]
                if not dezenas_cols: dezenas_cols = df.columns[-15:]
                set_palpite = set(selecionadas)
                ja_sorteado = False
                for _, row in df.iterrows():
                    jogo_hist = set(row[dezenas_cols].dropna().astype(int).values)
                    if set_palpite == jogo_hist:
                        ja_sorteado = True; break
                if ja_sorteado: st.error("🚨 **Este jogo já existe no banco histórico!**")
                else:
                    conc_col = next((c for c in df.columns if 'Concurso' in c or 'Sorteio' in c or 'N°' in c), None)
                    data_col = next((c for c in df.columns if 'Data' in c), None)
                    novo_registro = {col: None for col in df.columns}
                    if conc_col: 
                        try: novo_registro[conc_col] = int(df[conc_col].max()) + 1
                        except: novo_registro[conc_col] = len(df) + 1
                    if data_col: novo_registro[data_col] = datetime.today().strftime('%d/%m/%Y')
                    for i, col in enumerate(dezenas_cols):
                        if i < 15: novo_registro[col] = selecionadas[i]
                    df_novo = pd.concat([df, pd.DataFrame([novo_registro])], ignore_index=True)
                    df_novo.to_csv(ARQUIVO_BASE, index=False, sep=';')
                    st.cache_data.clear()
                    st.success("✅ **Jogo Gravado! A memória matemática será resetada.**")
                    if os.path.exists("memoria_calculos"):
                        for f in os.listdir("memoria_calculos"): os.remove(os.path.join("memoria_calculos", f))
                    st.rerun() 
            elif (verificar or validar_listas or salvar_db): st.error("Selecione exatamente 15 dezenas no volante ao lado!")
            elif len(selecionadas) > 0: st.markdown(f"<div style='border: 1px dashed #D9D9D9; border-radius:4px; padding:10px; font-size:12px; color:#6A6D70; text-align:center;'>Suas dezenas: {', '.join([f'{d:02d}' for d in selecionadas])}</div>", unsafe_allow_html=True)
            else: st.caption("Complete 15 dezenas para habilitar as ações.")

    # ==========================================
    # SESSÃO INFERIOR: ÚLTIMOS RESULTADOS
    # ==========================================
    st.markdown('<div class="faixa-resultados">Últimos resultados da Lotofácil</div>', unsafe_allow_html=True)
    dezenas_cols = [col for col in df.columns if "Dezena" in col]
    if not dezenas_cols: dezenas_cols = df.columns[-15:]
    conc_col = next((c for c in df.columns if 'Concurso' in c or 'Sorteio' in c or 'N°' in c), None)
    data_col = next((c for c in df.columns if 'Data' in c), None)
    ultimos_3 = df.tail(3).iloc[::-1] 
    col_card1, col_card2, col_card3 = st.columns(3)
    colunas_cards = [col_card1, col_card2, col_card3]
    for i, (idx, row) in enumerate(ultimos_3.iterrows()):
        concurso = row[conc_col] if conc_col else "Desconhecido"
        data_sorteio = row[data_col] if data_col else "N/A"
        dezenas = row[dezenas_cols].dropna().astype(int).values
        bolinhas_html = "".join([f'<div class="bolinha-roxa">{d:02d}</div>' for d in dezenas])
        html_card = f"""
<div class="card-resultado">
<div class="card-resultado-header"><span>Concurso: {concurso}</span><span>Data: {data_sorteio}</span></div>
<div class="card-resultado-body">{bolinhas_html}</div>
</div>"""
        with colunas_cards[i]: st.markdown(html_card, unsafe_allow_html=True)
