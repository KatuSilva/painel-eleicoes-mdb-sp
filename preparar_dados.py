import os
import pandas as pd

print("--- INICIANDO PROCESSAMENTO DE DADOS COM PANDAS ---")

def achar_coluna(colunas_disponiveis, opcoes):
    for op in opcoes:
        if op in colunas_disponiveis:
            return op
    return None

# ==============================================================
# 1. PROCESSAR DETALHES 2024
# ==============================================================
print("1/3 - Processando Detalhe 2024...")
df_det = pd.read_csv('detalhe_votacao_munzona_2024_SP.csv', sep=';', encoding='latin1')
df_det = df_det[df_det['NR_TURNO'] == 1]

agrup_det = df_det.groupby(['CD_MUNICIPIO', 'NM_MUNICIPIO', 'CD_CARGO', 'DS_CARGO'], as_index=False).agg({
    'QT_APTOS': 'sum',
    'QT_COMPARECIMENTO': 'sum',
    'QT_ABSTENCOES': 'sum',
    'QT_TOTAL_VOTOS_VALIDOS': 'sum',
    'QT_VOTOS_BRANCOS': 'sum',
    'QT_TOTAL_VOTOS_NULOS': 'sum'
}).rename(columns={
    'QT_APTOS': 'TOTAL_APTOS',
    'QT_COMPARECIMENTO': 'TOTAL_COMPARECIMENTO',
    'QT_ABSTENCOES': 'TOTAL_ABSTENCOES',
    'QT_TOTAL_VOTOS_VALIDOS': 'TOTAL_VALIDOS',
    'QT_VOTOS_BRANCOS': 'TOTAL_BRANCOS',
    'QT_TOTAL_VOTOS_NULOS': 'TOTAL_NULOS'
})
agrup_det.to_parquet('detalhe_2024.parquet', index=False)
print("-> detalhe_2024.parquet gerado com sucesso!")

# ==============================================================
# 2. PROCESSAR CANDIDATOS 2024
# ==============================================================
print("2/3 - Processando Candidatos 2024...")
df_cand24 = pd.read_csv('votacao_candidato_munzona_2024_SP.csv', sep=';', encoding='latin1')
df_cand24 = df_cand24[df_cand24['NR_TURNO'] == 1]

agrup_cand24 = df_cand24.groupby(
    ['CD_MUNICIPIO', 'NM_MUNICIPIO', 'CD_CARGO', 'DS_CARGO', 'NM_CANDIDATO', 'NM_URNA_CANDIDATO', 'SG_PARTIDO', 'DS_SIT_TOT_TURNO'],
    as_index=False
)['QT_VOTOS_NOMINAIS'].sum().rename(columns={'QT_VOTOS_NOMINAIS': 'VOTOS_2024'})

agrup_cand24.to_parquet('candidatos_2024.parquet', index=False)
print("-> candidatos_2024.parquet gerado com sucesso!")

# ==============================================================
# 3. PROCESSAR BASE DE 2026 (LEITURA EM BLOCOS / CHUNKS)
# ==============================================================
print("3/3 - Processando Base de 2026 (Arquivo grande lido em blocos)...")

arquivo_2026 = 'votacao_candidato_munzona_2026_SP.csv'
print(f"Lendo: {arquivo_2026}")

amostra = pd.read_csv(arquivo_2026, sep=';', encoding='latin1', nrows=2)
cols = amostra.columns.tolist()

c_uf = achar_coluna(cols, ['SG_UF', 'UF'])
c_mun_cod = achar_coluna(cols, ['CD_MUNICIPIO', 'CD_MUNIC'])
c_mun_nm = achar_coluna(cols, ['NM_MUNICIPIO', 'NM_MUNIC'])
c_cargo_cod = achar_coluna(cols, ['CD_CARGO'])
c_cargo_ds = achar_coluna(cols, ['DS_CARGO'])
c_cand_nm = achar_coluna(cols, ['NM_CANDIDATO', 'NM_CAND'])
c_urna_nm = achar_coluna(cols, ['NM_URNA_CANDIDATO', 'NM_URNA'])
c_partido = achar_coluna(cols, ['SG_PARTIDO', 'SG_PARTID'])
c_sit = achar_coluna(cols, ['DS_SIT_TOT_TURNO', 'DS_SIT_TO'])
c_votos = achar_coluna(cols, ['QT_VOTOS_NOMINAIS', 'QT_VOTOS'])

chunks_filtrados = []
chunk_size = 150000

for chunk in pd.read_csv(arquivo_2026, sep=';', encoding='latin1', chunksize=chunk_size, low_memory=False):
    filtro = (chunk[c_uf] == 'SP') & (chunk[c_cargo_cod].astype(str).isin(['6', '7']))
    pedaco = chunk[filtro]
    
    if not pedaco.empty:
        resumo_chunk = pedaco.groupby(
            [c_mun_cod, c_mun_nm, c_cargo_cod, c_cargo_ds, c_cand_nm, c_urna_nm, c_partido, c_sit],
            as_index=False
        )[c_votos].sum()
        chunks_filtrados.append(resumo_chunk)

print("Consolidando dados de 2026...")
df_2026_total = pd.concat(chunks_filtrados, ignore_index=True)

df_2026_final = df_2026_total.groupby(
    [c_mun_cod, c_mun_nm, c_cargo_cod, c_cargo_ds, c_cand_nm, c_urna_nm, c_partido, c_sit],
    as_index=False
)[c_votos].sum()

df_2026_final.columns = [
    'CD_MUNICIPIO', 'NM_MUNICIPIO', 'CD_CARGO', 'DS_CARGO',
    'NM_CANDIDATO', 'NM_URNA_CANDIDATO', 'SG_PARTIDO', 'DS_SIT_TOT_TURNO', 'VOTOS_2026'
]

def classificar_ideologia(sg):
    sg = str(sg).upper().strip()
    if sg in ['PL', 'REPUBLICANOS', 'NOVO', 'PRTB', 'MISSAO', 'MISSÃO']:
        return 'Direita Conservadora'
    elif sg in ['PP', 'UNIÃO', 'UNIAO', 'PSD', 'PODEMOS', 'PRD', 'AVANTE']:
        return 'Centro-Direita'
    elif sg in ['MDB', 'PSDB', 'CIDADANIA', 'SOLIDARIEDADE', 'AGIR']:
        return 'Centro'
    elif sg in ['PDT', 'PSB']:
        return 'Centro-Esquerda'
    elif sg in ['PT', 'PCDOB', 'PC DO B', 'PV', 'PSOL', 'REDE', 'UP', 'PCB', 'PCO']:
        return 'Esquerda'
    return 'Outros'

df_2026_final['ESPECTRO_IDEOLOGICO'] = df_2026_final['SG_PARTIDO'].apply(classificar_ideologia)
df_2026_final.to_parquet('candidatos_2026.parquet', index=False)
print("-> candidatos_2026.parquet gerado com sucesso!")
print("\nTODOS OS DADOS FORAM PROCESSADOS COM SUCESSO!")