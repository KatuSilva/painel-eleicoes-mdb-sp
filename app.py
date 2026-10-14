import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Raio-X Eleitoral SP | MDB", layout="wide")

# ==============================================================
# FUNÇÕES DE CARREGAMENTO E CLASSIFICAÇÃO
# ==============================================================
@st.cache_data
def carregar_dados():
    det = pd.read_parquet('detalhe_2024.parquet')
    c24 = pd.read_parquet('candidatos_2024.parquet')
    c26 = pd.read_parquet('candidatos_2026.parquet')
    status_reeleicao = pd.read_parquet('status_prefeitos_2028.parquet')
    return det, c24, c26, status_reeleicao

def classificar_ideologia(sg):
    sg = str(sg).upper().strip()
    if sg in ['PL', 'REPUBLICANOS', 'NOVO', 'PRTB', 'DC', 'MISSAO', 'MISSÃO', 'PSC', 'PTB']:
        return 'Direita Conservadora'
    elif sg in ['PP', 'UNIÃO', 'UNIAO', 'PSD', 'PODE', 'PODEMOS', 'PRD', 'AVANTE', 'PATRIOTA']:
        return 'Centro-Direita'
    elif sg in ['MDB', 'PSDB', 'CIDADANIA', 'SOLIDARIEDADE', 'AGIR', 'MOBILIZA', 'PMB', 'PROS']:
        return 'Centro'
    elif sg in ['PDT', 'PSB']:
        return 'Centro-Esquerda'
    else: # Qualquer outro partido (PT, PSOL, REDE, UP, PCB, PCO, PSTU, PCdoB, PV, etc) vai para Esquerda
        return 'Esquerda'

# Ordem fixa para os gráficos
ordem_espectro = ['Esquerda', 'Centro-Esquerda', 'Centro', 'Centro-Direita', 'Direita Conservadora']

cores_ideologia = {
    'Esquerda': '#d62728',             # Vermelho
    'Centro-Esquerda': '#ffbb78',      # Laranja claro
    'Centro': '#2ca02c',               # Verde
    'Centro-Direita': '#aec7e8',       # Azul claro
    'Direita Conservadora': '#1f77b4'  # Azul escuro
}

# --- PROTEÇÃO POR SENHA ---
def verificar_senha():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if not st.session_state["autenticado"]:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🔒 Acesso Restrito | MDB SP")
            senha_digitada = st.text_input("Digite a senha de acesso:", type="password")
            if st.button("Entrar no Painel", use_container_width=True):
                if senha_digitada == "MDB2028SP":
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Senha incorreta.")
        st.stop()

verificar_senha()

# Carregamento
df_det, df_c24, df_c26, df_status = carregar_dados()

df_c24['ESPECTRO_IDEOLOGICO'] = df_c24['SG_PARTIDO'].apply(classificar_ideologia)
df_c26['ESPECTRO_IDEOLOGICO'] = df_c26['SG_PARTIDO'].apply(classificar_ideologia)

# ==============================================================
# CABEÇALHO E FILTRO
# ==============================================================
col_logo, col_titulo = st.columns([1, 9])
with col_logo:
    if os.path.exists("logo_mdb.png"):
        st.image("logo_mdb.png", width=80)
with col_titulo:
    st.title("🎯 Raio-X Municipal SP: Inteligência Eleitoral 2024-2028")

municipios = sorted(df_det['NM_MUNICIPIO'].dropna().unique())
col_filtro, _ = st.columns([3, 7])
with col_filtro:
    cidade_selecionada = st.selectbox("Selecione o Município:", municipios)

det_cid = df_det[df_det['NM_MUNICIPIO'] == cidade_selecionada]
c24_cid = df_c24[df_c24['NM_MUNICIPIO'] == cidade_selecionada]
c26_cid = df_c26[df_c26['NM_MUNICIPIO'] == cidade_selecionada]

cod_mun = int(det_cid['CD_MUNICIPIO'].iloc[0]) if not det_cid.empty else None
det_pref = det_cid[det_cid['CD_CARGO'] == 11]

st.markdown("---")

# ==============================================================
# BLOCO A: RETRATO POLÍTICO DE 2024
# ==============================================================
st.subheader("🏛️ Bloco A: Retrato Político de 2024")

if not det_pref.empty:
    aptos = int(det_pref['TOTAL_APTOS'].sum())
    comp = int(det_pref['TOTAL_COMPARECIMENTO'].sum())
    abst = int(det_pref['TOTAL_ABSTENCOES'].sum())
    validos = int(det_pref['TOTAL_VALIDOS'].sum())

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Eleitorado Total", f"{aptos:,}".replace(",", "."))
    k2.metric("Comparecimento", f"{(comp/aptos)*100:.1f}%")
    k3.metric("Abstenção", f"{(abst/aptos)*100:.1f}%")
    k4.metric("Votos Válidos (Prefeito)", f"{validos:,}".replace(",", "."))

