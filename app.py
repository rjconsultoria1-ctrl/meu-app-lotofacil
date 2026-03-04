import streamlit as st
import pandas as pd
from collections import Counter
import itertools
import os
from datetime import datetime

st.set_page_config(page_title="Gerador Lotofácil VIP", page_icon="💎", layout="wide")

st.title("💎 Meu Gerador Lotofácil VIP - Múltiplas Estratégias")
st.write("Análise avançada com gestão de apostas, seleção de dezenas e Oráculo Histórico.")

ARQUIVO_BASE = "banco_dados.csv"

st.sidebar.title("🔐 Área Restrita")
senha_digitada = st.sidebar.text_input("Digite a senha de acesso:", type="password")
senha_correta = "abap123"

if senha_digitada != senha_correta:
    st.warning("🔒 Por favor, insira a senha no menu lateral para liberar o sistema.")
    st.stop()
else:
    st.sidebar.success("✅ Acesso Liberado!")

st.subheader("📁 Passo 1: Base de Dados")

df = None
col1, col2 = st.columns([2, 1])

with col1:
    if os.path.exists(ARQUIVO_BASE):
        try:
            df = pd.read_csv(ARQUIVO_BASE, sep=';', encoding='utf-8')
        except Exception:
            try:
                df = pd.read_csv(ARQUIVO_BASE, sep=';', encoding='latin-1')
            except Exception:
                try:
                    df = pd.read_csv(ARQUIVO_BASE, sep=',', encoding='utf-8')
                except Exception:
                    df = pd.read_csv(ARQUIVO_BASE, sep=',', encoding='latin-1')
                    
        st.info(f"📊 Base de dados automática carregada com sucesso! Temos **{len(df)} sorteios** registrados.")

with col2:
    with st.expander("🔄 Subir uma nova planilha manual"):
        arquivo_upado = st.file_uploader("Substituir base de dados", type=["csv", "xlsx"])
        if arquivo_upado is not None:
            if arquivo_upado.name.endswith('.csv'):
                try:
                    df = pd.read_csv(arquivo_upado, sep=';', encoding='utf-8')
                except Exception:
                    arquivo_upado.seek(0)
                    try:
                        df = pd.read_csv(arquivo_upado, sep=';', encoding='latin-1')
                    except Exception:
                        arquivo_upado.seek(0)
                        try:
                            df = pd.read_csv(arquivo_upado, sep=',', encoding='utf-8')
                        except Exception:
                            arquivo_upado.seek(0)
                            df = pd.read_csv(arquivo_upado, sep=',', encoding='latin-1')
            else:
                df = pd.read_excel(arquivo_upado)
            
            df.to_csv(ARQUIVO_BASE, index=False)
            st.success("Nova base salva no sistema! Recarregue a página.")

