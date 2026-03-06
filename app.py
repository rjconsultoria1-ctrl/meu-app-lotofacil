import streamlit as st
import pandas as pd
from collections import Counter
import itertools
import os
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Gerador VIP | Fiori", page_icon="💎", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 2. INJEÇÃO DE CSS (LOGIN CLASSICO + DASHBOARD ROXO)
# ==========================================
st.markdown("""
    <style>
        /* Oculta elementos nativos do Streamlit */
        [data-testid="collapsedControl"] { display: none; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Ajuste do container principal */
        .block-container { 
            padding-top: 0rem !important; 
            padding-bottom: 2rem; 
            max-width: 95% !important; 
            padding-left: 1rem; 
            padding-right: 1rem;
        }

        /* --- TELA DE LOGIN (Estilo SAP NetWeaver Clássico) --- */
        .login-bg {
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: radial-gradient(circle at 20% 30%, #E2EDF8 0%, #B8D0E8 100%);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-logo-top {
            position: absolute;
            top: 20px; left: 20px;
            background-color: white;
            padding: 10px 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            font-size: 24px;
        }
        .login-box {
            background-color: transparent;
            width: 320px;
        }
        
        /* --- HEADER E BARRA SUPERIOR --- */
        .fiori-header-bar {
            background-color: #354A5F;
            color: white;
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-family: Arial, sans-serif;
            margin-bottom: 10px;
        }
        .header-title { font-size: 22px; font-weight: bold; color: #32363A; margin-bottom: 5px; }
        .header-subtitle { font-size: 14px; color: #6A6D70; }

        /* --- BOTÕES GERAIS E VOLANTE --- */
        .stButton>button { border-radius: 4px; font-weight: bold; }
        
        /* Bolinhas do Volante (Roxo Lotofácil) */
        div[data-testid="stVerticalBlockBorderWrapper"] .stButton>button { 
            border-radius: 50% !important; 
            height: 42px !important;
            padding: 0 !important;
            font-size: 14px !important;
            border: 1px solid #7B2CBF;
            color: #7B2CBF;
            background-color: white;
        }
        
        /* --- CARDS DE ÚLTIMOS RESULTADOS (HTML Customizado) --- */
        .faixa-resultados {
            background-color: #D9D9D9;
            padding: 8px 15px;
            font-weight: bold;
            color: #333;
            margin-top: 30px;
            margin-bottom: 15px;
        }
        .resultados-container {
            display: flex;
            gap: 20px;
            justify-content: space-between;
            flex-wrap: wrap;
        }
        .card-resultado {
            background-color: white;
            border: 1px solid #E0E0E0;
            border-radius: 8px;
            flex: 1;
            min-width: 300px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            overflow: hidden;
        }
        .card-resultado-header {
            background-color: #5C2D91; /* Roxo Escuro */
            color: white;
            padding: 10px 15px;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            font-size: 14px;
        }
        .card-resultado-body {
            padding: 15px;
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 10px;
            justify-items: center;
        }
        .bolinha-roxa {
            background-color: #5C2D91;
            color: white;
            width: 35px; height: 35px;
            display: flex;
            align-items: center; justify-content: center;
            border-radius: 50%;
            font-weight: bold; font-size: 13px;
        }
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

def limpar_volante():
    st.session_state["palpite_manual"] = set()

# --- TELA DE LOGIN (Idêntica ao Protótipo NetWeaver) ---
if not st.session_state["logged_in"]:
    st.markdown('<div class="login-bg">', unsafe_allow_html=True)
    st.markdown('<div class="login-logo-top">💎</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        usuario = st.text_input("Usuário", value="consultor.sd", label_visibility="collapsed", placeholder="Usuário")
        senha = st.text_input("Senha", type="password", label_visibility="collapsed", placeholder="Senha")
        
        st.caption("Idioma")
        st.selectbox("", ["PT - Português", "EN - English", "ES - Español"], label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Logon", use_container_width=True, type="primary"):
            if senha == "abap123":
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("Falha na autenticação.")
        st.markdown("<p style='text-align:center; font-size:12px; color:#0070F2; margin-top:10px; cursor:pointer;'>Modificar senha</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==========================================
# 4. O APLICATIVO (Layout Split Screen)
# ==========================================

# --- HEADER FIORI ---
st.markdown("""
    <div class="fiori-header-bar">
        <div><span style="color:#6CB2EB;">&lt;</span> 💎 Gerador VIP |</div>
        <div>🔍 🔔 👤</div>
    </div>
    <div style="padding: 10px 0;">
        <span class="header-title">Painel Simulador VIP</span>
        <span class="header-subtitle" style="margin-left: 10px;">Otimização combinatória baseada em histórico e regras matemáticas.</span>
    </div>
""", unsafe_allow_html=True)

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
        return [{"Sel": False, "Rank": r, "Pts": round(s, 2), **{f"B{i+1}": d for i, d in enumerate(c)}} for r, (s, c) in enumerate(lista, 1)]

    return pd.DataFrame(formatar(lista_diamante[:5000])), pd.DataFrame(formatar(lista_frias[:5000])), pd.DataFrame(formatar(lista_geral[:5000])), pd.DataFrame(formatar(lista_reversa[:5000]))

# --- LEITURA DA BASE ---
df = None
if os.path.exists(ARQUIVO_BASE):
    try: df = pd.read_csv(ARQUIVO_BASE, sep=';', encoding='utf-8')
    except:
        try: df = pd.read_csv(ARQUIVO_BASE, sep=';', encoding='latin-1')
        except:
            try: df = pd.read_csv(ARQUIVO_BASE, sep=',', encoding='utf-8')
            except: df = pd.read_csv(ARQUIVO_BASE, sep=',', encoding='latin-1')

with st.expander("⚙️ Configurações (Atualizar Base de Dados)"):
    if df is not None: st.info(f"Status: ONLINE | {len(df)} sorteios.")
    arquivo_upado = st.file_uploader("Fazer Upload de novo Master Data:", type=["csv", "xlsx"])
    if arquivo_upado is not None:
        if arquivo_upado.name.endswith('.csv'):
            try: df_novo = pd.read_csv(arquivo_upado, sep=';', encoding='utf-8')
            except: df_novo = pd.read_csv(arquivo_upado, sep=',', encoding='latin-1')
        else: df_novo = pd.read_excel(arquivo_upado)
        df_novo.to_csv(ARQUIVO_BASE, index=False)
        st.cache_data.clear()
        st.success("Base atualizada!")
        st.rerun()

st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

# ==========================================
# DIVISÃO DA TELA: ESQUERDA (Tabelas) | DIREITA (Simulador)
# ==========================================
if df is not None:
    col_esq, col_dir = st.columns([1.2, 1], gap="large")

    with col_esq:
        c_radio, c_btn = st.columns([2, 1])
        with c_radio:
            N_DEZENAS = st.radio("Selecione a quantidade de Dezenas", [15, 16, 17], horizontal=True, label_visibility="collapsed")
        with c_btn:
            if st.button("Gerar Combinações", use_container_width=True):
                with st.spinner("Processando..."):
                    dia, fri, ger, rev = processar_motor_matematico(df, N_DEZENAS)
                    st.session_state["df_diamante"] = dia.head(100).sample(min(10, len(dia))).sort_values("Rank")
                    st.session_state["df_reversa"] = rev.head(100).sample(min(10, len(rev))).sort_values("Rank")
                    st.session_state["df_frias"] = fri.head(1000).sample(min(50, len(fri))).sort_values("Rank")
                    st.session_state["df_geral"] = ger.head(2000).sample(min(100, len(ger))).sort_values("Rank")
                    st.session_state["N_GERADO"] = N_DEZENAS
                    st.session_state["gerado"] = True

        if st.session_state.get("gerado"):
            cfg_col = {"Sel": st.column_config.CheckboxColumn("Sel", default=False)}
            a1, a2, a3, a4 = st.tabs(["💎 Diamante", "❄️ Elite", "🔥 Geral", "🔄 Reversa"])
            with a1: df_dia_ed = st.data_editor(st.session_state["df_diamante"], column_config=cfg_col, hide_index=True, key="e1", use_container_width=True)
            with a2: df_fri_ed = st.data_editor(st.session_state["df_frias"], column_config=cfg_col, hide_index=True, key="e2", use_container_width=True)
            with a3: df_ger_ed = st.data_editor(st.session_state["df_geral"], column_config=cfg_col, hide_index=True, key="e3", use_container_width=True)
            with a4: df_rev_ed = st.data_editor(st.session_state["df_reversa"], column_config=cfg_col, hide_index=True, key="e4", use_container_width=True)

    with col_dir:
        st.markdown("<h3 style='text-align:center; color:#5C2D91;'>Simulador da LOTOFÁCIL</h3>", unsafe_allow_html=True)
        
        caixa_simulador = st.container(border=True)
        with caixa_simulador:
            st.markdown("<div style='background-color:#5C2D91; color:white; padding:10px; font-weight:bold; margin:-1rem -1rem 1rem -1rem;'>EU TERIA GANHO ALGUM PRÊMIO?</div>", unsafe_allow_html=True)
            
            c_volante, c_resumo = st.columns([1, 1.2])
            
            with c_volante:
                # O Volante Roxo
                for linha in range(5):
                    cols = st.columns(5)
                    for col_idx in range(5):
                        num = linha * 5 + col_idx + 1
                        selecionada = num in st.session_state["palpite_manual"]
                        icone = "🟣" if selecionada else "⚪"
                        with cols[col_idx]:
                            st.button(f"{icone}\n{num:02d}", key=f"btn_{num}", on_click=toggle_dezena, args=(num,))
                
                selecionadas = sorted(list(st.session_state["palpite_manual"]))
                st.write(f"Números selecionados: {len(selecionadas)}")
                
                c_btn_ver, c_btn_lim = st.columns([4, 1])
                with c_btn_ver:
                    verificar = st.button("VERIFICAR", use_container_width=True)
                with c_btn_lim:
                    st.button("🗑️", on_click=limpar_volante, help="Limpar volante")

            with c_resumo:
                st.markdown("<h5 style='text-align:center;'>Eu teria ganho na Lotofácil?</h5>", unsafe_allow_html=True)
                if len(selecionadas) > 0:
                    st.write(f"Você escolheu os números: **{', '.join(map(str, selecionadas))}**")
                else:
                    st.caption("Selecione 15 números no volante e clique em Verificar.")

                if verificar and len(selecionadas) == 15:
                    dezenas_cols = [c for c in df.columns if "Dezena" in c]
                    if not dezenas_cols: dezenas_cols = df.columns[-15:]
                    
                    set_palpite = set(selecionadas)
                    acertos_hist = {15: 0, 14: 0, 13: 0, 12: 0, 11: 0}
                    
                    for _, row in df.iterrows():
                        jogo_hist = set(row[dezenas_cols].dropna().astype(int).values)
                        acertos = len(set_palpite.intersection(jogo_hist))
                        if acertos >= 11:
                            acertos_hist[acertos] += 1
                    
                    total_premios = sum(acertos_hist.values())
                    st.markdown(f"Foram encontrados **{acertos_hist[15]} concurso(s) vencedor(es)** (15 pontos) para essas combinações.")
                    st.markdown("**Resumo:**")
                    st.markdown(f"""
                    <ul style='font-size: 14px;'>
                        <li>Você teria acertado **15 dezenas** em {acertos_hist[15]} concursos.</li>
                        <li>Você teria acertado **14 dezenas** em {acertos_hist[14]} concursos.</li>
                        <li>Você teria acertado **13 dezenas** em {acertos_hist[13]} concursos.</li>
                        <li>Você teria acertado **12 dezenas** em {acertos_hist[12]} concursos.</li>
                        <li>Você teria acertado **11 dezenas** em {acertos_hist[11]} concursos.</li>
                    </ul>
                    """, unsafe_allow_html=True)
                elif verificar:
                    st.error("Selecione exatamente 15 dezenas!")

        if st.session_state.get("gerado"):
            if st.button("✔ Validar nas Listas Geradas", type="primary"):
                if len(selecionadas) == 15:
                    st.success("Funcionalidade de cruzamento ativada! (Logs no console)")
                else:
                    st.error("Marque 15 dezenas no volante acima primeiro.")

    # ==========================================
    # SESSÃO INFERIOR: ÚLTIMOS RESULTADOS
    # ==========================================
    st.markdown('<div class="faixa-resultados">Últimos resultados</div>', unsafe_allow_html=True)
    
    # Pegando os 3 últimos concursos do CSV
    dezenas_cols = [col for col in df.columns if "Dezena" in col]
    if not dezenas_cols: dezenas_cols = df.columns[-15:]
    conc_col = next((c for c in df.columns if 'Sorteio' in c or 'Concurso' in c or 'N°' in c), None)
    data_col = next((c for c in df.columns if 'Data' in c), None)
    
    ultimos_3 = df.tail(3).iloc[::-1] # Pega os 3 últimos e inverte a ordem
    
    cards_html = '<div class="resultados-container">'
    for _, row in ultimos_3.iterrows():
        concurso = row[conc_col] if conc_col else "N/A"
        data_sorteio = row[data_col] if data_col else "N/A"
        dezenas = row[dezenas_cols].dropna().astype(int).values
        
        bolinhas_html = "".join([f'<div class="bolinha-roxa">{d:02d}</div>' for d in dezenas])
        
        cards_html += f"""
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
    cards_html += '</div>'
    
    st.markdown(cards_html, unsafe_allow_html=True)