col_pref, col_vice = st.columns(2)

with col_pref:
    st.markdown("**Disputa para Prefeito**")
    prefeitos = c24_cid[c24_cid['CD_CARGO'] == 11].sort_values(by='VOTOS_2024', ascending=False).copy()
    if not prefeitos.empty:
        total_votos_pref = prefeitos['VOTOS_2024'].sum()
        prefeitos['% Válidos'] = (prefeitos['VOTOS_2024'] / total_votos_pref) * 100
        st.dataframe(
            prefeitos[['NM_URNA_CANDIDATO', 'SG_PARTIDO', 'DS_SIT_TOT_TURNO', 'VOTOS_2024', '% Válidos']]
            .rename(columns={'NM_URNA_CANDIDATO': 'Candidato', 'SG_PARTIDO': 'Partido', 'DS_SIT_TOT_TURNO': 'Resultado', 'VOTOS_2024': 'Votos'})
            .style.format({'% Válidos': '{:.2f}%', 'Votos': '{:,.0f}'}),
            hide_index=True, use_container_width=True
        )

with col_vice:
    st.markdown("**Informações do Chefe do Executivo Eleito**")
    status_cid = df_status[df_status['CD_MUNICIPIO'] == cod_mun]
    
    if not status_cid.empty:
        pref_nome = status_cid.iloc[0]['PREFEITO_ELEITO']
        st.info(f"**Prefeito Eleito:** {pref_nome}")
        apto_texto = status_cid.iloc[0]['APTO_REELEICAO_2028']
        if 'SIM' in apto_texto:
            st.success(f"🗳️ **Apto à reeleição em 2028:** {apto_texto}")
        else:
            st.warning(f"🚫 **Apto à reeleição em 2028:** {apto_texto}")
            
        vice_nome = status_cid.iloc[0]['VICE_ELEITO']
        is_mdb = status_cid.iloc[0]['VICE_E_MDB']
        if is_mdb == 'SIM':
            st.success(f"✅ O Vice-Prefeito eleito é do MDB: **{vice_nome}**")
        else:
            st.error(f"❌ O Vice não é do MDB (Eleito: {vice_nome})")
    else:
        st.warning("⚠️ Dados consolidados não encontrados.")

st.markdown("---")

# ==============================================================
# BLOCO B: O MDB E A CÂMARA MUNICIPAL
# ==============================================================
st.subheader("🟢 Bloco B: O MDB e a Câmara Municipal")

col_camara_graf, col_camara_partidos, col_camara_lista = st.columns([1.2, 1.2, 1.5])

todos_vereadores = c24_cid[c24_cid['CD_CARGO'] == 13].copy()
eleitos_ver = todos_vereadores[todos_vereadores['DS_SIT_TOT_TURNO'].astype(str).str.contains('ELEITO')].copy()

with col_camara_graf:
    st.markdown("**Câmara por Perfil Ideológico**")
    if not eleitos_ver.empty:
        agrup_ideologia = eleitos_ver.groupby('ESPECTRO_IDEOLOGICO').size().reset_index(name='Cadeiras')
        fig_camara = px.pie(
            agrup_ideologia, names='ESPECTRO_IDEOLOGICO', values='Cadeiras', 
            color='ESPECTRO_IDEOLOGICO', color_discrete_map=cores_ideologia, hole=0.4,
            category_orders={'ESPECTRO_IDEOLOGICO': ordem_espectro}
        )
        fig_camara.update_layout(margin=dict(t=10, b=0, l=0, r=0), height=320, legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5))
        st.plotly_chart(fig_camara, use_container_width=True)

with col_camara_partidos:
    st.markdown("**Eleitos por Partido**")
    if not eleitos_ver.empty:
        agrup_partido = eleitos_ver.groupby(['SG_PARTIDO', 'ESPECTRO_IDEOLOGICO']).size().reset_index(name='Cadeiras')
        agrup_partido = agrup_partido.sort_values(by='Cadeiras', ascending=True)
        fig_barras = px.bar(
            agrup_partido, x='Cadeiras', y='SG_PARTIDO', orientation='h',
            color='ESPECTRO_IDEOLOGICO', color_discrete_map=cores_ideologia, text='Cadeiras'
        )
        fig_barras.update_layout(margin=dict(t=10, b=0, l=0, r=0), height=320, xaxis_title="", yaxis_title="", showlegend=False, xaxis=dict(showticklabels=False, showgrid=False, zeroline=False))
        fig_barras.update_traces(textposition='outside', cliponaxis=False)
        st.plotly_chart(fig_barras, use_container_width=True)

