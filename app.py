import streamlit as st
import pandas as pd
from collections import Counter
import itertools
import os
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA (WIDE E ÍCONE)
# ==========================================
st.set_page_config(page_title="SAP Fiori | Lotofácil", page_icon="🔷", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 2. INJEÇÃO DE CSS - TEMA SAP MORNING HORIZON
# ==========================================
st.markdown("""
    <style>
        /* Esconde elementos nativos do Streamlit (Menu, Sidebar, Footer) */
        [data-testid="collapsedControl"] { display: none; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Fundo e tipografia geral Fiori Horizon */
        .stApp { 
            background-color: #F4F4F6; 
            font-family: "72", "Helvetica Neue", Helvetica, Arial, sans-serif; 
        }
        
        /* Ajuste do container principal */
        .block-container { 
            padding-top: 0rem !important; 
            padding-bottom: 2rem; 
            max-width: 100%; 
            padding-left: 0; 
            padding-right: 0;
        }

        /* --- SHELL BAR --- */
        .fiori-shell {
            background-color: #354A5F;
            color: white;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 1rem;
            box-shadow: 0 1px 4px rgba(0,0,0,0.15);
        }
        .fiori-shell-logo { font-weight: bold; font-size: 14px; letter-spacing: 0.5px; }
        
        /* --- DYNAMIC PAGE HEADER --- */
        .fiori-header {
            background-color: white;
            padding: 1.5rem 2rem 1rem 2rem;
            box-shadow: inset 0 -1px 0 #D9D9D9;
            margin-bottom: 20px;
        }
        .fiori-title { font-size: 20px; font-weight: bold; color: #1D2D3E; margin-bottom: 5px; }
        .fiori-subtitle { font-size: 13px; color: #556B82; }
        
        /* --- BOTÕES PADRÃO FIORI --- */
        .stButton>button { 
            border-radius: 6px !important; 
            font-weight: bold;
            border: 1px solid #0070F2;
            color: white;
            background-color: #0070F2;
            transition: all 0.2s ease;
        }
        .stButton>button:hover { background-color: #0050B3; border-color: #0050B3; }
        
        /* Botões Secundários e Volante */
        div[data-testid="stVerticalBlockBorderWrapper"] .stButton>button { 
            background-color: white;
            color: #0070F2;
            border: 1px solid #0070F2;
            height: 40px !important;
            padding: 0px !important;
            font-size: 15px !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] .stButton>button:hover {
            background-color: #E5F0FA;
        }

        .main-content { padding: 0 2rem; }
    </style>
""", unsafe_allow_html=True)

ARQUIVO_BASE = "banco_dados.csv"

# ==========================================
# 3. CONTROLE DE SESSÃO E LOGIN
# ==========================================
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "palpite_manual" not in st.session_state: st.session_state["palpite_manual"] = set()

def toggle_dezena(dezena):
    palpite = st.session_state["palpite_manual"]
    if dezena in palpite: palpite.remove(dezena)
    elif len(palpite) < 15: palpite.add(dezena)
    st.session_state["palpite_manual"] = palpite

# --- TELA DE LOGIN CORRIGIDA (Streamlit Nativo) ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        login_box = st.container(border=True)
        with login_box:
            st.markdown("<h2 style='text-align:center; color:#0070F2; margin-bottom:0;'>🔷 SAP BTP</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:#556B82;'>Cloud Identity Services</p><hr>", unsafe_allow_html=True)
            
            st.text_input("User Name or Email", value="consultor.sd", disabled=True)
            senha = st.text_input("Password", type="password", placeholder="Enter your password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Log On", use_container_width=True):
                if senha == "abap123":
                    st.session_state["logged_in"] = True
                    st.rerun()
                else:
                    st.error("Authentication failed. Please check your credentials.")
    st.stop() # Trava tudo aqui até logar!

# ==========================================
# 4. O APLICATIVO FIORI (Pós-Login)
# ==========================================

# --- SHELL BAR ---
col_logo, col_logout = st.columns([10, 1])
with col_logo:
    st.markdown("""
        <div class="fiori-shell" style="position: absolute; top: 0; left: 0; width: 100vw; z-index: 100;">
            <div class="fiori-shell-logo">🔷 SAP | Predictive Analytics Cockpit</div>
        </div>
    """, unsafe_allow_html=True)
with col_logout:
    st.markdown("<div style='margin-top: 5px; position: absolute; right: 20px; z-index: 101;'>", unsafe_allow_html=True)
    if st.button("Logoff"):
        st.session_state["logged_in"] = False
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)