if df is not None:
    st.subheader("🚀 Passo 2: Motores de Análise")
    
    # --- NOVIDADE: SELETOR DE DEZENAS ---
    N_DEZENAS = st.radio("Selecione o tamanho da aposta que deseja gerar:", [15, 16, 17], horizontal=True)

    if st.button("⚡ Processar as 4 Estratégias"):
        with st.spinner(f"Cruzando milhões de combinações para jogos de {N_DEZENAS} números. Aguarde..."):

            dezenas_cols = [col for col in df.columns if "Dezena" in col]
            if not dezenas_cols:
                dezenas_cols = df.columns[-15:]

            past_draws = [frozenset(row) for row in df[dezenas_cols].dropna().astype(int).values]
            all_numbers = df[dezenas_cols].dropna().astype(int).values.flatten()
            counts = Counter(all_numbers)

            ultimo_sorteio = past_draws[-1]

            invalid_games = set()
            todas_dezenas = set(range(1, 26))
            
            # Ajuste de regras baseado no tamanho do jogo
            if N_DEZENAS == 15:
                imp_d = [7, 8]; pri_d = [4, 5, 6]; mol_d = [9, 10, 11]; fib_d = [3, 4, 5]; soma_d = [180, 210]
            elif N_DEZENAS == 16:
                imp_d = [8, 9]; pri_d = [5, 6, 7]; mol_d = [10, 11]; fib_d = [4, 5]; soma_d = [195, 220]
            else: # 17
                imp_d = [8, 9, 10]; pri_d = [5, 6, 7, 8]; mol_d = [11, 12, 13]; fib_d = [4, 5, 6]; soma_d = [210, 250]

            primos = {2, 3, 5, 7, 11, 13, 17, 19, 23}
            moldura = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
            fibonacci = {1, 2, 3, 5, 8, 13, 21}

            lista_geral, lista_frias, lista_diamante, lista_reversa = [], [], [], []

            for comb in itertools.combinations(range(1, 26), N_DEZENAS):
                f_comb = frozenset(comb)

                freq_soma = sum(counts[d] for d in f_comb)
                impares = sum(1 for d in f_comb if d % 2 != 0)
                pares = N_DEZENAS - impares
                qtd_primos = sum(1 for d in f_comb if d in primos)
                qtd_moldura = sum(1 for d in f_comb if d in moldura)
                qtd_fibo = sum(1 for d in f_comb if d in fibonacci)
                soma_total = sum(f_comb)
                repetidas_do_ultimo = len(f_comb.intersection(ultimo_sorteio))

                # Estratégia Diamante (Dinâmica)
                if (impares in imp_d) and (pri_d[0] <= qtd_primos <= pri_d[-1]) and (mol_d[0] <= qtd_moldura <= mol_d[-1]) and (fib_d[0] <= qtd_fibo <= fib_d[-1]) and (soma_d[0] <= soma_total <= soma_d[1]):
                    lista_diamante.append((freq_soma, sorted(list(f_comb))))

                # Estratégia Frias
                score_frias = (50000 - freq_soma) / 100.0
                if impares in imp_d: score_frias += 50
                if qtd_primos in pri_d: score_frias += 30
                lista_frias.append((score_frias, sorted(list(f_comb))))

                # Estratégia Geral
                score_geral = freq_soma / 100.0
                if impares in imp_d: score_geral += 50
                else: score_geral -= 30
                if qtd_primos in pri_d: score_geral += 30
                else: score_geral -= 30
                lista_geral.append((score_geral, sorted(list(f_comb))))

                # Estratégia Reversa
                alvo_repetidas = 9 if N_DEZENAS == 15 else (10 if N_DEZENAS == 16 else 11)
                if repetidas_do_ultimo in [alvo_repetidas, alvo_repetidas+1]:
                    lista_reversa.append((score_geral, sorted(list(f_comb))))

            lista_diamante.sort(key=lambda x: x[0], reverse=True)
            lista_frias.sort(key=lambda x: x[0], reverse=True)
            lista_geral.sort(key=lambda x: x[0], reverse=True)
            lista_reversa.sort(key=lambda x: x[0], reverse=True)

            def formatar_saida(lista_jogos):
                # Inclui a coluna 'Jogar?' como False
                return [{"Jogar?": False, "Rank": rank, "Pontuação": round(score, 2), **{f"B{i+1}": dez for i, dez in enumerate(comb)}}
                        for rank, (score, comb) in enumerate(lista_jogos, 1)]

            st.session_state["df_diamante"] = pd.DataFrame(formatar_saida(lista_diamante[:10]))
            st.session_state["df_frias"] = pd.DataFrame(formatar_saida(lista_frias[:1000]))
            st.session_state["df_geral"] = pd.DataFrame(formatar_saida(lista_geral[:5000]))
            st.session_state["df_reversa"] = pd.DataFrame(formatar_saida(lista_reversa[:10]))
            st.session_state["N_GERADO"] = N_DEZENAS
            st.session_state["gerado"] = True

            st.success("✅ Análise Concluída! Suas listas estão prontas abaixo.")

    if st.session_state.get("gerado"):
        st.write(f"### 📋 Listas de {st.session_state['N_GERADO']} Dezenas (Marque os jogos que você fará)")
        
        # --- NOVIDADE: DATA EDITOR COM CHECKBOX ---
        aba1, aba2, aba3, aba4 = st.tabs(["💎 Diamante", "❄️ Elite", "🔥 Geral", "🔄 Reversa"])
        
        cfg_coluna = {"Jogar?": st.column_config.CheckboxColumn("Jogar?", default=False)}

        with aba1:
            df_diamante_edit = st.data_editor(st.session_state["df_diamante"], column_config=cfg_coluna, hide_index=True, key="ed_diamante")
        with aba2:
            df_frias_edit = st.data_editor(st.session_state["df_frias"], column_config=cfg_coluna, hide_index=True, key="ed_frias")
        with aba3:
            df_geral_edit = st.data_editor(st.session_state["df_geral"], column_config=cfg_coluna, hide_index=True, key="ed_geral")
        with aba4:
            df_reversa_edit = st.data_editor(st.session_state["df_reversa"], column_config=cfg_coluna, hide_index=True, key="ed_reversa")

        st.markdown("---")
        st.subheader("🏆 Passo 3: Conferidor de Resultados Oficial")
        st.write("Digite as 15 dezenas do sorteio oficial da Caixa para verificar seu desempenho.")
        
        dezenas_sorteadas = st.multiselect("Selecione as exatas 15 dezenas sorteadas:", options=list(range(1, 26)), max_selections=15)

        if len(dezenas_sorteadas) == 15:
            if st.button("🎰 Conferir Sorteio"):
                set_sorteadas = set(dezenas_sorteadas)
                n_gerado = st.session_state['N_GERADO']
                colunas_b = [f"B{i+1}" for i in range(n_gerado)]
                
                listas_para_conferir = [
                    ("💎 Diamante", df_diamante_edit),
                    ("🔄 Reversa", df_reversa_edit),
                    ("❄️ Elite", df_frias_edit),
                    ("🔥 Geral", df_geral_edit),
                ]

                # Analisando Meus Jogos (Marcados)
                melhor_acerto_meus = 0
                qtd_jogos_marcados = 0
                mensagem_meus = ""
                
                # Analisando Sistema (Não Marcados)
                melhor_acerto_sistema = 0
                mensagem_sistema = ""

                for nome_lista, df_lista in listas_para_conferir:
                    if not df_lista.empty:
                        for index, row in df_lista.iterrows():
                            jogo = set(row[colunas_b].values)
                            acertos = len(set_sorteadas.intersection(jogo))
                            
                            if row["Jogar?"]: # Se o usuário marcou a caixinha
                                qtd_jogos_marcados += 1
                                if acertos > melhor_acerto_meus:
                                    melhor_acerto_meus = acertos
                                    mensagem_meus = f"{acertos} acertos no jogo Rank #{row['Rank']} da lista {nome_lista}."
                            else: # Jogos do sistema
                                if acertos > melhor_acerto_sistema:
                                    melhor_acerto_sistema = acertos
                                    mensagem_sistema = f"{acertos} acertos no jogo Rank #{row['Rank']} da lista {nome_lista}."

                # Exibindo resultado dos MEUS JOGOS
                st.markdown("#### 🎯 Desempenho dos SEUS Jogos (Marcados)")
                if qtd_jogos_marcados == 0:
                    st.warning("Você não marcou nenhum jogo nas caixinhas acima!")
                else:
                    if melhor_acerto_meus >= 14:
                        st.balloons()
                        st.success(f"🎉 **ESPETACULAR!** Você fez {mensagem_meus} 🤑")
                    elif melhor_acerto_meus >= 11:
                        st.info(f"👍 **LUCRO!** Dos {qtd_jogos_marcados} jogos que você marcou, seu melhor resultado foi: {mensagem_meus}")
                    else:
                        st.error(f"📉 Dos {qtd_jogos_marcados} jogos marcados, o maior acerto foi de apenas {melhor_acerto_meus}. Não deu prêmio.")

                # Exibindo resultado do RESTO DO SISTEMA
                st.markdown("#### 🤖 Desempenho Geral do Sistema (Não marcados)")
                st.write(f"Nas outras opções geradas, o motor matemático alcançou **{mensagem_sistema}**")

        st.markdown("---")
        # --- NOVIDADE: ORÁCULO HISTÓRICO ---
        st.subheader("🔮 Passo 4: O Oráculo (Consulta de Palpite Manual)")
        st.write("Tem um palpite próprio de 15 números? Descubra se ele já saiu na história da Lotofácil ou se está nas nossas listas quentes.")
        
        palpite_manual = st.multiselect("Digite as suas 15 dezenas do palpite:", options=list(range(1, 26)), max_selections=15, key="palpite")
        
        if len(palpite_manual) == 15:
            if st.button("🔍 Consultar Oráculo"):
                set_palpite = set(palpite_manual)
                
                # 1. Checa no Banco de Dados Histórico
                dezenas_cols = [col for col in df.columns if "Dezena" in col]
                if not dezenas_cols: dezenas_cols = df.columns[-15:]
                
                concurso_col = next((c for c in df.columns if 'Sorteio' in c or 'Concurso' in c or 'N°' in c), None)
                data_col = next((c for c in df.columns if 'Data' in c), None)
                
                ja_sorteado = False
                for idx, row in df.iterrows():
                    jogo_hist = set(row[dezenas_cols].dropna().astype(int).values)
                    if set_palpite == jogo_hist:
                        conc = row[concurso_col] if concurso_col else f"Linha {idx}"
                        data_s = row[data_col] if data_col else "Data Desconhecida"
                        st.error(f"🚨 **CUIDADO!** Essa combinação exata JÁ FOI SORTEADA ANTES no concurso **{conc}** (Data: {data_s}). Estatisticamente, a chance de um mesmo sorteio de 15 números se repetir é quase zero. Não recomendamos este jogo!")
                        ja_sorteado = True
                        break
                
                if not ja_sorteado:
                    st.success("✅ **EXCELENTE!** Essa sequência exata NUNCA foi sorteada na história da Lotofácil. É um jogo estatisticamente limpo!")
                
                # 2. Checa se o palpite está em alguma das nossas listas sugeridas
                n_gerado = st.session_state['N_GERADO']
                colunas_b = [f"B{i+1}" for i in range(n_gerado)]
                
                listas_para_conferir = [
                    ("💎 Diamante", df_diamante_edit),
                    ("🔄 Reversa", df_reversa_edit),
                    ("❄️ Elite", df_frias_edit),
                    ("🔥 Geral", df_geral_edit),
                ]
                
                encontrado_lista = False
                for nome_lista, df_lista in listas_para_conferir:
                    if not df_lista.empty:
                        for index, row in df_lista.iterrows():
                            jogo_sistema = set(row[colunas_b].values)
                            # Se as 15 escolhidas estiverem DENTRO do jogo do sistema (que pode ter 15, 16 ou 17)
                            if set_palpite.issubset(jogo_sistema):
                                st.info(f"🔥 **Sintonia!** O seu palpite está contido no jogo **Rank #{row['Rank']}** da lista **{nome_lista}** gerada hoje!")
                                encontrado_lista = True
                                break
                    if encontrado_lista: break
