import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Configuração da página Streamlit com visual premium
st.set_page_config(
    page_title="Gestão de Ocorrências - Estudo do Meio",
    page_icon="🎓",
    layout="wide"
)

# Estilização CSS premium (fontes modernas, cores harmoniosas e cantos arredondados)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    div[data-testid="stAppViewContainer"] {
        background-color: #f8fafc !important;
    }
    
    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1200px !important;
        margin: 0 auto !important;
    }
    
    h1 {
        color: #1e293b;
        font-weight: 700;
        margin-bottom: 1.5rem;
        font-size: 2.25rem !important;
        letter-spacing: -0.02em;
    }
    
    h2, h3, h4 {
        color: #4f46e5;
        font-weight: 600;
        letter-spacing: -0.01em;
    }
    
    /* Containers brancos premium */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02) !important;
        border: 1px solid #f1f5f9 !important;
        border-radius: 16px !important;
        padding: 24px !important;
        margin-bottom: 20px !important;
    }
    
    /* Formulários */
    div[data-testid="stForm"] {
        background-color: #ffffff !important;
        border: 1px solid #f1f5f9 !important;
        border-radius: 16px !important;
        padding: 28px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02) !important;
        margin-bottom: 20px !important;
    }
    
    /* Botão Primário */
    button[kind="primary"] {
        background: linear-gradient(135deg, #4f46e5 0%, #3730a3 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.55rem 1.2rem !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 4px 10px rgba(79, 70, 229, 0.18) !important;
    }
    button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.28) !important;
        background: linear-gradient(135deg, #5a52ff 0%, #4338ca 100%) !important;
    }
    
    /* Cartão Customizado */
    .custom-card {
        background-color: #ffffff;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
        border: 1px solid #f1f5f9;
        border-left: 5px solid #6366f1;
        margin-bottom: 12px;
    }
    </style>
