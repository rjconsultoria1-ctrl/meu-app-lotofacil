import streamlit as st
import pandas as pd
from collections import Counter
import itertools
import os
from datetime import datetime

st.set_page_config(page_title="Gerador Lotofácil VIP", page_icon="💎", layout="wide")

st.title("💎 Meu Gerador Lotofácil VIP - Múltiplas Estratégias")
st.write("Análise avançada com banco de dados automático e engenharia reversa.")

ARQUIVO_BASE = 'banco_dados.csv' # Nome do nosso banco de dados interno

st.sidebar.title("🔐 Área Restrita")
senha_digitada = st.sidebar.text_input("Digite a senha de acesso:", type="password")
senha_correta = "abap123"

if senha_digitada != senha_correta:
    st.warning("🔒 Por favor, insira a senha no menu lateral para liberar o sistema.")
else:
    st.sidebar.success("✅ Acesso Liberado!")
    
st.subheader("📁 Passo 1: Base de Dados")
    
    # Lógica do Banco de Dados Automático
df = None
col1, col2 = st.columns([2, 1]) # <-- Essa linha cria o col1 e precisa existir!
    
with col1:
        if os.path.exists(ARQUIVO_BASE):
            try:
                # Tenta ler no padrão americano (vírgula)
                df = pd.read_csv(ARQUIVO_BASE, encoding='utf-8')
            except pd.errors.ParserError:
                # Se der erro de estrutura (Parser), tenta com ponto e vírgula (Padrão Excel Brasil)
                df = pd.read_csv(ARQUIVO_BASE, sep=';', encoding='utf-8')
            except UnicodeDecodeError:
                # Se der erro de sotaque (Unicode), tenta o padrão Windows/latin-1
                try:
                    df = pd.read_csv(ARQUIVO_BASE, sep=';', encoding='latin-1')
                except:
                    df = pd.read_csv(ARQUIVO_BASE, encoding='latin-1')
                    
            st.info(f"📊 Base de dados automática carregada com sucesso! Temos **{len(df)} sorteios** registrados.")
            
with col2:
        with st.expander("🔄 Subir uma nova planilha manual"):
            arquivo_upado = st.file_uploader("Substituir base de dados", type=["csv", "xlsx"])
            if arquivo_upado is not None:
                if arquivo_upado.name.endswith('.csv'):
                    try:
                        df = pd.read_csv(arquivo_upado, sep=';', encoding='utf-8')
                    except UnicodeDecodeError:
                        arquivo_upado.seek(0)
                        df = pd.read_csv(arquivo_upado, sep=';', encoding='latin-1')
                else:
                    df = pd.read_excel(arquivo_upado)
                df.to_csv(ARQUIVO_BASE, index=False)
                st.success("Nova base salva no sistema! Recarregue a página.")
    
