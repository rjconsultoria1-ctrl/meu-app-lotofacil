import streamlit as st
import pandas as pd
from collections import Counter
import itertools
import os
from datetime import datetime

# Configuração da página (Layout Wide obrigatório para visual Fiori)
st.set_page_config(page_title="Cockpit Lotofácil", page_icon="🔷", layout="wide")

# ==========================================
# INJEÇÃO DE CSS - TEMA SAP FIORI (QUARTZ LIGHT)
# ==========================================
st.markdown("""
    <style>
        /* Fundo padrão do SAP Fiori */
        .stApp { background-color: #F4F4F6; font-family: "72", "Helvetica Neue", Helvetica, Arial, sans-serif; }
        
        /* Ajuste do container para anular a margem do Streamlit e colar a Shell Bar no topo */
        .block-container { padding-top: 0rem !important; padding-bottom: 2rem; max-width: 100%; padding-left: 0; padding-right: 0;}
        
        /* A famosa SAP Shell Bar */
        .fiori-shell {
            background-color: #0A6ED1;
            color: white;
            padding: 12px 24px;
            font-size: 1.1rem;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .fiori-shell-logo { display: flex; align-items: center; gap: 10px; }
        .fiori-shell-icons { font-size: 1.2rem; cursor: pointer; }
        
        /* Containers centrais com margem correta */
        .main-content { padding: 0 2rem; }
        
        /* KPI Cards (Tiles do Fiori) */
        .kpi-container { display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap; }
        .fiori-card {
            background-color: white;
            border-radius: 4px;
            padding: 15px 20px;
            box-shadow: 0 0 2px rgba(0,0,0,0.1), 0 2px 8px rgba(0,0,0,0.1);
            flex: 1;
            min-width: 200px;
            border-bottom: 4px solid #0A6ED1;
        }
        .fiori-card.green { border-bottom-color: #107E3E; }
        .fiori-card.orange { border-bottom-color: #E9730C; }
        
        .fiori-card h3 { margin: 0; font-size: 2.2rem; color: #32363A; padding-bottom: 5px;}
        .fiori-card p { margin: 0; font-size: 0.9rem; color: #6A6D70; }
        
        /* Estilização dos Botões Estilo SAP */
        .stButton>button { 
            border-radius: 4px !important; 
            font-weight: bold;
            border: 1px solid #0A6ED1;
            color: #0A6ED1;
            transition: all 0.2s;
        }
        .stButton>button:hover { background-color: #0A6ED1; color: white; }
        
        /* Bolinhas do Volante - Transformando em 'Tiles' Quadrados Arredondados Fiori */
        div[data-testid="stVerticalBlockBorderWrapper"] .stButton>button { 
            height: 45px !important;
            padding: 0px !important;
            font-size: 14px !important;
            background-color: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid #D9D9D9;
            color: #32363A;
        }
        
        @media (max-width: 768px) {
            .fiori-shell { font-size: 1rem; padding: 10px 15px; }
            .main-content { padding: 0 1rem; }
            div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; }
            div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"] { min-width: 18% !important; padding: 2px !important; }
        }
    </style>
""", unsafe_allow_html=True)

# Renderizando a Shell Bar do Fiori via HTML
st.markdown("""
    <div class="fiori-shell">
        <div class="fiori-shell-logo">
            <span>🔷 SAP BTP</span>
            <span style="font-weight: normal; margin-left: 10px;">| Cockpit de Automação Lotofácil</span>
        </div>
        <div class="fiori-shell-icons">
            🔍 🔔 ⚙️ 👤
        </div>
    </div>
""", unsafe_allow_html=True)

ARQUIVO_BASE = "banco_dados.csv"

# --- CONTROLE DE SESSÃO ---
if "palpite_manual" not in st.session_state: st.session_state["palpite_manual"] = set()

def toggle_dezena(dezena):
    palpite = st.session_state["palpite_manual"]
    if dezena in palpite: palpite.remove(dezena)
    elif len(palpite) < 15: palpite.add(dezena)
    st.session_state["palpite_manual"] = palpite

# Início do Container Principal (para aplicar o padding correto abaixo da Shell Bar)
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# --- ÁREA RESTRITA E MENU LATERAL ---
st.sidebar.title("🔐 Login SAP")
senha_digitada = st.sidebar.text_input("Senha de acesso:", type="password")
senha_correta = "abap123"

if senha_digitada != senha_correta:
    st.warning("🔒 Por favor, insira a senha no menu lateral para autenticação (SSO).")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()