""", unsafe_allow_html=True)


def inicializar_conexao():
    """Configura a conexão com o Google Sheets usando st-gsheets-connection."""
    try:
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        st.error(f"Erro ao configurar conexão com o Google Sheets: {e}")
        return None


def ler_tabela(conn, nome_aba):
    """Lê os dados de uma aba específica da planilha (ttl=0 para evitar cache)."""
    try:
        df = conn.read(worksheet=nome_aba, ttl=0)
        # Limpa linhas e colunas vazias
        df = df.dropna(how="all").reset_index(drop=True)
        # Padroniza nomes das colunas em minúsculas para evitar problemas de case-sensitivity
        df.columns = [str(col).strip().lower() for col in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao ler a aba '{nome_aba}' do Google Sheets: {e}")
        return pd.DataFrame()


def obter_rubrica_por_ano(df_criterios, ano_aluno):
    """
    Busca os critérios de avaliação (AA e CS) correspondentes ao ano/série do aluno.
    Se não encontrar uma rubrica específica, cai na rubrica 'Geral' (fallback).
    """
    if df_criterios.empty:
        return pd.DataFrame()
        
    ano_clean = str(ano_aluno).strip().lower()
    
    # 1. Tenta mapear o ano do aluno para o nome da rubrica
    # Ex: aluno é da "3ª série" -> tenta achar rubrica = "3ª série"
    df_filtrado = df_criterios[df_criterios["rubrica"].str.strip().str.lower() == ano_clean]
    
    # 2. Caso não ache nada, faz o fallback para "Geral"
    if df_filtrado.empty:
        df_filtrado = df_criterios[df_criterios["rubrica"].str.strip().str.lower() == "geral"]
        
    return df_filtrado


def main():
    st.markdown("<h1 style='text-align: center;'>🎓 Estudo do Meio</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b; font-size: 1.05rem; margin-bottom: 25px;'>Registro de ocorrências (AA e CS) integrado com o Google Sheets</p>", unsafe_allow_html=True)
    
    conn = inicializar_conexao()
    if not conn:
        return
        
    # Carrega tabelas de parâmetros
    df_professores = ler_tabela(conn, "Professores")
    df_alunos = ler_tabela(conn, "Alunos")
    df_criterios = ler_tabela(conn, "Criterios")
    df_ocorrencias = ler_tabela(conn, "Ocorrencias")
    
    if df_professores.empty or df_alunos.empty or df_criterios.empty:
        st.warning("⚠️ Planilha de parâmetros incompleta. Verifique se as abas 'Professores', 'Alunos' e 'Criterios' contêm dados cadastrados.")
        return

    # Controle de sessão/login do Professor
    if "prof_logado" not in st.session_state:
        st.session_state.prof_logado = None
        
    if st.session_state.prof_logado is None:
        st.markdown("### 🔑 Acesso do Professor")
        st.info("Para registrar ocorrências, faça login com o seu e-mail cadastrado na planilha.")
        
        with st.form("form_login"):
            email_digitado = st.text_input("E-mail Institucional:", placeholder="Ex: professor@escola.com").strip().lower()
            entrar = st.form_submit_button("Entrar", use_container_width=True)
            
            if entrar:
                if not email_digitado:
                    st.error("Por favor, digite seu e-mail.")
                else:
                    # Valida e-mail contra a aba Professores
                    prof_info = df_professores[df_professores["email"].str.strip().str.lower() == email_digitado]
                    if not prof_info.empty:
                        st.session_state.prof_logado = prof_info.iloc[0].to_dict()
                        st.success(f"Bem-vindo(a), {st.session_state.prof_logado['nome']}!")
                        import time
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("E-mail não cadastrado na aba 'Professores' da planilha.")
        return
        
    # Se logado, renderiza a interface principal
    prof = st.session_state.prof_logado
    
    # Header do Professor logado
    col_header1, col_header2 = st.columns([4, 1])
    with col_header1:
        st.markdown(f"### 👤 Professor: {prof['nome']}")
        st.caption(f"**Destino:** {prof.get('viagem', 'Todos')} | **Ônibus:** {prof.get('onibus', 'Todos')}")
    with col_header2:
        if st.button("Sair", use_container_width=True):
            st.session_state.prof_logado = None
            st.rerun()
            
    st.divider()
    
    # 1. Filtros e seleção de aluno
    st.markdown("### 🔍 1. Buscar Aluno")
    col_filt1, col_filt2 = st.columns(2)
    with col_filt1:
        filtrar_destino = st.checkbox("Somente alunos do meu destino", value=True)
    with col_filt2:
        filtrar_onibus = st.checkbox("Somente alunos do meu ônibus", value=False)
        
    # Filtragem dos alunos com base nos parâmetros do professor
    df_alunos_filtrados = df_alunos.copy()
    
    if filtrar_destino and pd.notna(prof.get('viagem')) and str(prof.get('viagem')).strip():
        destino_prof = str(prof['viagem']).strip().lower()
        df_alunos_filtrados = df_alunos_filtrados[df_alunos_filtrados['viagem_destino'].str.strip().str.lower() == destino_prof]
        
    if filtrar_onibus and pd.notna(prof.get('onibus')) and str(prof.get('onibus')).strip():
        onibus_prof = str(prof['onibus']).strip().lower()
        df_alunos_filtrados = df_alunos_filtrados[df_alunos_filtrados['onibus'].str.strip().str.lower() == onibus_prof]
        
    if df_alunos_filtrados.empty:
        st.info("ℹ️ Nenhum aluno atende aos filtros de destino/ônibus do professor.")
        return
        
    # Cria selectbox de busca do aluno
    aluno_opcoes = {}
    for _, al in df_alunos_filtrados.iterrows():
        label = f"{al['nome']} (RA: {al['ra']} | Série: {al['ano']} | Destino: {al['viagem_destino']})"
        aluno_opcoes[label] = al.to_dict()
        
    aluno_selecionado_label = st.selectbox(
        "Selecione o Aluno:",
        options=["-- Selecione --"] + list(aluno_opcoes.keys()),
        index=0,
        placeholder="Digite o nome ou RA para buscar..."
    )
    
    if aluno_selecionado_label == "-- Selecione --":
        st.info("👆 Selecione um aluno acima para prosseguir.")
        return
        
    aluno = aluno_opcoes[aluno_selecionado_label]
    
    # Card com info do aluno
    st.markdown(f"""
        <div class="custom-card">
            <h4 style="margin: 0; color: #4f46e5; font-size: 1.1rem;">🎓 {aluno['nome']}</h4>
            <p style="margin: 5px 0 0 0; color: #64748b; font-size: 0.9rem;">
                <b>RA:</b> {aluno['ra']} &nbsp;|&nbsp; <b>Turma/Série:</b> {aluno['ano']} &nbsp;|&nbsp; <b>Destino:</b> {aluno['viagem_destino']} &nbsp;|&nbsp; <b>Ônibus:</b> {aluno.get('onibus', 'N/A')}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # 2. Detalhes da ocorrência baseados nos Critérios da Planilha
    st.markdown("### 📝 2. Detalhes da Ocorrência")
    
    # Filtra os critérios correspondentes ao ano/série do aluno
    df_criterios_aluno = obter_rubrica_por_ano(df_criterios, aluno['ano'])
    
    if df_criterios_aluno.empty:
        st.warning("⚠️ Nenhum critério de avaliação configurado para o ano deste aluno na aba 'Criterios'.")
        return
        
    df_aa = df_criterios_aluno[df_criterios_aluno["tipo"].str.strip().str.upper() == "AA"]
    df_cs = df_criterios_aluno[df_criterios_aluno["tipo"].str.strip().str.upper() == "CS"]
    
    with st.form("form_registro_ocorrencia", clear_on_submit=True):
        st.markdown("<p style='color:#dc2626; font-weight:bold;'>⚠️ Assinale as infrações cometidas. Os pontos serão subtraídos da nota do aluno.</p>", unsafe_allow_html=True)
        
        tab_aa, tab_cs = st.tabs(["Atitude (AA)", "Comportamento Social (CS)"])
        
        # Estrutura para salvar o estado das seleções
        selecoes_aa = []
        descontos_aa = 0.0
        
        selecoes_cs = []
        descontos_cs = 0.0
        
        with tab_aa:
            st.caption("Critérios de Atitude Frente à Aprendizagem (AA):")
            for idx, r in df_aa.iterrows():
                cb_key = f"cb_aa_{idx}"
                col_txt, col_grav = st.columns([3, 2])
                with col_txt:
                    marcado = st.checkbox(r['descricao'], key=cb_key)
                if marcado:
                    with col_grav:
                        # Extrai os pesos/descontos da planilha
                        leve = float(r.get('desconto_leve', 0.1))
                        mod = float(r.get('desconto_moderado', 0.3))
                        grav = float(r.get('desconto_grave', 0.5))
                        
                        opcoes = [f"Leve (-{leve} pts)", f"Moderado (-{mod} pts)", f"Grave (-{grav} pts)"]
                        gravidade = st.radio("Gravidade", options=opcoes, key=f"rad_aa_{idx}", horizontal=True, label_visibility="collapsed")
                        
                        if "Leve" in gravidade:
                            descontos_aa += leve
                            selecoes_aa.append(f"{r['descricao']} (Leve)")
                        elif "Moderado" in gravidade:
                            descontos_aa += mod
                            selecoes_aa.append(f"{r['descricao']} (Moderado)")
                        else:
                            descontos_aa += grav
                            selecoes_aa.append(f"{r['descricao']} (Grave)")
                            
        with tab_cs:
            st.caption("Critérios de Comportamento Social (CS):")
            for idx, r in df_cs.iterrows():
                cb_key = f"cb_cs_{idx}"
                col_txt, col_grav = st.columns([3, 2])
                with col_txt:
                    marcado = st.checkbox(r['descricao'], key=cb_key)
                if marcado:
                    with col_grav:
                        # Extrai os pesos/descontos da planilha
                        leve = float(r.get('desconto_leve', 0.1))
                        mod = float(r.get('desconto_moderado', 0.3))
                        grav = float(r.get('desconto_grave', 0.5))
                        
                        opcoes = [f"Leve (-{leve} pts)", f"Moderado (-{mod} pts)", f"Grave (-{grav} pts)"]
                        gravidade = st.radio("Gravidade", options=opcoes, key=f"rad_cs_{idx}", horizontal=True, label_visibility="collapsed")
                        
                        if "Leve" in gravidade:
                            descontos_cs += leve
                            selecoes_cs.append(f"{r['descricao']} (Leve)")
                        elif "Moderado" in gravidade:
                            descontos_cs += mod
                            selecoes_cs.append(f"{r['descricao']} (Moderado)")
                        else:
                            descontos_cs += grav
                            selecoes_cs.append(f"{r['descricao']} (Grave)")
                            
        st.markdown("<br>", unsafe_allow_html=True)
        observacoes = st.text_area("📝 Detalhamento e Contextualização do Ocorrido (Obrigatório):", placeholder="Descreva os fatos em texto livre...")
        
        # Mostra resumo do desconto antes de enviar
        if descontos_aa > 0 or descontos_cs > 0:
            st.warning(f"⚠️ **Resumo da Dedução:** Serão deduzidos **-{descontos_aa:.1f} pontos** em AA e **-{descontos_cs:.1f} pontos** em CS.")
            
        salvar = st.form_submit_button("💾 Salvar Registro na Planilha", use_container_width=True)
        
        if salvar:
            if not selecoes_aa and not selecoes_cs:
                st.error("❌ Erro: Selecione pelo menos uma infração/critério de AA ou CS.")
            elif not observacoes.strip():
                st.error("❌ Erro: Descreva e contextualize o ocorrido no campo de observações.")
            else:
                # 3. Processa e grava os dados na aba Ocorrencias
                novo_id = int(df_ocorrencias["id"].max() + 1) if not df_ocorrencias.empty and "id" in df_ocorrencias.columns else 1
                
                novo_registro = {
                    "id": novo_id,
                    "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "professor_email": prof["email"].strip(),
                    "professor_nome": prof["nome"].strip(),
                    "aluno_ra": str(aluno["ra"]).strip(),
                    "aluno_nome": aluno["nome"].strip(),
                    "aluno_turma": aluno["ano"].strip(),
                    "destino": aluno["viagem_destino"].strip(),
                    "onibus": aluno.get("onibus", "Sem ônibus") if pd.notna(aluno.get("onibus")) else "Sem ônibus",
                    "criterios_aa": "; ".join(selecoes_aa) if selecoes_aa else "Nenhum",
                    "desconto_aa": float(descontos_aa),
                    "criterios_cs": "; ".join(selecoes_cs) if selecoes_cs else "Nenhum",
                    "desconto_cs": float(descontos_cs),
                    "observacoes": observacoes.strip()
                }
                
                # Cria DataFrame
                df_novo = pd.DataFrame([novo_registro])
                
                # Assegura a integridade das colunas
                for col in df_ocorrencias.columns:
                    if col not in df_novo.columns:
                        df_novo[col] = None
                for col in df_novo.columns:
                    if col not in df_ocorrencias.columns:
                        df_ocorrencias[col] = None
                
                df_novo = df_novo[df_ocorrencias.columns]
                
                # Concatena os DataFrames
                df_consolidado = pd.concat([df_ocorrencias, df_novo], ignore_index=True)
                
                # Grava no Google Sheets
                try:
                    conn.update(worksheet="Ocorrencias", data=df_consolidado)
                    st.success(f"✅ Ocorrência registrada com sucesso para o aluno {aluno['nome']}!")
                    import time
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar no Google Sheets: {e}")


if __name__ == "__main__":
    main()
