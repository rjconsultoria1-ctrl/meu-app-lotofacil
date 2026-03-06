import streamlit as st
import pandas as pd
from collections import Counter
import itertools
import os
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Gerador Lotofácil VIP", page_icon="💎", layout="wide")

# Injeção de CSS - Fundo, Ajustes e o visual do VOLANTE VIP
st.markdown("""
    <style>
        .stApp { background-color: #F0F8FF; }
        .block-container { padding-top: 4rem; padding-bottom: 2rem; }
        @media (max-width: 768px) {
            h1 {font-size: 1.8rem !important;}
            h2 {font-size: 1.4rem !important;}
            h3 {font-size: 1.2rem !important;}
            
            /* Forçar as bolinhas do volante a não empilharem no celular */
            div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stHorizontalBlock"] {
                flex-wrap: nowrap !important;
            }
            div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"] {
                min-width: 18% !important;
                padding: 2px !important;
            }
        }
        
        /* Deixar as bolinhas do volante redondas e padronizadas */
        div[data-testid="stVerticalBlockBorderWrapper"] .stButton>button { 
            border-radius: 50% !important; 
            height: 45px !important;
            padding: 0px !important;
            font-size: 14px !important;
            font-weight: bold;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)

ARQUIVO_BASE = "banco_dados.csv"

# --- CONTROLE DE SESSÃO ---
if "palpite_manual" not in st.session_state:
    st.session_state["palpite_manual"] = set()

def toggle_dezena(dezena):
    palpite = st.session_state["palpite_manual"]
    if dezena in palpite:
        palpite.remove(dezena)
    elif len(palpite) < 15:
        palpite.add(dezena)
    st.session_state["palpite_manual"] = palpite

# --- ÁREA RESTRITA E MENU LATERAL ---
st.sidebar.title("🔐 Login VIP")
senha_digitada = st.sidebar.text_input("Senha de acesso:", type="password")
senha_correta = "abap123"

if senha_digitada != senha_correta:
    st.warning("🔒 Por favor, insira a senha no menu lateral para liberar o sistema.")
    st.stop()
else:
    st.sidebar.success("✅ Acesso Liberado!")

with st.sidebar.expander("📁 Gestão do Banco de Dados", expanded=False):
    df = None
    if os.path.exists(ARQUIVO_BASE):
        try: df = pd.read_csv(ARQUIVO_BASE, sep=';', encoding='utf-8')
        except:
            try: df = pd.read_csv(ARQUIVO_BASE, sep=';', encoding='latin-1')
            except:
                try: df = pd.read_csv(ARQUIVO_BASE, sep=',', encoding='utf-8')
                except: df = pd.read_csv(ARQUIVO_BASE, sep=',', encoding='latin-1')
        st.success(f"Temos {len(df)} sorteios registrados.")
    
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
        # Limpa o cache automaticamente se o arquivo mudar!
        st.cache_data.clear()
        st.success("Nova base salva! Atualize a página.")

# ==========================================
# O CÉREBRO DA OPERAÇÃO (COM MEMÓRIA CACHE)
# ==========================================
@st.cache_data(show_spinner=False)
def processar_motor_matematico(df_dados, n_dezenas):
    """
    Esta função processa os milhões de cálculos.
    Como tem o @st.cache_data, se a base não mudar, ele puxa da memória em 0.01 segundos!
    """
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

    # Retorna o Banco de Dados Completo (Top 5000 de cada)
    return pd.DataFrame(formatar(lista_diamante[:5000])), pd.DataFrame(formatar(lista_frias[:5000])), pd.DataFrame(formatar(lista_geral[:5000])), pd.DataFrame(formatar(lista_reversa[:5000]))

# --- TELA PRINCIPAL ---
st.markdown("## 💎 Gerador Lotofácil VIP")

if df is not None:
    st.markdown("### 🚀 Passo 1: Motores de Análise")
    
    # Botão rebaixado para melhorar o fluxo
    N_DEZENAS = st.radio("Selecione a quantidade de dezenas para os jogos:", [15, 16, 17], horizontal=True)
    btn_processar = st.button("⚡ Processar Combinações", use_container_width=True)

    if btn_processar:
        with st.spinner(f"Acessando núcleo de processamento para {N_DEZENAS} números..."):
            # O sistema vai tentar puxar da Memória RAM. Se não tiver, ele calcula.
            dia_full, fri_full, ger_full, rev_full = processar_motor_matematico(df, N_DEZENAS)
            
            # --- O FATOR SURPRESA (Amostragem Aleatória) ---
            # Ele pega a "nata" das listas e sorteia algumas opções frescas para a tela
            st.session_state["df_diamante"] = dia_full.head(100).sample(min(10, len(dia_full))).sort_values("Rank")
            st.session_state["df_reversa"] = rev_full.head(100).sample(min(10, len(rev_full))).sort_values("Rank")
            st.session_state["df_frias"] = fri_full.head(1000).sample(min(50, len(fri_full))).sort_values("Rank")
            st.session_state["df_geral"] = ger_full.head(2000).sample(min(100, len(ger_full))).sort_values("Rank")
            
            st.session_state["N_GERADO"] = N_DEZENAS
            st.session_state["gerado"] = True

    if st.session_state.get("gerado"):
        st.markdown(f"### 📋 Listas de {st.session_state['N_GERADO']} Dezenas (Resultados Dinâmicos)")
        st.caption("As listas abaixo exibem seleções premium exclusivas. A cada processamento, novas combinações da elite serão sorteadas!")
        
        cfg_coluna = {"Jogar?": st.column_config.CheckboxColumn("Jogar?", default=False)}
        aba1, aba2, aba3, aba4 = st.tabs(["💎 Diamante", "❄️ Elite", "🔥 Geral", "🔄 Reversa"])
        
        with aba1: df_diamante_edit = st.data_editor(st.session_state["df_diamante"], column_config=cfg_coluna, hide_index=True, key="ed_dia", use_container_width=True)
        with aba2: df_frias_edit = st.data_editor(st.session_state["df_frias"], column_config=cfg_coluna, hide_index=True, key="ed_fri", use_container_width=True)
        with aba3: df_geral_edit = st.data_editor(st.session_state["df_geral"], column_config=cfg_coluna, hide_index=True, key="ed_ger", use_container_width=True)
        with aba4: df_reversa_edit = st.data_editor(st.session_state["df_reversa"], column_config=cfg_coluna, hide_index=True, key="ed_rev", use_container_width=True)

        st.markdown("---")
        
        # --- A NOVA CARTELA VIP (Volante Centralizado) ---
        st.markdown("### 🎯 Volante de Simulação")
        st.caption("Marque suas 15 dezenas no volante abaixo para conferir resultados ou histórico.")
        
        c1, c2, c3 = st.columns([1, 2, 1]) # O c2 é a nossa coluna central
        
        with c2:
            # st.container com border cria a caixinha sombreada bonita
            volante = st.container(border=True)
            with volante:
                st.markdown("<h4 style='text-align: center; margin-bottom: 20px;'>Volante Oficial</h4>", unsafe_allow_html=True)
                
                # Montando o grid de 5x5 perfeitamente
                for linha in range(5):
                    cols = st.columns(5)
                    for col_idx in range(5):
                        num = linha * 5 + col_idx + 1
                        selecionada = num in st.session_state["palpite_manual"]
                        icone = "🟢" if selecionada else "⚪"
                        with cols[col_idx]:
                            st.button(f"{icone}\n{num:02d}", key=f"btn_{num}", on_click=toggle_dezena, args=(num,), use_container_width=True)
        
        selecionadas = sorted(list(st.session_state["palpite_manual"]))
        st.write(f"**Dezenas selecionadas ({len(selecionadas)}/15):** " + " - ".join([f"{d:02d}" for d in selecionadas]))

        if len(selecionadas) == 15:
            col_acao1, col_acao2 = st.columns(2)
            
            with col_acao1:
                if st.button("🎰 Conferir nas minhas Listas", use_container_width=True):
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
                                        mensagem_meus = f"{acertos} acertos no jogo Rank #{row['Rank']} da lista {nome_lista}."
                                else:
                                    if acertos > melhor_acerto_sistema:
                                        melhor_acerto_sistema = acertos
                                        mensagem_sistema = f"{acertos} acertos no jogo Rank #{row['Rank']} da lista {nome_lista}."

                    st.markdown("#### 🎯 Desempenho dos SEUS Jogos")
                    if qtd_jogos_marcados == 0:
                        st.warning("Nenhum jogo marcado.")
                    else:
                        if melhor_acerto_meus >= 14: st.success(f"🎉 **ESPETACULAR!** {mensagem_meus}")
                        elif melhor_acerto_meus >= 11: st.info(f"👍 **LUCRO!** Melhor marcado: {mensagem_meus}")
                        else: st.error(f"📉 Maior acerto marcado: {melhor_acerto_meus}.")

                    st.markdown("#### 🤖 Desempenho do Sistema")
                    st.write(f"O motor alcançou **{mensagem_sistema}** nos outros jogos.")

            with col_acao2:
                if st.button("🔮 Consultar Oráculo (Histórico)", use_container_width=True):
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
                            st.error(f"🚨 **CUIDADO!** Esse jogo JÁ FOI SORTEADO no concurso **{conc}** ({data_s}). Fuja dele!")
                            ja_sorteado = True
                            break
                    if not ja_sorteado: st.success("✅ **EXCELENTE!** Combinação NUNCA sorteada na história.")