# --- CÉREBRO DA OPERAÇÃO (MEMÓRIA CACHE) ---
@st.cache_data(show_spinner=False)
def processar_motor_matematico(df_dados, n_dezenas):
    dezenas_cols = [col for col in df_dados.columns if "Dezena" in col]
    if not dezenas_cols: dezenas_cols = df_dados.columns[-15:]
    
    past_draws = [frozenset(row) for row in df_dados[dezenas_cols].dropna().astype(int).values]
    all_numbers = df_dados[dezenas_cols].dropna().astype(int).values.flatten()
    counts = Counter(all_numbers)
    ultimo_sorteio = past_draws[-1]

    if n_dezenas == 15:
        imp_d = [7, 8]; pri_d = [4, 5, 6]; mol_d = [9, 10, 11]; fib_d = [3, 4, 5]; soma_d = [180, 210]
    elif n_dezenas == 16:
        imp_d = [8, 9]; pri_d = [5, 6, 7]; mol_d = [10, 11]; fib_d = [4, 5]; soma_d = [195, 220]
    else:
        imp_d = [8, 9, 10]; pri_d = [5, 6, 7, 8]; mol_d = [11, 12, 13]; fib_d = [4, 5, 6]; soma_d = [210, 250]

    primos = {2, 3, 5, 7, 11, 13, 17, 19, 23}
    moldura = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
    fibonacci = {1, 2, 3, 5, 8, 13, 21}

    lista_geral, lista_frias, lista_diamante, lista_reversa = [], [], [], []

    for comb in itertools.combinations(range(1, 26), n_dezenas):
        f_comb = frozenset(comb)
        freq_soma = sum(counts[d] for d in f_comb)
        impares = sum(1 for d in f_comb if d % 2 != 0)
        qtd_primos = sum(1 for d in f_comb if d in primos)
        qtd_moldura = sum(1 for d in f_comb if d in moldura)
        qtd_fibo = sum(1 for d in f_comb if d in fibonacci)
        soma_total = sum(f_comb)
        repetidas_do_ultimo = len(f_comb.intersection(ultimo_sorteio))

        if (impares in imp_d) and (pri_d[0] <= qtd_primos <= pri_d[-1]) and (mol_d[0] <= qtd_moldura <= mol_d[-1]) and (fib_d[0] <= qtd_fibo <= fib_d[-1]) and (soma_d[0] <= soma_total <= soma_d[1]):
            lista_diamante.append((freq_soma, sorted(list(f_comb))))

        score_frias = (50000 - freq_soma) / 100.0
        if impares in imp_d: score_frias += 50
        if qtd_primos in pri_d: score_frias += 30
        lista_frias.append((score_frias, sorted(list(f_comb))))

        score_geral = freq_soma / 100.0
        if impares in imp_d: score_geral += 50
        else: score_geral -= 30
        if qtd_primos in pri_d: score_geral += 30
        else: score_geral -= 30
        lista_geral.append((score_geral, sorted(list(f_comb))))

        alvo_repetidas = 9 if n_dezenas == 15 else (10 if n_dezenas == 16 else 11)
        if repetidas_do_ultimo in [alvo_repetidas, alvo_repetidas+1]:
            lista_reversa.append((score_geral, sorted(list(f_comb))))

    lista_diamante.sort(key=lambda x: x[0], reverse=True)
    lista_frias.sort(key=lambda x: x[0], reverse=True)
    lista_geral.sort(key=lambda x: x[0], reverse=True)
    lista_reversa.sort(key=lambda x: x[0], reverse=True)

    def formatar(lista):
        return [{"Select": False, "Rank": r, "Score": round(s, 2), **{f"B{i+1}": d for i, d in enumerate(c)}} for r, (s, c) in enumerate(lista, 1)]

    return pd.DataFrame(formatar(lista_diamante[:5000])), pd.DataFrame(formatar(lista_frias[:5000])), pd.DataFrame(formatar(lista_geral[:5000])), pd.DataFrame(formatar(lista_reversa[:5000]))


