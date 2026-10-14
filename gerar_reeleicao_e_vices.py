import pandas as pd

print("--- INICIANDO PROCESSAMENTO OFICIAL DE PREFEITOS E VICES ---")

# 1. Obter prefeitos e vices que venceram no resultado final (1º ou 2º Turno)
print("1/3 - Lendo consulta_cand_2024_SP.csv...")
cand = pd.read_csv('consulta_cand_2024_SP.csv', sep=';', encoding='latin1', low_memory=False)

pref_eleitos = cand[(cand['CD_CARGO'] == 11) & (cand['DS_SIT_TOT_TURNO'] == 'ELEITO')].copy()
vices_eleitos = cand[(cand['CD_CARGO'] == 12) & (cand['DS_SIT_TOT_TURNO'] == 'ELEITO')].copy()

# 2. Ler complementar para a flag de Reeleição (ST_REELEICAO)
print("2/3 - Lendo consulta_cand_complementar_2024_SP.csv...")
comp = pd.read_csv('consulta_cand_complementar_2024_SP.csv', sep=';', encoding='latin1', low_memory=False)
comp_sub = comp[['SQ_CANDIDATO', 'ST_REELEICAO']].drop_duplicates(subset=['SQ_CANDIDATO'])

# Cruzar prefeito com a situação de reeleição
pref_merge = pref_eleitos.merge(comp_sub, on='SQ_CANDIDATO', how='left')

# 3. Cruzar com o Vice da mesma cidade (SG_UE)
vices_sub = vices_eleitos[['SG_UE', 'NM_URNA_CANDIDATO', 'SG_PARTIDO']].rename(
    columns={'NM_URNA_CANDIDATO': 'NM_VICE', 'SG_PARTIDO': 'SG_PARTIDO_VICE'}
).drop_duplicates(subset=['SG_UE'])

final_df = pref_merge.merge(vices_sub, on='SG_UE', how='left')

# Formatar colunas finais
final_df['CD_MUNICIPIO'] = final_df['SG_UE'].astype(int)
final_df['PREFEITO_ELEITO'] = final_df['NM_URNA_CANDIDATO'] + " (" + final_df['SG_PARTIDO'] + ")"
final_df['VICE_ELEITO'] = final_df['NM_VICE'].fillna('Não localizado') + " (" + final_df['SG_PARTIDO_VICE'].fillna('N/A') + ")"
final_df['VICE_E_MDB'] = final_df['SG_PARTIDO_VICE'].apply(lambda x: 'SIM' if str(x).strip().upper() == 'MDB' else 'NÃO')
final_df['APTO_REELEICAO_2028'] = final_df['ST_REELEICAO'].apply(
    lambda x: 'NÃO (Cumprindo 2º Mandato Consecutivo)' if str(x).strip().upper() == 'S' else 'SIM (Cumprindo 1º Mandato)'
)

tabela_final = final_df[['CD_MUNICIPIO', 'NM_UE', 'PREFEITO_ELEITO', 'VICE_ELEITO', 'VICE_E_MDB', 'APTO_REELEICAO_2028']].drop_duplicates(subset=['CD_MUNICIPIO'])
tabela_final.to_parquet('status_prefeitos_2028.parquet', index=False)

print(f"\n-> SUCESSO: status_prefeitos_2028.parquet gerado para {len(tabela_final)} cidades!")