else:
    st.sidebar.success("✅ Autenticado com sucesso")

with st.sidebar.expander("📁 Gestão de Master Data (Base CSV)", expanded=False):
    df = None
    if os.path.exists(ARQUIVO_BASE):
        try: df = pd.read_csv(ARQUIVO_BASE, sep=';', encoding='utf-8')
        except:
            try: df = pd.read_csv(ARQUIVO_BASE, sep=';', encoding='latin-1')
            except:
                try: df = pd.read_csv(ARQUIVO_BASE, sep=',', encoding='utf-8')
                except: df = pd.read_csv(ARQUIVO_BASE, sep=',', encoding='latin-1')
    
    st.write("Substituir base manual:")
    arquivo_upado = st.file_uploader("", type=["csv", "xlsx"])
    if arquivo_upado is not None:
        if arquivo_upado.name.endswith('.csv'):
            try: df = pd.read_csv(arquivo_upado, sep=';', encoding='utf-8')
            except:
                arquivo_upado.seek(0)
                try: df = pd.read_csv(arquivo_upado, sep=';', encoding='latin-1')
                except:
                    arquivo_upado.seek(0)
                    df = pd.read_csv(arquivo_upado, sep=',', encoding='utf-8')
        else:
            df = pd.read_excel(arquivo_upado)
        df.to_csv(ARQUIVO_BASE, index=False)
        st.cache_data.clear()
        st.success("Nova base salva! Atualize a página.")

# ==========================================
# CÉREBRO DA OPERAÇÃO (MEMÓRIA CACHE)
# ==========================================
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
        return [{"Jogar?": False, "Rank": r, "Pontuação": round(s, 2), **{f"B{i+1}": d for i, d in enumerate(c)}} for r, (s, c) in enumerate(lista, 1)]

    return pd.DataFrame(formatar(lista_diamante[:5000])), pd.DataFrame(formatar(lista_frias[:5000])), pd.DataFrame(formatar(lista_geral[:5000])), pd.DataFrame(formatar(lista_reversa[:5000]))

