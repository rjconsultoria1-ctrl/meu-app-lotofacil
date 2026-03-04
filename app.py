import streamlit as st
import pandas as pd
from collections import Counter
import itertools

st.set_page_config(page_title="Gerador Lotofácil VIP", page_icon="💎", layout="wide")

st.title("💎 Meu Gerador Lotofácil VIP - Múltiplas Estratégias")
st.write("Análise avançada dividida em 3 estratégias estatísticas distintas.")

st.sidebar.title("🔐 Área Restrita")
senha_digitada = st.sidebar.text_input("Digite a senha de acesso:", type="password")
senha_correta = "abap123"

if senha_digitada != senha_correta:
    st.warning("🔒 Por favor, insira a senha no menu lateral para liberar o sistema.")
else:
    st.sidebar.success("✅ Acesso Liberado!")
    
    st.subheader("📁 Passo 1: Atualize os Dados")
    arquivo_upado = st.file_uploader("Suba a sua planilha de sorteios", type=["csv", "xlsx"])
    
    if arquivo_upado is not None:
        try:
            if arquivo_upado.name.endswith('.csv'):
                df = pd.read_csv(arquivo_upado)
            else:
                df = pd.read_excel(arquivo_upado)
                
            st.success("Planilha carregada com sucesso!")
                
            st.subheader("🚀 Passo 2: Motores de Análise")
            
            if st.button("⚡ Processar as 3 Estratégias"):
                with st.spinner('Rodando 3 algoritmos simultâneos em 2 milhões de combinações. Aguarde...'):
                    
                    dezenas_cols = [col for col in df.columns if 'Dezena' in col]
                    if not dezenas_cols: 
                        dezenas_cols = df.columns[-15:]
                        
                    past_draws = [frozenset(row) for row in df[dezenas_cols].values]
                    all_numbers = df[dezenas_cols].values.flatten()
                    counts = Counter(all_numbers)
                    
                    invalid_16 = set()
                    todas_dezenas = set(range(1, 26))
                    for draw in past_draws:
                        for r in (todas_dezenas - draw):
                            invalid_16.add(draw | frozenset([r]))

                    primos = {2, 3, 5, 7, 11, 13, 17, 19, 23}
                    moldura = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
                    fibonacci = {1, 2, 3, 5, 8, 13, 21}

                    lista_geral = []
                    lista_frias = []
                    lista_diamante = []
                    
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
                            
                            # Estratégia Diamante
                            if (impares == 8 or impares == 9) and (5 <= qtd_primos <= 6) and (10 <= qtd_moldura <= 11) and (4 <= qtd_fibo <= 5) and (195 <= soma_total <= 220):
                                lista_diamante.append((freq_soma, sorted(list(f_comb))))

                            # Estratégia Frias
                            score_frias = (50000 - freq_soma) / 100.0
                            if impares == 8 and pares == 8: score_frias += 50
                            elif impares == 9 and pares == 7: score_frias += 40
                            if 5 <= qtd_primos <= 7: score_frias += 30
                            lista_frias.append((score_frias, sorted(list(f_comb))))

                            # Estratégia Geral
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

                    lista_diamante.sort(key=lambda x: x[0], reverse=True)
                    lista_frias.sort(key=lambda x: x[0], reverse=True)
                    lista_geral.sort(key=lambda x: x[0], reverse=True)
                    
                    top_10_diamante = lista_diamante[:10]
                    top_1000_frias = lista_frias[:1000]
                    top_5000_geral = lista_geral[:5000]
                    
                    def formatar_saida(lista_jogos):
                        return [{'Rank': rank, 'Pontuação': round(score, 2), **{f'B{i+1}': dez for i, dez in enumerate(comb)}} 
                                for rank, (score, comb) in enumerate(lista_jogos, 1)]

                    # Salvando no "cérebro" do app para não sumir
                    st.session_state['df_diamante'] = pd.DataFrame(formatar_saida(top_10_diamante))
                    st.session_state['df_frias'] = pd.DataFrame(formatar_saida(top_1000_frias))
                    st.session_state['df_geral'] = pd.DataFrame(formatar_saida(top_5000_geral))
                    st.session_state['gerado'] = True
                    
                    st.success("✅ Tripla Análise Concluída com Sucesso!")
                    
            # Só mostra as abas e o conferidor se as listas já foram geradas
            if st.session_state.get('gerado'):
                aba1, aba2, aba3 = st.tabs(["💎 Top 10 Diamante", "❄️ Top 1.000 Elite", "🔥 Top 5.000 Geral"])
                
                with aba1: st.dataframe(st.session_state['df_diamante'])
                with aba2: st.dataframe(st.session_state['df_frias'])
                with aba3: st.dataframe(st.session_state['df_geral'])

                # --- NOVIDADE: O CONFERIDOR DE MILHÕES ---
                st.markdown("---")
                st.subheader("🏆 Passo 3: Conferidor de Milhões")
                st.write("Digite as 15 dezenas do último sorteio da Caixa para descobrir se nossos motores bateram o prêmio máximo!")
                
                # Caixinha multiseleção limitando a 15 dezenas
                dezenas_sorteadas = st.multiselect("Selecione as exatas 15 dezenas sorteadas:", options=list(range(1, 26)), max_selections=15)
                
                if len(dezenas_sorteadas) == 15:
                    if st.button("🎰 Conferir Sorteio"):
                        set_sorteadas = set(dezenas_sorteadas)
                        
                        def conferir_lista(df, nome_lista):
                            for index, row in df.iterrows():
                                # Pega as 16 dezenas daquela linha
                                jogo = set(row[['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11', 'B12', 'B13', 'B14', 'B15', 'B16']].values)
                                
                                # Se as 15 sorteadas estão DENTRO do nosso jogo de 16, é prêmio máximo!
                                if set_sorteadas.issubset(jogo):
                                    st.balloons() # Chuva de balões na tela!
                                    st.success(f"🎉 **PARABÉNS!** Se você tivesse escolhido a sequência **Rank #{row['Rank']}** da planilha **{nome_lista}**, você seria um **VENCEDOR MILIONÁRIO**! 🤑")
                                    st.write(f"A sua aposta de 16 números daquela linha era: {sorted(list(jogo))}")
                                    return True
                            return False
                            
                        acertou = False
                        # Checa do Diamante para o Geral
                        if conferir_lista(st.session_state['df_diamante'], "💎 Top 10 Diamante"): acertou = True
                        elif conferir_lista(st.session_state['df_frias'], "❄️ Top 1.000 Elite"): acertou = True
                        elif conferir_lista(st.session_state['df_geral'], "🔥 Top 5.000 Geral"): acertou = True
                        
                        if not acertou:
                            st.info("Poxa, dessa vez o prêmio de 15 pontos não estava nas nossas listas. Mas os matemáticos não desistem!")

        except Exception as e:
            st.error(f"Poxa, deu um erro ao ler a planilha. Detalhe técnico: {e}")