# --- DYNAMIC PAGE HEADER E LÓGICA DE DADOS ---
df = None
if os.path.exists(ARQUIVO_BASE):
    try: df = pd.read_csv(ARQUIVO_BASE, sep=';', encoding='utf-8')
    except:
        try: df = pd.read_csv(ARQUIVO_BASE, sep=';', encoding='latin-1')
        except:
            try: df = pd.read_csv(ARQUIVO_BASE, sep=',', encoding='utf-8')
            except: df = pd.read_csv(ARQUIVO_BASE, sep=',', encoding='latin-1')

st.markdown("""
    <div class="fiori-header">
        <div class="fiori-title">Gerador Estratégico Lotofácil VIP</div>
        <div class="fiori-subtitle">Otimização combinatória baseada em histórico e regras matemáticas (Clean Core API).</div>
    </div>
""", unsafe_allow_html=True)

st.markdown('<div class="main-content">', unsafe_allow_html=True)

with st.expander("⚙️ Settings (Master Data Upload)"):
    if df is not None: st.info(f"Status do Banco: ONLINE | {len(df)} sorteios sincronizados.")
    st.write("Atualizar Base de Dados:")
    arquivo_upado = st.file_uploader("", type=["csv", "xlsx"], label_visibility="collapsed")
    if arquivo_upado is not None:
        if arquivo_upado.name.endswith('.csv'):
            try: df_novo = pd.read_csv(arquivo_upado, sep=';', encoding='utf-8')
            except: df_novo = pd.read_csv(arquivo_upado, sep=',', encoding='latin-1')
        else: df_novo = pd.read_excel(arquivo_upado)
        df_novo.to_csv(ARQUIVO_BASE, index=False)
        st.cache_data.clear()
        st.success("Master Data atualizado. Sincronização concluída.")
        st.rerun()

