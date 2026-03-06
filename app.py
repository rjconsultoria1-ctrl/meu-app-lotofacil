import streamlit as st
import pandas as pd
from collections import Counter
import itertools
import os
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA (WIDE E ÍCONE)
# ==========================================
st.set_page_config(page_title="Gerador VIP | Fiori", page_icon="💎", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 2. INJEÇÃO DE CSS - TEMA SAP MORNING HORIZON & AJUSTES
# ==========================================
st.markdown("""
    <style>
        /* Esconde elementos nativos do Streamlit */
        [data-testid="collapsedControl"] { display: none; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Fundo e tipografia geral */
        .stApp { 
            background-color: #F4F4F6; 
            font-family: "72", "Helvetica Neue", Helvetica, Arial, sans-serif; 
        }
        
        /* Ajuste do container principal (Tirando margens nativas) */
        .block-container { 
            padding-top: 0rem !important; 
            padding-bottom: 2rem; 
            max-width: 100%; 
            padding-left: 0; 
            padding-right: 0;
        }

        /* --- SHELL BAR FIXA (Corrigido o Z-Index) --- */
        .fiori-shell {
            background-color: #354A5F;
            color: white;
            height: 48px;
            display: flex;
            align-items: center;
            padding: 0 2rem;
            box-shadow: 0 1px 4px rgba(0,0,0,0.2);
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            z-index: 999; /* Fica acima de tudo */
        }
        .fiori-shell-logo { font-weight: bold; font-size: 15px; letter-spacing: 0.5px; }
        
        /* Container do Botão de Logoff (Fixo no canto direito) */
        .logoff-container {
            position: fixed;
            top: 6px;
            right: 20px;
            z-index: 1000;
        }
        
        /* --- DYNAMIC PAGE HEADER --- */
        .fiori-header {
            background-color: white;
            padding: 1.5rem 2rem 1rem 2rem;
            box-shadow: inset 0 -1px 0 #D9D9D9;
            margin-bottom: 20px;
            margin-top: 48px; /* Empurra o conteúdo para baixo da Shell Bar */
        }
        .fiori-title { font-size: 22px; font-weight: bold; color: #1D2D3E; margin-bottom: 5px; }
        .fiori-subtitle { font-size: 14px; color: #556B82; }
        
        /* --- MARGENS LATERAIS (Respiro do Conteúdo) --- */
        .main-content { 
            padding: 0 5%; 
            max-width: 1400px; 
            margin: 0 auto; 
        }
        
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
        
        /* O Botão de Logoff precisa de um estilo mais discreto (transparente) */
        .logoff-container .stButton>button {
            background-color: transparent !important;
            border: 1px solid white !important;
            color: white !important;
            height: 34px !important;
            padding: 0 15px !important;
        }
        .logoff-container .stButton>button:hover {
            background-color: rgba(255,255,255,0.2) !important;
        }

        /* --- O VOLANTE (Bolinhas 🟢/⚪) --- 
           Pegando apenas o container com borda para não afetar o resto */
        div[data-testid="stVerticalBlockBorderWrapper"] .stButton>button { 
            background-color: white;
            color: #32363A;
            border: 1px solid #D9D9D9;
            height: 48px !important;
            border-radius: 50% !important; /* Retorno da bolinha perfeita */
            padding: 0px !important;
            font-size: 14px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        div[data-testid="stVerticalBlockBorderWrapper"] .stButton>button:hover {
            background-color: #E5F0FA;
            border-color: #0070F2;
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

# --- TELA DE LOGIN (Nossa Marca!) ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        # Container sem borda nativa para não bugar o CSS do Volante
        st.markdown("""
            <div style="background-color: white; padding: 3rem 2.5rem; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,20,50,0.1); text-align: center;">
                <h2 style='color:#0070F2; margin-bottom:5px;'>💎 Gerador VIP Lotofácil</h2>
                <p style='color:#556B82; font-size: 14px; margin-bottom: 20px;'>Acesso Restrito</p>
        """, unsafe_allow_html=True)
        
        st.text_input("Usuário", value="consultor.sd", disabled=True)
        senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Entrar", use_container_width=True):
            if senha == "abap123":
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("Falha na autenticação. Verifique suas credenciais.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# 4. O APLICATIVO FIORI (Pós-Login)
# ==========================================

# --- SHELL BAR FIXA E BOTÃO DE LOGOFF ---
st.markdown("""
    <div class="fiori-shell">
        <div class="fiori-shell-logo">🔷 SAP Fiori | Gerador VIP Lotofácil</div>
    </div>
""", unsafe_allow_html=True)

st.markdown('<div class="logoff-container">', unsafe_allow_html=True)
if st.button("Sair (Logoff)", key="btn_sair"):
    st.session_state["logged_in"] = False
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

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
        return [{"Selecionar": False, "Rank": r, "Pontuação": round(s, 2), **{f"B{i+1}": d for i, d in enumerate(c)}} for r, (s, c) in enumerate(lista, 1)]

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
        <div class="fiori-title">Painel de Otimização e Simulador VIP</div>
        <div class="fiori-subtitle">Otimização combinatória baseada em histórico e regras matemáticas.</div>
    </div>
""", unsafe_allow_html=True)

# Abre a margem espaçosa do Main Content
st.markdown('<div class="main-content">', unsafe_allow_html=True)

with st.expander("⚙️ Configurações (Atualizar Base de Dados)"):
    if df is not None: st.info(f"Status do Banco: ONLINE | {len(df)} sorteios sincronizados.")
    st.write("Fazer Upload de novo Master Data:")
    arquivo_upado = st.file_uploader("", type=["csv", "xlsx"], label_visibility="collapsed")
    if arquivo_upado is not None:
        if arquivo_upado.name.endswith('.csv'):
            try: df_novo = pd.read_csv(arquivo_upado, sep=';', encoding='utf-8')
            except: df_novo = pd.read_csv(arquivo_upado, sep=',', encoding='latin-1')
        else: df_novo = pd.read_excel(arquivo_upado)
        df_novo.to_csv(ARQUIVO_BASE, index=False)
        st.cache_data.clear()
        st.success("Base de dados atualizada com sucesso.")
        st.rerun()

if df is not None:
    col_filtro, col_btn = st.columns([3, 1])
    with col_filtro:
        N_DEZENAS = st.radio("Selecione o tamanho do jogo:", [15, 16, 17], horizontal=True)
    with col_btn:
        st.write("") 
        if st.button("▶ Gerar Combinações", use_container_width=True):
            with st.spinner("Processando combinações em background..."):
                dia_full, fri_full, ger_full, rev_full = processar_motor_matematico(df, N_DEZENAS)
                
                st.session_state["df_diamante"] = dia_full.head(100).sample(min(10, len(dia_full))).sort_values("Rank")
                st.session_state["df_reversa"] = rev_full.head(100).sample(min(10, len(rev_full))).sort_values("Rank")
                st.session_state["df_frias"] = fri_full.head(1000).sample(min(50, len(fri_full))).sort_values("Rank")
                st.session_state["df_geral"] = ger_full.head(2000).sample(min(100, len(ger_full))).sort_values("Rank")
                
                st.session_state["N_GERADO"] = N_DEZENAS
                st.session_state["gerado"] = True

    if st.session_state.get("gerado"):
        st.markdown(f"#### 📑 Resultados Gerados ({st.session_state['N_GERADO']} Dezenas)")
        
        cfg_coluna = {"Selecionar": st.column_config.CheckboxColumn("Selecionar", default=False)}
        aba1, aba2, aba3, aba4 = st.tabs(["💎 Diamante", "❄️ Elite", "🔥 Geral", "🔄 Reversa"])
        
        with aba1: df_diamante_edit = st.data_editor(st.session_state["df_diamante"], column_config=cfg_coluna, hide_index=True, key="ed_dia", use_container_width=True)
        with aba2: df_frias_edit = st.data_editor(st.session_state["df_frias"], column_config=cfg_coluna, hide_index=True, key="ed_fri", use_container_width=True)
        with aba3: df_geral_edit = st.data_editor(st.session_state["df_geral"], column_config=cfg_coluna, hide_index=True, key="ed_ger", use_container_width=True)
        with aba4: df_reversa_edit = st.data_editor(st.session_state["df_reversa"], column_config=cfg_coluna, hide_index=True, key="ed_rev", use_container_width=True)

    # ==========================================
    # VOLANTE INDEPENDENTE (Sempre Visível)
    # ==========================================
    st.markdown("---")
    st.markdown("#### 🛠️ Painel de Simulação Livre (Volante)")
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        volante = st.container(border=True) # A mágica do CSS acontece aqui dentro
        with volante:
            st.markdown("<p style='text-align: center; color: #556B82; font-weight: bold;'>Marque suas 15 dezenas abaixo</p>", unsafe_allow_html=True)
            for linha in range(5):
                cols = st.columns(5)
                for col_idx in range(5):
                    num = linha * 5 + col_idx + 1
                    selecionada = num in st.session_state["palpite_manual"]
                    icone = "🟢" if selecionada else "⚪"
                    with cols[col_idx]:
                        st.button(f"{icone}\n{num:02d}", key=f"btn_{num}", on_click=toggle_dezena, args=(num,), use_container_width=True)
    
    selecionadas = sorted(list(st.session_state["palpite_manual"]))
    st.caption(f"Dezenas apontadas ({len(selecionadas)}/15): " + " - ".join([f"{d:02d}" for d in selecionadas]))

    if len(selecionadas) == 15:
        col_acao1, col_acao2 = st.columns(2)
        
        with col_acao1:
            # A validação nas listas só funciona se as listas foram geradas!
            pode_validar = st.session_state.get("gerado", False)
            if st.button("✔ Validar nas Listas Geradas", use_container_width=True, disabled=not pode_validar):
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
                            
                            if row["Selecionar"]:
                                qtd_jogos_marcados += 1
                                if acertos > melhor_acerto_meus:
                                    melhor_acerto_meus = acertos
                                    mensagem_meus = f"{acertos} acertos no Jogo #{row['Rank']} ({nome_lista})."
                            else:
                                if acertos > melhor_acerto_sistema:
                                    melhor_acerto_sistema = acertos
                                    mensagem_sistema = f"{acertos} acertos no Jogo #{row['Rank']} ({nome_lista})."

                st.markdown("##### 📌 Desempenho (Sua Seleção)")
                if qtd_jogos_marcados == 0: st.warning("Nenhum item marcado nas listas acima.")
                else:
                    if melhor_acerto_meus >= 14: st.success(f"**[SUCESSO]** {mensagem_meus}")
                    elif melhor_acerto_meus >= 11: st.info(f"**[LUCRO]** Melhor jogo: {mensagem_meus}")
                    else: st.error(f"**[BAIXO]** Maior acerto: {melhor_acerto_meus}.")

                st.markdown("##### 🤖 Desempenho (Motor Base)")
                st.write(f"O motor de background (não selecionados) alcançou **{mensagem_sistema}**.")
            
            if not pode_validar:
                st.caption("Gere as combinações primeiro para usar este botão.")

        with col_acao2:
            # O Oráculo funciona sempre, independente de ter gerado combinações!
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
                        st.error(f"🚨 **[JOGO DUPLICADO]** Combinação já existente no Concurso **{conc}** ({data_s}). Aposta bloqueada por regra estatística!")
                        ja_sorteado = True
                        break
                if not ja_sorteado: st.success("✅ **[VALIDADO]** Combinação inédita. Liberado para aposta oficial.")

st.markdown('</div>', unsafe_allow_html=True)