with col_camara_lista:
    st.markdown("**Desempenho Geral (Todos os Vereadores)**")
    if not todos_vereadores.empty:
        votos_totais_ver = todos_vereadores['VOTOS_2024'].sum()
        todos_vereadores['%'] = (todos_vereadores['VOTOS_2024'] / votos_totais_ver) * 100
        todos_vereadores = todos_vereadores.sort_values(by='VOTOS_2024', ascending=False)
        st.dataframe(
            todos_vereadores[['NM_URNA_CANDIDATO', 'SG_PARTIDO', 'DS_SIT_TOT_TURNO', 'VOTOS_2024', '%']]
            .rename(columns={'NM_URNA_CANDIDATO': 'Nome Urna', 'SG_PARTIDO': 'Partido', 'DS_SIT_TOT_TURNO': 'Situação', 'VOTOS_2024': 'Votos'})
            .style.format({'%': '{:.2f}%', 'Votos': '{:,.0f}'}),
            hide_index=True, use_container_width=True, height=320
        )

st.markdown("<br>", unsafe_allow_html=True)
col_mdb_24, col_mdb_26 = st.columns(2)

with col_mdb_24:
    st.markdown("**Desempenho MDB em 2024 (Vereadores)**")
    mdb_2024 = todos_vereadores[todos_vereadores['SG_PARTIDO'] == 'MDB'].copy()
    if mdb_2024.empty:
        st.warning("O MDB não lançou candidatos a vereador nesta cidade.")
    else:
        votos_totais_mdb = mdb_2024['VOTOS_2024'].sum()
        perc_mdb = (votos_totais_mdb / votos_totais_ver) * 100 if votos_totais_ver > 0 else 0
        st.success(f"**Total de Votos Nominais do MDB (Vereador):** {votos_totais_mdb:,} ({perc_mdb:.2f}% da cidade)")
        st.dataframe(
            mdb_2024[['NM_URNA_CANDIDATO', 'DS_SIT_TOT_TURNO', 'VOTOS_2024', '%']]
            .rename(columns={'NM_URNA_CANDIDATO': 'Nome Urna', 'DS_SIT_TOT_TURNO': 'Situação', 'VOTOS_2024': 'Votos'})
            .sort_values(by='Votos', ascending=False).style.format({'%': '{:.2f}%', 'Votos': '{:,.0f}'}),
            hide_index=True, use_container_width=True
        )

with col_mdb_26:
    st.markdown("**Deputados do MDB Votados em 2026 na Cidade**")
    mdb_2026 = c26_cid[c26_cid['SG_PARTIDO'] == 'MDB'].copy()
    if mdb_2026.empty:
        st.info("Nenhum voto registrado para o MDB em 2026 nesta cidade.")
    else:
        votos_totais_cidade_2026 = c26_cid['VOTOS_2026'].sum()
        votos_totais_mdb_2026 = mdb_2026['VOTOS_2026'].sum()
        perc_mdb_2026 = (votos_totais_mdb_2026 / votos_totais_cidade_2026) * 100 if votos_totais_cidade_2026 > 0 else 0
        st.success(f"**Total de Votos Nominais do MDB (Deputados):** {votos_totais_mdb_2026:,} ({perc_mdb_2026:.2f}% da cidade)")
        mdb_2026['%'] = (mdb_2026['VOTOS_2026'] / votos_totais_cidade_2026) * 100
        st.dataframe(
            mdb_2026[['DS_CARGO', 'NM_URNA_CANDIDATO', 'DS_SIT_TOT_TURNO', 'VOTOS_2026', '%']]
            .rename(columns={'DS_CARGO': 'Cargo', 'NM_URNA_CANDIDATO': 'Nome Urna', 'DS_SIT_TOT_TURNO': 'Resultado Geral', 'VOTOS_2026': 'Votos na Cidade'})
            .sort_values(by='Votos na Cidade', ascending=False).style.format({'%': '{:.2f}%', 'Votos na Cidade': '{:,.0f}'}),
            hide_index=True, use_container_width=True
        )

st.markdown("---")

# ==============================================================
# BLOCO C: O VOTO IDEOLÓGICO EM 2026
# ==============================================================
st.subheader("⚖️ Bloco C: O Voto Ideológico em 2026 (Deputado Federal)")
federais_2026 = c26_cid[c26_cid['CD_CARGO'].astype(str) == '6']