if df is not None:
        st.subheader("🚀 Passo 2: Motores de Análise")
        
        if st.button("⚡ Processar as 4 Estratégias"):
            with st.spinner('Rodando algoritmos e cruzando 2 milhões de combinações. Aguarde...'):
                
                dezenas_cols = [col for col in df.columns if 'Dezena' in col]
                if not dezenas_cols: dezenas_cols = df.columns[-15:]
                    
                past_draws = [frozenset(row) for row in df[dezenas_cols].values]
                all_numbers = df[dezenas_cols].values.flatten()
                counts = Counter(all_numbers)
                
                ultimo_sorteio = past_draws[-1]
                
                invalid_16 = set()
                todas_dezenas = set(range(1, 26))
                for draw in past_draws:
                    for r in (todas_dezenas - draw):
                        invalid_16.add(draw | frozenset([r]))

                primos = {2, 3, 5, 7, 11, 13, 17, 19, 23}
                moldura = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
                fibonacci = {1, 2, 3, 5, 8, 13, 21}

                lista_geral, lista_frias, lista_diamante, lista_reversa = [], [], [], []
                
                for comb in itertools.combinations(range(1, 26), 16):
                    f_comb = frozenset(comb)
                    
                    if f_comb not in invalid_16:
                        freq_soma = sum(counts[d] for d in f_comb)
                        impares = sum(1 for d in f_comb if d % 2 != 0)
                        pares = 16 - impares
                        qtd_primos = sum(1 for d in f_comb if d in primos)
                        qtd_moldura = sum(1 for d in f_comb if d in moldura)
                        qtd_fibo = sum(1 for d in f_comb if d in fibonacci)
                        soma_total = sum(f_comb)
                        repetidas_do_ultimo = len(f_comb.intersection(ultimo_sorteio))
                        
                        if (impares == 8 or impares == 9) and (5 <= qtd_primos <= 6) and (10 <= qtd_moldura <= 11) and (4 <= qtd_fibo <= 5) and (195 <= soma_total <= 220):
                            lista_diamante.append((freq_soma, sorted(list(f_comb))))

                        score_frias = (50000 - freq_soma) / 100.0
                        if impares == 8 and pares == 8: score_frias += 50
                        elif impares == 9 and pares == 7: score_frias += 40
                        if 5 <= qtd_primos <= 7: score_frias += 30
                        lista_frias.append((score_frias, sorted(list(f_comb))))

                        score_geral = freq_soma / 100.0
                        if impares == 8 and pares == 8: score_geral += 50
                        elif impares == 9 and pares == 7: score_geral += 40
                        else: score_geral -= 30
                        if 5 <= qtd_primos <= 7: score_geral += 30
                        else: score_geral -= 30
                        if 10 <= qtd_moldura <= 12: score_geral += 30
                        else: score_geral -= 30
                        if 4 <= qtd_fibo <= 5: score_geral += 20
                        else: score_geral -= 20
                        if 195 <= soma_total <= 235: score_geral += 20
                        else: score_geral -= 40
                        lista_geral.append((score_geral, sorted(list(f_comb))))
                            
                        if repetidas_do_ultimo in [9, 10] and (195 <= soma_total <= 235) and (7 <= impares <= 9):
                            lista_reversa.append((score_geral, sorted(list(f_comb))))

                lista_diamante.sort(key=lambda x: x[0], reverse=True)
                lista_frias.sort(key=lambda x: x[0], reverse=True)
                lista_geral.sort(key=lambda x: x[0], reverse=True)
                lista_reversa.sort(key=lambda x: x[0], reverse=True)
                
                def formatar_saida(lista_jogos):
                    return [{'Rank': rank, 'Pontuação': round(score, 2), **{f'B{i+1}': dez for i, dez in enumerate(comb)}} 
                            for rank, (score, comb) in enumerate(lista_jogos, 1)]

                st.session_state['df_diamante'] = pd.DataFrame(formatar_saida(lista_diamante[:10]))
                st.session_state['df_frias'] = pd.DataFrame(formatar_saida(lista_frias[:1000]))
                st.session_state['df_geral'] = pd.DataFrame(formatar_saida(lista_geral[:5000]))
                st.session_state['df_reversa'] = pd.DataFrame(formatar_saida(lista_reversa[:10]))
                st.session_state['gerado'] = True
                
                st.success("✅ Quádrupla Análise Concluída com Sucesso!")
                
        if st.session_state.get('gerado'):
            aba1, aba2, aba3, aba4 = st.tabs(["💎 Top 10 Diamante", "❄️ Top 1.000 Elite", "🔥 Top 5.000 Geral", "🔄 Top 10 Engenharia Reversa"])
            
            with aba1: st.dataframe(st.session_state['df_diamante'])
            with aba2: st.dataframe(st.session_state['df_frias'])
            with aba3: st.dataframe(st.session_state['df_geral'])
            with aba4: st.dataframe(st.session_state['df_reversa'])

            st.markdown("---")
            st.subheader("🏆 Passo 3: Conferidor e Atualização do Banco")
            dezenas_sorteadas = st.multiselect("Selecione as exatas 15 dezenas sorteadas:", options=list(range(1, 26)), max_selections=15)
            
            if len(dezenas_sorteadas) == 15:
                # --- BOTÃO 1: CONFERIR ---
                if st.button("🎰 Conferir Sorteio com Nossas Listas"):
                    set_sorteadas = set(dezenas_sorteadas)
                    max_acertos = 0
                    melhor_jogo, melhor_rank, qual_lista = None, 0, ""
                    
                    listas_para_conferir = [
                        ("💎 Top 10 Diamante", st.session_state['df_diamante']),
                        ("🔄 Top 10 Reversa", st.session_state['df_reversa']),
                        ("❄️ Top 1.000 Elite", st.session_state['df_frias']),
                        ("🔥 Top 5.000 Geral", st.session_state['df_geral'])
                    ]
                    
                    for nome_lista, df_lista in listas_para_conferir:
                        if not df_lista.empty:
                            for index, row in df_lista.iterrows():
                                jogo = set(row[['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11', 'B12', 'B13', 'B14', 'B15', 'B16']].values)
                                acertos = len(set_sorteadas.intersection(jogo))
                                if acertos > max_acertos:
                                    max_acertos = acertos
                                    melhor_jogo = sorted(list(jogo))
                                    melhor_rank = row['Rank']
                                    qual_lista = nome_lista
                    
                    if max_acertos == 15:
                        st.balloons()
                        st.success(f"🎉 **PARABÉNS!** 15 ACERTOS CRAVADOS na lista **{qual_lista}** (Rank #{melhor_rank})! 🤑")
                        st.write(f"A sua aposta era: {melhor_jogo}")
                    elif max_acertos == 14:
                        st.warning(f"😱 **NA TRAVE!!!** Você acertou **14 números** na lista **{qual_lista}** (Rank #{melhor_rank})!")
                        st.write(f"A sua aposta era: {melhor_jogo}")
                    else:
                        st.info(f"O nosso maior acerto foi de {max_acertos} números na lista {qual_lista} (Rank #{melhor_rank}).")
                        st.write(f"A aposta era: {melhor_jogo}")

                st.markdown("---")
                # --- BOTÃO 2: SALVAR NO BANCO DE DADOS ---
                st.write("Esse sorteio já aconteceu? Adicione-o à nossa base de dados para as próximas análises da Engenharia Reversa!")
                if st.button("💾 Adicionar Sorteio ao Banco de Dados"):
                    dezenas_cols = [col for col in df.columns if 'Dezena' in col]
                    if not dezenas_cols: dezenas_cols = df.columns[-15:]
                    
                    ultimo_sorteio_base = set(df.iloc[-1][dezenas_cols].values)
                    
                    if set(dezenas_sorteadas) == ultimo_sorteio_base:
                        st.warning("⚠️ Este sorteio já é o último registrado na sua base de dados!")
                    else:
                        novo_id = df['N° Sorteio'].max() + 1 if 'N° Sorteio' in df.columns else len(df) + 1
                        data_hoje = datetime.now().strftime('%d/%m/%Y')
                        
                        novo_registro = {}
                        if 'N° Sorteio' in df.columns: novo_registro['N° Sorteio'] = novo_id
                        if 'Data Sorteio' in df.columns: novo_registro['Data Sorteio'] = data_hoje
                        
                        dezenas_ordenadas = sorted(list(dezenas_sorteadas))
                        for i, col in enumerate(dezenas_cols):
                            novo_registro[col] = dezenas_ordenadas[i]
                            
                        for col in df.columns:
                            if col not in novo_registro: novo_registro[col] = ''
                                
                        df_novo = pd.concat([df, pd.DataFrame([novo_registro])], ignore_index=True)
                        df_novo.to_csv(ARQUIVO_BASE, index=False)
                        st.success(f"✅ Sorteio #{novo_id} salvo com sucesso! O banco de dados foi atualizado. (Recarregue a página para analisar o novo cenário)")
