import streamlit as st
import pandas as pd
from collections import Counter
import itertools

# Configuração da página
st.set_page_config(page_title="Gerador Lotofácil VIP", page_icon="🎲", layout="wide")

st.title("🎲 Meu Gerador Lotofácil VIP")
st.write("Bem-vindo ao seu sistema pessoal de análise estatística.")

# --- SISTEMA DE LOGIN SIMPLES ---
st.sidebar.title("🔐 Área Restrita")
senha_digitada = st.sidebar.text_input("Digite a senha de acesso:", type="password")
senha_correta = "abap123" # Pode mudar sua senha aqui!

if senha_digitada != senha_correta:
    st.warning("🔒 Por favor, insira a senha no menu lateral para liberar o sistema.")
else:
    st.sidebar.success("✅ Acesso Liberado!")
    
    # --- ÁREA DO APLICATIVO ---
    st.subheader("📁 Passo 1: Atualize os Dados")
    arquivo_upado = st.file_uploader("Suba a sua planilha de sorteios (CSV ou Excel)", type=["csv", "xlsx"])
    
    if arquivo_upado is not None:
        try:
            # Lê o arquivo dependendo da extensão
            if arquivo_upado.name.endswith('.csv'):
                df = pd.read_csv(arquivo_upado)
            else:
                df = pd.read_excel(arquivo_upado)
                
            st.success("Planilha carregada com sucesso!")
            with st.expander("Espiar os últimos sorteios lidos"):
                st.dataframe(df.tail(5)) # Mostra as 5 últimas linhas para conferência
                
            st.subheader("🚀 Passo 2: A Mágica Matemática")
            st.write("Clique no botão abaixo para avaliar todas as 2.042.975 combinações possíveis e extrair o ouro.")
            
            if st.button("⚡ Gerar Top 5.000 Melhores Jogos"):
                # Mostra uma barrinha de carregamento enquanto pensa
                with st.spinner('Calculando matrizes e cruzando histórico... Isso leva uns 5 a 10 segundos!'):
                    
                    # 1. Isola só as colunas das dezenas (ignora data, número do concurso, etc se houver)
                    # Vamos assumir que as dezenas estão nas últimas 15 colunas ou se chamam 'Dezena 1', etc.
                    # Para simplificar, vamos pegar as 15 colunas que contêm os números:
                    dezenas_cols = [col for col in df.columns if 'Dezena' in col]
                    if not dezenas_cols: # Se as colunas não tiverem o nome "Dezena", pega as últimas 15
                        dezenas_cols = df.columns[-15:]
                        
                    past_draws = [frozenset(row) for row in df[dezenas_cols].values]
                    all_numbers = df[dezenas_cols].values.flatten()
                    counts = Counter(all_numbers)
                    
                    # 2. Descobre quem já saiu
                    invalid_16 = set()
                    todas_dezenas = set(range(1, 26))
                    for draw in past_draws:
                        for r in (todas_dezenas - draw):
                            invalid_16.add(draw | frozenset([r]))

                    # 3. Avalia os 2 milhões
                    valid_scored = []
                    for comb in itertools.combinations(range(1, 26), 16):
                        f_comb = frozenset(comb)
                        if f_comb not in invalid_16:
                            # A nossa regra de pontos
                            score = sum(counts[d] / 100.0 for d in f_comb)
                            impares = sum(1 for d in f_comb if d % 2 != 0)
                            pares = 16 - impares
                            
                            if impares == 8 and pares == 8: score += 50
                            elif impares == 9 and pares == 7: score += 40
                            elif impares == 7 and pares == 9: score += 30
                            elif impares == 10 and pares == 6: score += 10
                            else: score -= 50
                            
                            valid_scored.append((score, sorted(list(f_comb))))

                    # 4. Ordena e pega os top 5.000 (reduzi para 5mil para ficar mais leve na tela)
                    valid_scored.sort(key=lambda x: x[0], reverse=True)
                    top_5k = valid_scored[:5000]

                    # 5. Prepara a tabela de saída
                    export_data = [{'Rank': rank, 'Score (Força)': round(score, 2), **{f'Bola {i+1}': dez for i, dez in enumerate(comb)}} 
                                   for rank, (score, comb) in enumerate(top_5k, 1)]
                    df_resultado = pd.DataFrame(export_data)
                    
                    st.success("✅ Análise Concluída com Sucesso!")
                    st.dataframe(df_resultado) # Mostra na tela
                    
                    # Botão para baixar o resultado
                    csv = df_resultado.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Baixar Resultados (CSV)",
                        data=csv,
                        file_name='Meus_Jogos_Ouro.csv',
                        mime='text/csv',
                    )
        except Exception as e:
            st.error(f"Poxa, deu um erro ao ler a planilha. Detalhe técnico: {e}")