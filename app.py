import streamlit as st
import pandas as pd
from collections import Counter
import itertools
import os
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Gerador VIP | SAP", page_icon="💎", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 2. INJEÇÃO DE CSS (ESTILIZAÇÃO TOTAL E RESPONSIVA)
# ==========================================
st.markdown("""
    <style>
        [data-testid="collapsedControl"] { display: none; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        
        .block-container { 
            padding-top: 0rem !important; 
            padding-bottom: 2rem; 
            max-width: 95% !important; 
            padding-left: 1rem; 
            padding-right: 1rem;
        }

        /* --- BARRA FIORI E BOTÃO SAIR --- */
        .fiori-header-bar {
            background-color: #354A5F; color: white; padding: 10px 20px;
            display: flex; justify-content: space-between; align-items: center;
            font-family: Arial, sans-serif; position: fixed;
            top: 0; left: 0; width: 100vw; z-index: 998;
            box-shadow: 0 1px 4px rgba(0,0,0,0.2);
        }
        .header-spacer { margin-top: 50px; }
        
        /* Container flutuante para o botão Sair real */
        .btn-sair-container {
            position: fixed; top: 4px; right: 20px; z-index: 1000;
        }
        .btn-sair-container .stButton > button {
            background-color: transparent !important; border: none !important;
            color: white !important; font-size: 14px; padding: 5px 10px !important;
            height: auto !important;
        }
        .btn-sair-container .stButton > button:hover {
            color: #6CB2EB !important; text-decoration: underline; background-color: transparent !important;
        }

        .page-title-section { padding: 10px 0; border-bottom: 1px solid #D9D9D9; margin-bottom: 15px; }
        .header-title { font-size: 22px; font-weight: bold; color: #32363A; }
        .header-subtitle { font-size: 14px; color: #6A6D70; }

        .stButton>button { border-radius: 4px; font-weight: bold; }
        .stButton>button[kind="primary"] { background-color: #5C2D91; border-color: #5C2D91; color: white; }
        .stButton>button[kind="primary"]:hover { background-color: #4A1E7A; border-color: #4A1E7A; }

        /* --- O VOLANTE ROXO E RESPONSIVIDADE MOBILE --- */
        /* Formata os botões do simulador (Grid 5x5) */
        div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"] .stButton > button { 
            border-radius: 50% !important; 
            height: 42px !important; width: 42px !important;
            padding: 0 !important; font-size: 15px !important;
            margin: auto; display: flex; justify-content: center; align-items: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.15) !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"] .stButton > button[kind="secondary"] {
            background-color: white !important; color: #5C2D91 !important; border: 2px solid #5C2D91 !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"] .stButton > button[kind="primary"] {
            background-color: #5C2D91 !important; color: white !important; border: 2px solid #5C2D91 !important;
        }

        /* Mágica Responsiva: Trava as 5 colunas do volante para NÃO empilharem no celular */
        @media (max-width: 640px) {
            /* Identifica colunas agrupadas de 5 (nosso volante) e força exibição em linha */
            div[data-testid="stHorizontalBlock"]:has(> div:nth-child(5)) {
                flex-wrap: nowrap !important;
                gap: 5px !important;
                justify-content: center;
            }
            div[data-testid="stHorizontalBlock"]:has(> div:nth-child(5)) > div[data-testid="column"] {
                width: 20% !important;
                flex: 1 1 20% !important;
                min-width: 0 !important;
            }
        }
        
        /* --- CARDS DE RESULTADOS --- */
        .faixa-resultados {
            background-color: #D9D9D9; padding: 10px 20px; font-weight: bold; color: #333;
            margin-top: 30px; margin-bottom: 15px; border-radius: 4px;
        }
        .card-resultado {
            background-color: white; border: 1px solid #E0E0E0; border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05); overflow: hidden; width: 100%;
        }
        .card-resultado-header {
            background-color: #5C2D91; color: white; padding: 12px 18px; font-weight: bold;
            display: flex; justify-content: space-between; font-size: 14px;
        }
        .card-resultado-body {
            padding: 15px; display: grid; grid-template-columns: repeat(5, 1fr);
            gap: 12px; justify-items: center;
        }
        .bolinha-roxa {
            background-color: #5C2D91; color: white; width: 38px; height: 38px;
            display: flex; align-items: center; justify-content: center;
            border-radius: 50%; font-weight: bold; font-size: 14px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.15);
        }
    </style>
""", unsafe_allow_html=True)