if df is not None:
    # Captura a dezena atual antes de desenhar os KPIs
    N_DEZENAS = st.radio("Filtro de Processamento (Qtd. Dezenas):", [15, 16, 17], horizontal=True)
    
    qtd_sorteios = len(df)
    status_memoria = "Ativo" if st.session_state.get("gerado") else "Aguardando"
    cor_memoria = "green" if st.session_state.get("gerado") else "orange"

    # --- KPI TILES (CARDS FIORI) ---
    st.markdown(f"""
        <div class="kpi-container">
            <div class="fiori-card">
                <h3>{qtd_sorteios}</h3>
                <p>Sorteios Master Data</p>
            </div>
            <div class="fiori-card">
                <h3>{N_DEZENAS}</h3>
                <p>Dezenas Selecionadas</p>
            </div>
            <div class="fiori-card {cor_memoria}">
                <h3>{status_memoria}</h3>
                <p>Status do Motor BTP</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    btn_processar = st.button("▶ Executar Background Job", use_container_width=True)

    if btn_processar:
        with st.spinner(f"Processando algoritmo em background (Job {N_DEZENAS})..."):
            dia_full, fri_full, ger_full, rev_full = processar_motor_matematico(df, N_DEZENAS)
            
            st.session_state["df_diamante"] = dia_full.head(100).sample(min(10, len(dia_full))).sort_values("Rank")
            st.session_state["df_reversa"] = rev_full.head(100).sample(min(10, len(rev_full))).sort_values("Rank")
            st.session_state["df_frias"] = fri_full.head(1000).sample(min(50, len(fri_full))).sort_values("Rank")
            st.session_state["df_geral"] = ger_full.head(2000).sample(min(100, len(ger_full))).sort_values("Rank")
            
            st.session_state["N_GERADO"] = N_DEZENAS
            st.session_state["gerado"] = True
            st.rerun() # Atualiza os KPIs automaticamente

    if st.session_state.get("gerado"):
        st.markdown(f"#### 📊 Monitor de Documentos ({st.session_state['N_GERADO']} Dezenas)")
        
        cfg_coluna = {"Jogar?": st.column_config.CheckboxColumn("Jogar?", default=False)}
        aba1, aba2, aba3, aba4 = st.tabs(["💎 Estratégia Diamante", "❄️ Estratégia Elite", "🔥 Estratégia Geral", "🔄 Estratégia Reversa"])
        
        with aba1: df_diamante_edit = st.data_editor(st.session_state["df_diamante"], column_config=cfg_coluna, hide_index=True, key="ed_dia", use_container_width=True)
        with aba2: df_frias_edit = st.data_editor(st.session_state["df_frias"], column_config=cfg_coluna, hide_index=True, key="ed_fri", use_container_width=True)
        with aba3: df_geral_edit = st.data_editor(st.session_state["df_geral"], column_config=cfg_coluna, hide_index=True, key="ed_ger", use_container_width=True)
        with aba4: df_reversa_edit = st.data_editor(st.session_state["df_reversa"], column_config=cfg_coluna, hide_index=True, key="ed_rev", use_container_width=True)

        st.markdown("---")
        
        st.markdown("#### ⚙️ Simulação e Oráculo (Conferência)")
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            volante = st.container(border=True)
            with volante:
                st.markdown("<h5 style='text-align: center; color: #32363A; margin-bottom: 15px;'>Grid de Entrada de Dezenas</h5>", unsafe_allow_html=True)
                for linha in range(5):
                    cols = st.columns(5)
                    for col_idx in range(5):
                        num = linha * 5 + col_idx + 1
                        selecionada = num in st.session_state["palpite_manual"]
                        icone = "🟩" if selecionada else "⬜"
                        with cols[col_idx]:
                            st.button(f"{icone}\n{num:02d}", key=f"btn_{num}", on_click=toggle_dezena, args=(num,), use_container_width=True)
        
        selecionadas = sorted(list(st.session_state["palpite_manual"]))
        st.caption(f"Dezenas apontadas ({len(selecionadas)}/15): " + " - ".join([f"{d:02d}" for d in selecionadas]))

        if len(selecionadas) == 15:
            col_acao1, col_acao2 = st.columns(2)
            
            with col_acao1:
                if st.button("✔ Validar nas Listas Atuais", use_container_width=True):
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
                                
                                if row["Jogar?"]:
                                    qtd_jogos_marcados += 1
                                    if acertos > melhor_acerto_meus:
                                        melhor_acerto_meus = acertos
                                        mensagem_meus = f"{acertos} acertos no documento #{row['Rank']} da {nome_lista}."
                                else:
                                    if acertos > melhor_acerto_sistema:
                                        melhor_acerto_sistema = acertos
                                        mensagem_sistema = f"{acertos} acertos no documento #{row['Rank']} da {nome_lista}."

                    st.markdown("##### 🎯 Log de Execução (Meus Jogos)")
                    if qtd_jogos_marcados == 0: st.warning("Nenhum item marcado para processamento.")
                    else:
                        if melhor_acerto_meus >= 14: st.success(f"🎉 **[SUCESSO EXTREMO]** {mensagem_meus}")
                        elif melhor_acerto_meus >= 11: st.info(f"👍 **[LUCRO APROVADO]** Melhor marcado: {mensagem_meus}")
                        else: st.error(f"📉 **[FALHA]** Maior acerto marcado: {melhor_acerto_meus}.")

                    st.markdown("##### 🤖 Log de Execução (Sistema Geral)")
                    st.write(f"O motor de background alcançou **{mensagem_sistema}**.")

            with col_acao2:
                if st.button("🔎 Consultar Oráculo (Banco Histórico)", use_container_width=True):
                    set_palpite = set(selecionadas)
                    dezenas_cols = [col for col in df.columns if "Dezena" in col]
                    if not dezenas_cols: dezenas_cols = df.columns[-15:]
                    
                    concurso_col = next((c for c in df.columns if 'Sorteio' in c or 'Concurso' in c or 'N°' in c), None)
                    data_col = next((c for c in df.columns if 'Data' in c), None)
                    
                    ja_sorteado = False
                    for idx, row in df.iterrows():
                        jogo_hist = set(row[dezenas_cols].dropna().astype(int).values)
                        if set_palpite == jogo_hist:
                            conc = row[concurso_col] if concurso_col else f"Linha {idx}"
                            data_s = row[data_col] if data_col else "Desconhecida"
                            st.error(f"🚨 **[ALERTA DE DUPLICIDADE]** Ordem já existente no concurso **{conc}** ({data_s}). Jogo bloqueado por validação estatística!")
                            ja_sorteado = True
                            break
                    if not ja_sorteado: st.success("✅ **[VALIDAÇÃO OK]** Combinação inédita liberada para processamento.")

# Fim do main-content
st.markdown('</div>', unsafe_allow_html=True)
