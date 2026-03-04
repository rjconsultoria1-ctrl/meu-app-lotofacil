import streamlit as st
import pandas as pd
from collections import Counter
import itertools

# Configuração da página
st.set_page_config(page_title="Gerador Lotofácil VIP", page_icon="💎", layout="wide")

st.title("💎 Meu Gerador Lotofácil VIP - Edição Diamante")
st.write("Bem-vindo ao seu sistema de análise estatística com filtros avançados.")

# --- SISTEMA DE LOGIN SIMPLES ---
st.sidebar.title("🔐 Área Restrita")
senha_digitada = st.sidebar.text_input("Digite a senha de acesso:", type="password")
senha_correta = "abap123"

if senha_digitada != senha_correta:
    st.warning("🔒 Por favor, insira a senha no menu lateral para liberar o sistema.")
else:
    st.sidebar.success("✅ Acesso Liberado!")
    
    # --- ÁREA DO APLICATIVO ---
    st.subheader("📁 Passo 1: Atualize os Dados")
    arquivo_upado = st.file_uploader("Suba a sua planilha de sorteios (CSV ou Excel)", type=["csv", "xlsx"])
    
    if arquivo_upado is not None:
        try:
            if arquivo_upado.name.endswith('.csv'):
                df = pd.read_csv(arquivo_upado)
            else:
                df = pd.read_excel(arquivo_upado)
                
            st.success("Planilha carregada com sucesso!")
                
            st.subheader("🚀 Passo 2: O Motor de Regras Complexas")
            st.write("O algoritmo irá cruzar 2 milhões de combinações contra as 6 regras de ouro: Frequência, Pares/Ímpares, Primos, Moldura, Fibonacci e Soma.")
            
            if st.button("⚡ Gerar Quadros de Ouro (Top 10, 1.000 e 5.000)"):
                with st.spinner('Processando matrizes pesadas... O processador está fritando, isso pode levar até 1 minuto!'):
                    
                    # 1. Puxa as dezenas
                    dezenas_cols = [col for col in df.columns if 'Dezena' in col]
                    if not dezenas_cols: 
                        dezenas_cols = df.columns[-15:]
                        
                    past_draws = [frozenset(row) for row in df[dezenas_cols].values]
                    all_numbers = df[dezenas_cols].values.flatten()
                    counts = Counter(all_numbers)
                    
                    # 2. Elimina histórico
                    invalid_16 = set()
                    todas_dezenas = set(range(1, 26))
                    for draw in past_draws:
                        for r in (todas_dezenas - draw):
                            invalid_16.add(draw | frozenset([r]))

                    # --- CONJUNTOS MATEMÁTICOS ---
                    primos = {2, 3, 5, 7, 11, 13, 17, 19, 23}
                    moldura = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
                    fibonacci = {1, 2, 3, 5, 8, 13, 21}

                    valid_scored = []
                    
                    # 3. Varredura Total
                    for comb in itertools.combinations(range(1, 26), 16):
                        f_comb = frozenset(comb)
                        
                        if f_comb not in invalid_16:
                            # Regra 1: Frequência Histórica
                            score = sum(counts[d] / 100.0 for d in f_comb)
                            
                            # Regra 2: Pares e Ímpares
                            impares = sum(1 for d in f_comb if d % 2 != 0)
                            pares = 16 - impares
                            if impares == 8 and pares == 8: score += 50
                            elif impares == 9 and pares == 7: score += 40
                            else: score -= 30
                                
                            # Regra 3: Números Primos
                            qtd_primos = sum(1 for d in f_comb if d in primos)
                            if 5 <= qtd_primos <= 7: score += 30
                            else: score -= 30
                                
                            # Regra 4: Moldura
                            qtd_moldura = sum(1 for d in f_comb if d in moldura)
                            if 10 <= qtd_moldura <= 12: score += 30
                            else: score -= 30
                                
                            # Regra 5: Fibonacci
                            qtd_fibo = sum(1 for d in f_comb if d in fibonacci)
                            if 4 <= qtd_fibo <= 5: score += 20
                            else: score -= 20
                                
                            # Regra 6: Soma das Dezenas
                            soma_total = sum(f_comb)
                            if 195 <= soma_total <= 235: score += 20
                            else: score -= 40
                                
                            valid_scored.append((score, sorted(list(f_comb))))

                    # 4. Ordenação e Separação dos Quadros
                    valid_scored.sort(key=lambda x: x[0], reverse=True)
                    
                    top_5000 = valid_scored[:5000]
                    top_1000 = valid_scored[:1000]
                    top_10 = valid_scored[:10]
                    
                    # Função para transformar a lista em formato de tabela (DataFrame)
                    def formatar_saida(lista_jogos):
                        return [{'Rank': rank, 'Score Total': round(score, 2), **{f'B{i+1}': dez for i, dez in enumerate(comb)}} 
                                for rank, (score, comb) in enumerate(lista_jogos, 1)]

                    df_top_10 = pd.DataFrame(formatar_saida(top_10))
                    df_top_1000 = pd.DataFrame(formatar_saida(top_1000))
                    df_top_5000 = pd.DataFrame(formatar_saida(top_5000))
                    
                    st.success("✅ Análise Diamante Concluída com Sucesso!")
                    
                    # --- CRIANDO AS ABAS NA TELA ---
                    aba1, aba2, aba3 = st.tabs(["💎 Top 10 Diamante", "🥇 Top 1.000 Elite", "🥈 Top 5.000 Geral"])
                    
                    with aba1:
                        st.markdown("### Os 10 jogos matematicamente mais perfeitos")
                        st.write("Estas combinações gabaritaram TODAS as regras (Ímpares, Primos, Moldura, Fibonacci, Soma e Dezenas Quentes).")
                        st.dataframe(df_top_10)
                        st.download_button(label="📥 Baixar Top 10", data=df_top_10.to_csv(index=False).encode('utf-8'), file_name='Top_10_Diamante.csv', mime='text/csv')
                        
                    with aba2:
                        st.markdown("### O seleto grupo de Elite")
                        st.write("Mil jogos com altíssima viabilidade estatística.")
                        st.dataframe(df_top_1000)
                        st.download_button(label="📥 Baixar Top 1.000", data=df_top_1000.to_csv(index=False).encode('utf-8'), file_name='Top_1000_Elite.csv', mime='text/csv')
                        
                    with aba3:
                        st.markdown("### A Base Geral")
                        st.write("Os 5.000 melhores jogos filtrados a partir de 2 milhões de possibilidades.")
                        st.dataframe(df_top_5000)

        except Exception as e:
            st.error(f"Poxa, deu um erro ao ler a planilha. Detalhe técnico: {e}")