ARQUIVO_BASE = "banco_dados.csv"

# ==========================================
# 3. CONTROLE DE SESSÃO E LOGIN
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

def toggle_dezena(dezena):
    palpite = st.session_state["palpite_manual"]
    if dezena in palpite: palpite.remove(dezena)
    elif len(palpite) < 15: palpite.add(dezena)
    st.session_state["palpite_manual"] = palpite

def limpar_volante():
    st.session_state["palpite_manual"] = set()

# --- TELA DE LOGIN ---
if not st.session_state["logged_in"]:
    st.markdown("""
        <style>
            .stApp { background: radial-gradient(circle at 20% 30%, #E2EDF8 0%, #B8D0E8 100%); }
            .login-box { background-color: white; padding: 3rem; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,20,50,0.15); margin-top: -10vh; }
            .stSelectbox>div { background-color: white !important; }
        </style>
    """, unsafe_allow_html=True)
    st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.container(border=False):
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            st.markdown("<h2 style='text-align:center; color:#0070F2; margin-top:0;'>💎 Logon</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:#556B82; font-size: 14px; margin-bottom: 30px;'>Gerador VIP Lotofácil</p>", unsafe_allow_html=True)
            
            usuario = st.text_input("Usuário", value="consultor.sd", placeholder="Digite seu usuário")
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            st.caption("Idioma")
            st.selectbox("", ["PT - Português", "EN - English", "ES - Español"], label_visibility="collapsed")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Logon", use_container_width=True, type="secondary"):
                if senha == "abap123":
                    st.session_state["logged_in"] = True
                    st.rerun()
                else:
                    st.error("Falha na autenticação.")
            st.markdown("<p style='text-align:center; font-size:12px; color:#0070F2; margin-top:15px; cursor:pointer;'>Modificar senha / Ajuda</p>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==========================================
# 4. O APLICATIVO (Layout Analítico)
# ==========================================

# --- BARRA FIORI E BOTÃO SAIR (FUNCIONAL) ---
st.markdown("""
    <div class="fiori-header-bar">
        <div><span style="color:#6CB2EB;">💎 Gerador VIP</span> | Painel Simulador Lotofácil</div>
        <div>🔍 🔔 ⚙️ | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</div> </div>
    <div class="header-spacer"></div>
""", unsafe_allow_html=True)

# Botão Sair Real flutuando no topo direito
st.markdown('<div class="btn-sair-container">', unsafe_allow_html=True)
if st.button("Sair", key="btn_sair_topo"):
    st.session_state["logged_in"] = False
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
    <div class="page-title-section">
        <span class="header-title">Cockpit de Otimização e Simulador VIP</span>
        <span class="header-subtitle" style="margin-left: 15px;">Modelagem combinatória baseada em histórico de sorteios.</span>
    </div>
""", unsafe_allow_html=True)

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
        return [{"Sel": False, "Rank": r, "Pts": round(s, 2), **{f"B{i+1}": f"{d:02d}" for i, d in enumerate(c)}} for r, (s, c) in enumerate(lista, 1)]

    return pd.DataFrame(formatar(lista_diamante[:5000])), pd.DataFrame(formatar(lista_frias[:5000])), pd.DataFrame(formatar(lista_geral[:5000])), pd.DataFrame(formatar(lista_reversa[:5000]))

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
        st.success("Sincronização concluída.")
        st.rerun()

st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

# ==========================================
# DIVISÃO DA TELA: Tabelas (Esq) | Simulador (Dir)
# ==========================================
if df is not None:
    col_esq, col_dir = st.columns([1.2, 1], gap="large")

    with col_esq:
        c_radio, c_btn = st.columns([2, 1])
        with c_radio:
            N_DEZENAS = st.radio("Selecione a quantidade de Dezenas", [15, 16, 17], horizontal=True, label_visibility="collapsed")
        with c_btn:
            if st.button("▶ Gerar Combinações", use_container_width=True, type="secondary"):
                with st.spinner("Processando combinações em background..."):
                    dia, fri, ger, rev = processar_motor_matematico(df, N_DEZENAS)
                    st.session_state["df_diamante"] = dia.head(100).sample(min(10, len(dia))).sort_values("Rank")
                    st.session_state["df_reversa"] = rev.head(100).sample(min(10, len(rev))).sort_values("Rank")
                    st.session_state["df_frias"] = fri.head(1000).sample(min(50, len(fri))).sort_values("Rank")
                    st.session_state["df_geral"] = ger.head(2000).sample(min(100, len(ger))).sort_values("Rank")
                    st.session_state["N_GERADO"] = N_DEZENAS
                    st.session_state["gerado"] = True

        cfg_col = {"Sel": st.column_config.CheckboxColumn("Sel", default=False)}
        a1, a2, a3, a4 = st.tabs(["💎 Ranking Diamante", "❄️ Ranking Elite", "🔥 Ranking Geral", "🔄 Ranking Reversa"])
        with a1: df_dia_ed = st.data_editor(st.session_state["df_diamante"], column_config=cfg_col, hide_index=True, key="e1", use_container_width=True)
        with a2: df_fri_ed = st.data_editor(st.session_state["df_frias"], column_config=cfg_col, hide_index=True, key="e2", use_container_width=True)
        with a3: df_ger_ed = st.data_editor(st.session_state["df_geral"], column_config=cfg_col, hide_index=True, key="e3", use_container_width=True)
        with a4: df_rev_ed = st.data_editor(st.session_state["df_reversa"], column_config=cfg_col, hide_index=True, key="e4", use_container_width=True)

    with col_dir:
        st.markdown("<h3 style='text-align:center; color:#5C2D91; margin-top:0;'>Simulador da LOTOFÁCIL</h3>", unsafe_allow_html=True)
        
        caixa_simulador = st.container(border=True)
        with caixa_simulador:
            st.markdown("<div style='background-color:#5C2D91; color:white; padding:12px; font-weight:bold; margin:-1rem -1rem 1.5rem -1rem;'>EU TERIA GANHO ALGUM PRÊMIO?</div>", unsafe_allow_html=True)
            
            c_volante, c_resumo = st.columns([1, 1.2])
            
            with c_volante:
                # Volante com CSS injetado para travar no mobile
                for linha in range(5):
                    cols = st.columns(5)
                    for col_idx in range(5):
                        num = linha * 5 + col_idx + 1
                        selecionada = num in st.session_state["palpite_manual"]
                        tipo_btn = "primary" if selecionada else "secondary"
                        with cols[col_idx]:
                            st.button(f"{num:02d}", key=f"btn_{num}", type=tipo_btn, on_click=toggle_dezena, args=(num,))
                
                selecionadas = sorted(list(st.session_state["palpite_manual"]))
                st.markdown(f"<p style='text-align:center; font-size:12px; color:#6A6D70; margin-top:10px;'>Números selecionados: <b>{len(selecionadas)}/15</b></p>", unsafe_allow_html=True)
                
                # BOTOES DE AÇÃO
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1: verificar = st.button("Verificar Histórico", use_container_width=True, type="primary")
                with c_btn2: validar_listas = st.button("Validar nas Listas", use_container_width=True)
                
                c_btn3, c_btn4 = st.columns([4, 1])
                with c_btn3: salvar_db = st.button("💾 Gravar no Banco", use_container_width=True)
                with c_btn4: st.button("🗑️", on_click=limpar_volante, help="Limpar volante")

            with c_resumo:
                st.markdown("<h5 style='text-align:center; color:#32363A;'>Resumo do Palpite</h5>", unsafe_allow_html=True)
                
                # AÇÃO 1: VERIFICAR HISTÓRICO
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
                
                # AÇÃO 2: VALIDAR NAS LISTAS
                elif validar_listas and len(selecionadas) == 15:
                    if not st.session_state.get("gerado"):
                        st.warning("Gere as combinações nas tabelas ao lado primeiro!")
                    else:
                        set_sorteadas = set(selecionadas)
                        n_gerado = st.session_state['N_GERADO']
                        colunas_b = [f"B{i+1}" for i in range(n_gerado)]
                        
                        listas_para_conferir = [
                            ("💎 Diamante", df_dia_ed), ("🔄 Reversa", df_rev_ed),
                            ("❄️ Elite", df_fri_ed), ("🔥 Geral", df_ger_ed)
                        ]

                        melhor_acerto = 0
                        mensagem = ""
                        for nome_lista, df_lista in listas_para_conferir:
                            if not df_lista.empty:
                                for index, row in df_lista.iterrows():
                                    jogo = set([int(row[col]) for col in colunas_b])
                                    acertos = len(set_sorteadas.intersection(jogo))
                                    if acertos > melhor_acerto:
                                        melhor_acerto = acertos
                                        mensagem = f"{acertos} acertos na linha #{row['Rank']} da lista {nome_lista}."

                        if melhor_acerto >= 14: st.success(f"🎉 **CRUZAMENTO PERFEITO!** {mensagem}")
                        elif melhor_acerto >= 11: st.info(f"👍 **CRUZAMENTO POSITIVO:** {mensagem}")
                        else: st.error(f"📉 **FALHA:** Maior acerto nas listas geradas: {melhor_acerto}.")

                # AÇÃO 3: GRAVAR NO BANCO (COM ATUALIZAÇÃO EM TEMPO REAL)
                elif salvar_db and len(selecionadas) == 15:
                    dezenas_cols = [c for c in df.columns if "Dezena" in c]
                    if not dezenas_cols: dezenas_cols = df.columns[-15:]
                    
                    set_palpite = set(selecionadas)
                    ja_sorteado = False
                    for _, row in df.iterrows():
                        jogo_hist = set(row[dezenas_cols].dropna().astype(int).values)
                        if set_palpite == jogo_hist:
                            ja_sorteado = True
                            break
                    
                    if ja_sorteado:
                        st.error("🚨 **Este jogo já existe no banco de dados histórico!** Gravação bloqueada.")
                    else:
                        conc_col = next((c for c in df.columns if 'Concurso' in c or 'Sorteio' in c or 'N°' in c), None)
                        data_col = next((c for c in df.columns if 'Data' in c), None)
                        
                        novo_registro = {col: None for col in df.columns}
                        if conc_col: 
                            try: novo_registro[conc_col] = int(df[conc_col].max()) + 1
                            except: novo_registro[conc_col] = len(df) + 1
                        if data_col: 
                            novo_registro[data_col] = datetime.today().strftime('%d/%m/%Y')
                        
                        for i, col in enumerate(dezenas_cols):
                            if i < 15: novo_registro[col] = selecionadas[i]
                        
                        df_novo = pd.concat([df, pd.DataFrame([novo_registro])], ignore_index=True)
                        df_novo.to_csv(ARQUIVO_BASE, index=False, sep=';')
                        st.cache_data.clear()
                        st.success("✅ **Jogo Gravado com Sucesso! Atualizando painel...**")
                        # O GATILHO MÁGICO PARA ATUALIZAR OS CARDS NA HORA
                        st.rerun() 

                elif (verificar or validar_listas or salvar_db):
                    st.error("Selecione exatamente 15 dezenas no volante ao lado!")
                elif len(selecionadas) > 0:
                     st.markdown(f"<div style='border: 1px dashed #D9D9D9; border-radius:4px; padding:10px; font-size:12px; color:#6A6D70; text-align:center;'>Suas dezenas: {', '.join([f'{d:02d}' for d in selecionadas])}</div>", unsafe_allow_html=True)
                else:
                    st.caption("Complete 15 dezenas para habilitar as ações.")

    # ==========================================
    # SESSÃO INFERIOR: ÚLTIMOS RESULTADOS (Cards lado a lado)
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
<div class="card-resultado-header">
<span>Concurso: {concurso}</span>
<span>Data: {data_sorteio}</span>
</div>
<div class="card-resultado-body">
{bolinhas_html}
</div>
</div>
"""
        with colunas_cards[i]:
            st.markdown(html_card, unsafe_allow_html=True)