if not federais_2026.empty:
    votos_totais_federais = federais_2026['VOTOS_2026'].sum()
    ideologia_df = federais_2026.groupby('ESPECTRO_IDEOLOGICO', as_index=False)['VOTOS_2026'].sum()
    ideologia_df['Perc'] = (ideologia_df['VOTOS_2026'] / votos_totais_federais) * 100
    ideologia_df['Texto_Barra'] = ideologia_df.apply(lambda row: f"{row['VOTOS_2026']:,}<br>({row['Perc']:.1f}%)".replace(',', '.'), axis=1)

    fig_ideologia = px.bar(
        ideologia_df, x='ESPECTRO_IDEOLOGICO', y='VOTOS_2026',
        color='ESPECTRO_IDEOLOGICO', color_discrete_map=cores_ideologia,
        text='Texto_Barra', labels={'ESPECTRO_IDEOLOGICO': 'Espectro', 'VOTOS_2026': 'Votos Nominais'},
        category_orders={'ESPECTRO_IDEOLOGICO': ordem_espectro} # Força a ordem da Esquerda para a Direita
    )
    fig_ideologia.update_layout(showlegend=False, height=350, margin=dict(t=20, b=20, l=10, r=10))
    st.plotly_chart(fig_ideologia, use_container_width=True)

st.markdown("---")

# ==============================================================
# BLOCO D: RADAR DE CAPTAÇÃO 2028
# ==============================================================
st.subheader("🎯 Bloco D: Radar de Captação (Até 5º Suplente para Convidar)")
st.caption("Suplentes (1º ao 5º) de outras legendas. O selo ⭐ aponta quem disputou eleição em 2026.")

suplentes_2024 = todos_vereadores[
    (todos_vereadores['DS_SIT_TOT_TURNO'] == 'SUPLENTE') & 
    (todos_vereadores['SG_PARTIDO'] != 'MDB')
].copy()

if not suplentes_2024.empty:
    suplentes_2024['RANK_PARTIDO'] = suplentes_2024.groupby('SG_PARTIDO')['VOTOS_2024'].rank(ascending=False, method='first')
    radar_df = suplentes_2024[suplentes_2024['RANK_PARTIDO'] <= 5].copy()
    candidatos_2026_nomes = set(df_c26['NM_CANDIDATO'].dropna().str.upper().unique())
    radar_df['Disputou em 2026?'] = radar_df['NM_CANDIDATO'].str.upper().apply(
        lambda x: "⭐ Sim (Candidato 2026)" if x in candidatos_2026_nomes else "Não"
    )
    st.dataframe(
        radar_df[['NM_URNA_CANDIDATO', 'SG_PARTIDO', 'VOTOS_2024', 'RANK_PARTIDO', 'Disputou em 2026?']]
        .rename(columns={'NM_URNA_CANDIDATO': 'Nome de Urna', 'SG_PARTIDO': 'Partido em 2024', 'VOTOS_2024': 'Votos 2024', 'RANK_PARTIDO': 'Posição'})
        .sort_values(by='Votos 2024', ascending=False).style.format({'Posição': '{:.0f}º Suplente'}),
        hide_index=True, use_container_width=True
    )
else:
    st.write("Nenhum suplente mapeado para os critérios selecionados nesta cidade.")

st.markdown("---")

# ==============================================================
# BLOCO E: OS DONOS DA CIDADE (TOP 10 DEPUTADOS)
# ==============================================================
st.subheader("👑 Bloco E: Os 'Donos' da Cidade (Top 10 Deputados 2026)")
col_fed, col_est = st.columns(2)

with col_fed:
    st.markdown("**Top 10 Deputados Federais**")
    top_fed = c26_cid[c26_cid['CD_CARGO'].astype(str) == '6'].sort_values(by='VOTOS_2026', ascending=False).head(10)
    if not top_fed.empty:
        st.dataframe(
            top_fed[['NM_URNA_CANDIDATO', 'SG_PARTIDO', 'DS_SIT_TOT_TURNO', 'VOTOS_2026']]
            .rename(columns={'NM_URNA_CANDIDATO': 'Deputado Federal', 'SG_PARTIDO': 'Partido', 'DS_SIT_TOT_TURNO': 'Situação', 'VOTOS_2026': 'Votos na Cidade'})
            .style.format({'Votos na Cidade': '{:,.0f}'}),
            hide_index=True, use_container_width=True
        )

with col_est:
    st.markdown("**Top 10 Deputados Estaduais**")
    top_est = c26_cid[c26_cid['CD_CARGO'].astype(str) == '7'].sort_values(by='VOTOS_2026', ascending=False).head(10)
    if not top_est.empty:
        st.dataframe(
            top_est[['NM_URNA_CANDIDATO', 'SG_PARTIDO', 'DS_SIT_TOT_TURNO', 'VOTOS_2026']]
            .rename(columns={'NM_URNA_CANDIDATO': 'Deputado Estadual', 'SG_PARTIDO': 'Partido', 'DS_SIT_TOT_TURNO': 'Situação', 'VOTOS_2026': 'Votos na Cidade'})
            .style.format({'Votos na Cidade': '{:,.0f}'}),
            hide_index=True, use_container_width=True
        )