if df is not None:
    col_filtro, col_btn = st.columns([3, 1])
    with col_filtro:
        N_DEZENAS = st.radio("Selecione o Target (Tamanho do Jogo):", [15, 16, 17], horizontal=True)
    with col_btn:
        st.write("") 
        if st.button("▶ Execute Prediction", use_container_width=True):
            with st.spinner("Executing background job (In-Memory Processing)..."):
                dia_full, fri_full, ger_full, rev_full = processar_motor_matematico(df, N_DEZENAS)
                
                st.session_state["df_diamante"] = dia_full.head(100).sample(min(10, len(dia_full))).sort_values("Rank")
                st.session_state["df_reversa"] = rev_full.head(100).sample(min(10, len(rev_full))).sort_values("Rank")
                st.session_state["df_frias"] = fri_full.head(1000).sample(min(50, len(fri_full))).sort_values("Rank")
                st.session_state["df_geral"] = ger_full.head(2000).sample(min(100, len(ger_full))).sort_values("Rank")
                
                st.session_state["N_GERADO"] = N_DEZENAS
                st.session_state["gerado"] = True

    if st.session_state.get("gerado"):
        st.markdown(f"#### 📑 Results Object Page ({st.session_state['N_GERADO']} Dezenas)")
        
        cfg_coluna = {"Select": st.column_config.CheckboxColumn("Select", default=False)}
        aba1, aba2, aba3, aba4 = st.tabs(["💎 Diamante", "❄️ Elite", "🔥 Geral", "🔄 Reversa"])
        
        with aba1: df_diamante_edit = st.data_editor(st.session_state["df_diamante"], column_config=cfg_coluna, hide_index=True, key="ed_dia", use_container_width=True)
        with aba2: df_frias_edit = st.data_editor(st.session_state["df_frias"], column_config=cfg_coluna, hide_index=True, key="ed_fri", use_container_width=True)
        with aba3: df_geral_edit = st.data_editor(st.session_state["df_geral"], column_config=cfg_coluna, hide_index=True, key="ed_ger", use_container_width=True)
        with aba4: df_reversa_edit = st.data_editor(st.session_state["df_reversa"], column_config=cfg_coluna, hide_index=True, key="ed_rev", use_container_width=True)

        st.markdown("---")
        
        st.markdown("#### 🛠️ Object Simulation Panel")
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            volante = st.container(border=True)
            with volante:
                st.markdown("<p style='text-align: center; color: #556B82; font-weight: bold;'>Interactive Data Grid</p>", unsafe_allow_html=True)
                for linha in range(5):
                    cols = st.columns(5)
                    for col_idx in range(5):
                        num = linha * 5 + col_idx + 1
                        selecionada = num in st.session_state["palpite_manual"]
                        label = f"🟦 {num:02d}" if selecionada else f"⬜ {num:02d}"
                        with cols[col_idx]:
                            st.button(label, key=f"btn_{num}", on_click=toggle_dezena, args=(num,), use_container_width=True)
        
        selecionadas = sorted(list(st.session_state["palpite_manual"]))
        st.caption(f"Items selected ({len(selecionadas)}/15): " + " - ".join([f"{d:02d}" for d in selecionadas]))

        if len(selecionadas) == 15:
            col_acao1, col_acao2 = st.columns(2)
            
            with col_acao1:
                if st.button("✔ Validate Document", use_container_width=True):
                    set_sorteadas = set(selecionadas)
                    n_gerado = st.session_state['N_GERADO']
                    colunas_b = [f"B{i+1}" for i in range(n_gerado)]
                    
                    listas_para_conferir = [
                        ("💎 Diamante", df_diamante_edit), ("🔄 Reversa", df_reversa_edit),
                        ("❄️ Elite", df_frias_edit), ("🔥 Geral", df_geral_edit)
                    ]

                    melhor_acerto_meus, qtd_jogos_marcados, mensagem_meus = 0, 0, ""
                    melhor_acerto_sistema, mensagem_sistema = 0, ""

                    for nome_lista, df_lista in listas_para_conferir:
                        if not df_lista.empty:
                            for index, row in df_lista.iterrows():
                                jogo = set(row[colunas_b].values)
                                acertos = len(set_sorteadas.intersection(jogo))
                                
                                if row["Select"]:
                                    qtd_jogos_marcados += 1
                                    if acertos > melhor_acerto_meus:
                                        melhor_acerto_meus = acertos
                                        mensagem_meus = f"{acertos} matches in Document #{row['Rank']} ({nome_lista})."
                                else:
                                    if acertos > melhor_acerto_sistema:
                                        melhor_acerto_sistema = acertos
                                        mensagem_sistema = f"{acertos} matches in Document #{row['Rank']} ({nome_lista})."

                    st.markdown("##### 📌 User Selection Log")
                    if qtd_jogos_marcados == 0: st.warning("No items selected for validation.")
                    else:
                        if melhor_acerto_meus >= 14: st.success(f"**[CRITICAL SUCCESS]** {mensagem_meus}")
                        elif melhor_acerto_meus >= 11: st.info(f"**[ROI APPROVED]** Best document: {mensagem_meus}")
                        else: st.error(f"**[DEVIATION]** Max matches: {melhor_acerto_meus}.")

                    st.markdown("##### 🤖 Background Engine Log")
                    st.write(f"The unselected engine reached **{mensagem_sistema}**.")

            with col_acao2:
                if st.button("🔎 Master Data Query (History Check)", use_container_width=True):
                    set_palpite = set(selecionadas)
                    dezenas_cols = [col for col in df.columns if "Dezena" in col]
                    if not dezenas_cols: dezenas_cols = df.columns[-15:]
                    
                    concurso_col = next((c for c in df.columns if 'Sorteio' in c or 'Concurso' in c or 'N°' in c), None)
                    data_col = next((c for c in df.columns if 'Data' in c), None)
                    
                    ja_sorteado = False
                    for idx, row in df.iterrows():
                        jogo_hist = set(row[dezenas_cols].dropna().astype(int).values)
                        if set_palpite == jogo_hist:
                            conc = row[concurso_col] if concurso_col else f"Line {idx}"
                            data_s = row[data_col] if data_col else "Unknown"
                            st.error(f"🚨 **[DATA DUPLICATION ERROR]** Sequence found in Document **{conc}** ({data_s}). Execution blocked by statistical rules!")
                            ja_sorteado = True
                            break
                    if not ja_sorteado: st.success("✅ **[VALIDATION PASSED]** Sequence is unique. Ready for processing.")

st.markdown('</div>', unsafe_allow_html=True)
