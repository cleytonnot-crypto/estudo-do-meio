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
        height: auto !important;
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
        # Padroniza nomes das colunas em minúsculas
        df.columns = [str(col).strip().lower() for col in df.columns]
        return df
    except Exception as e:
        # Se a aba estiver vazia ou não existir, cria estrutura básica vazia
        colunas_padrao = {
            "Professores": ["nome", "email", "viagem", "onibus"],
            "Alunos": ["ra", "nome", "ano", "viagem_destino", "onibus"],
            "Criterios": ["rubrica", "tipo", "descricao", "desconto_leve", "desconto_moderado", "desconto_grave"],
            "Ocorrencias": ["id", "data_hora", "professor_email", "professor_nome", "aluno_ra", "aluno_nome", "aluno_turma", "destino", "onibus", "criterios_aa", "desconto_aa", "criterios_cs", "desconto_cs", "observacoes"]
        }
        return pd.DataFrame(columns=colunas_padrao.get(nome_aba, []))


def obter_rubrica_por_ano(df_criterios, ano_aluno):
    """Mapeia os critérios para o ano/série correspondente ou cai em Geral."""
    if df_criterios.empty:
        return pd.DataFrame()
    ano_clean = str(ano_aluno).strip().lower()
    df_filtrado = df_criterios[df_criterios["rubrica"].str.strip().str.lower() == ano_clean]
    if df_filtrado.empty:
        df_filtrado = df_criterios[df_criterios["rubrica"].str.strip().str.lower() == "geral"]
    return df_filtrado


def main():
    st.markdown("<h2 style='text-align: center; color: #1e293b; margin-bottom: 5px;'>Estudo do Meio</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b; font-size: 1.05rem; margin-bottom: 25px;'>Painel completo conectado ao Google Sheets</p>", unsafe_allow_html=True)
    
    conn = inicializar_conexao()
    if not conn:
        return
        
    # Carrega dados
    df_professores = ler_tabela(conn, "Professores")
    df_alunos = ler_tabela(conn, "Alunos")
    df_criterios = ler_tabela(conn, "Criterios")
    df_ocorrencias = ler_tabela(conn, "Ocorrencias")
    
    # ----------------- NAVEGAÇÃO PRINCIPAL -----------------
    if 'selection' not in st.session_state:
        st.session_state.selection = '📝 Registrar Ocorrência'
        
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        if st.button("📝 Registrar Ocorrência", use_container_width=True, type="primary" if st.session_state.selection == '📝 Registrar Ocorrência' else "secondary"):
            st.session_state.selection = '📝 Registrar Ocorrência'
            st.rerun()
    with col_m2:
        if st.button("📊 Análise de Ocorrências", use_container_width=True, type="primary" if st.session_state.selection == '📊 Análise de Ocorrências' else "secondary"):
            st.session_state.selection = '📊 Análise de Ocorrências'
            st.rerun()
    with col_m3:
        if st.button("⚙️ Administração", use_container_width=True, type="primary" if st.session_state.selection == '⚙️ Administração' else "secondary"):
            st.session_state.selection = '⚙️ Administração'
            st.rerun()
            
    selection = st.session_state.selection
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ==================== ABA 1: REGISTRAR OCORRÊNCIA ====================
    if selection == '📝 Registrar Ocorrência':
        st.markdown("<h1>📝 Registrar Ocorrência</h1>", unsafe_allow_html=True)
        
        # Controle de Login do Professor
        if "prof_logado" not in st.session_state:
            st.session_state.prof_logado = None
            
        if st.session_state.prof_logado is None:
            st.info("Para registrar ocorrências, faça login com o seu e-mail cadastrado.")
            with st.form("form_login"):
                email_digitado = st.text_input("E-mail Institucional:", placeholder="Ex: professor@escola.com").strip().lower()
                entrar = st.form_submit_button("Entrar", use_container_width=True)
                if entrar:
                    if not email_digitado:
                        st.error("Por favor, digite seu e-mail.")
                    elif df_professores.empty:
                        st.error("A lista de professores está vazia. Vá em 'Administração' para cadastrar o primeiro professor.")
                    else:
                        prof_info = df_professores[df_professores["email"].str.strip().str.lower() == email_digitado]
                        if not prof_info.empty:
                            st.session_state.prof_logado = prof_info.iloc[0].to_dict()
                            st.success(f"Bem-vindo(a), {st.session_state.prof_logado['nome']}!")
                            import time
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("E-mail não cadastrado na aba 'Professores'.")
            return
            
        prof = st.session_state.prof_logado
        
        # Cabeçalho de Professor
        col_h1, col_h2 = st.columns([4, 1])
        with col_h1:
            st.markdown(f"### 👤 Professor: {prof['nome']}")
            st.caption(f"**Destino:** {prof.get('viagem', 'Todos')} | **Ônibus:** {prof.get('onibus', 'Todos')}")
        with col_h2:
            if st.button("Sair", use_container_width=True):
                st.session_state.prof_logado = None
                st.rerun()
                
        st.divider()
        
        if df_alunos.empty:
            st.warning("⚠️ Nenhum aluno cadastrado. Vá em 'Administração' para cadastrar alunos.")
            return
        if df_criterios.empty:
            st.warning("⚠️ Nenhum critério de avaliação cadastrado. Vá em 'Administração' para cadastrar critérios.")
            return
            
        # Filtros de Aluno
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtrar_destino = st.checkbox("Somente alunos do meu destino", value=True)
        with col_f2:
            filtrar_onibus = st.checkbox("Somente alunos do meu ônibus", value=False)
            
        df_alunos_filtrados = df_alunos.copy()
        if filtrar_destino and pd.notna(prof.get('viagem')) and str(prof.get('viagem')).strip():
            df_alunos_filtrados = df_alunos_filtrados[df_alunos_filtrados['viagem_destino'].str.strip().str.lower() == str(prof['viagem']).strip().lower()]
        if filtrar_onibus and pd.notna(prof.get('onibus')) and str(prof.get('onibus')).strip():
            df_alunos_filtrados = df_alunos_filtrados[df_alunos_filtrados['onibus'].str.strip().str.lower() == str(prof['onibus']).strip().lower()]
            
        if df_alunos_filtrados.empty:
            st.info("ℹ️ Nenhum aluno atende aos filtros de destino/ônibus.")
            return
            
        aluno_opcoes = {}
        for _, al in df_alunos_filtrados.iterrows():
            label = f"{al['nome']} (RA: {al['ra']} | Série: {al['ano']} | Destino: {al['viagem_destino']})"
            aluno_opcoes[label] = al.to_dict()
            
        aluno_sel_label = st.selectbox("Selecione o Aluno:", options=["-- Selecione --"] + list(aluno_opcoes.keys()))
        if aluno_sel_label == "-- Selecione --":
            return
            
        aluno = aluno_opcoes[aluno_sel_label]
        
        st.markdown(f"""
            <div class="custom-card">
                <h4 style="margin: 0; color: #4f46e5; font-size: 1.1rem;">🎓 {aluno['nome']}</h4>
                <p style="margin: 5px 0 0 0; color: #64748b; font-size: 0.9rem;">
                    <b>RA:</b> {aluno['ra']} &nbsp;|&nbsp; <b>Série:</b> {aluno['ano']} &nbsp;|&nbsp; <b>Destino:</b> {aluno['viagem_destino']} &nbsp;|&nbsp; <b>Ônibus:</b> {aluno.get('onibus', 'N/A')}
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Filtra os critérios
        df_criterios_aluno = obter_rubrica_por_ano(df_criterios, aluno['ano'])
        df_aa = df_criterios_aluno[df_criterios_aluno["tipo"].str.strip().str.upper() == "AA"]
        df_cs = df_criterios_aluno[df_criterios_aluno["tipo"].str.strip().str.upper() == "CS"]
        
        with st.form("form_reg_ocorrencia", clear_on_submit=True):
            tab_aa, tab_cs = st.tabs(["Atitude (AA)", "Comportamento Social (CS)"])
            
            selecoes_aa, descontos_aa = [], 0.0
            selecoes_cs, descontos_cs = [], 0.0
            
            with tab_aa:
                for idx, r in df_aa.iterrows():
                    col_txt, col_grav = st.columns([3, 2])
                    with col_txt:
                        marcado = st.checkbox(r['descricao'], key=f"cb_aa_{idx}")
                    if marcado:
                        with col_grav:
                            l, m, g = float(r.get('desconto_leve', 0.1)), float(r.get('desconto_moderado', 0.3)), float(r.get('desconto_grave', 0.5))
                            grav = st.radio("Gravidade", options=[f"Leve (-{l})", f"Moderado (-{m})", f"Grave (-{g})"], key=f"rad_aa_{idx}", horizontal=True, label_visibility="collapsed")
                            if "Leve" in grav:
                                descontos_aa += l; selecoes_aa.append(f"{r['descricao']} (Leve)")
                            elif "Moderado" in grav:
                                descontos_aa += m; selecoes_aa.append(f"{r['descricao']} (Moderado)")
                            else:
                                descontos_aa += g; selecoes_aa.append(f"{r['descricao']} (Grave)")
                                
            with tab_cs:
                for idx, r in df_cs.iterrows():
                    col_txt, col_grav = st.columns([3, 2])
                    with col_txt:
                        marcado = st.checkbox(r['descricao'], key=f"cb_cs_{idx}")
                    if marcado:
                        with col_grav:
                            l, m, g = float(r.get('desconto_leve', 0.1)), float(r.get('desconto_moderado', 0.3)), float(r.get('desconto_grave', 0.5))
                            grav = st.radio("Gravidade", options=[f"Leve (-{l})", f"Moderado (-{m})", f"Grave (-{g})"], key=f"rad_cs_{idx}", horizontal=True, label_visibility="collapsed")
                            if "Leve" in grav:
                                descontos_cs += l; selecoes_cs.append(f"{r['descricao']} (Leve)")
                            elif "Moderado" in grav:
                                descontos_cs += m; selecoes_cs.append(f"{r['descricao']} (Moderado)")
                            else:
                                descontos_cs += g; selecoes_cs.append(f"{r['descricao']} (Grave)")
                                
            observacoes = st.text_area("📝 Observações / Contextualização (Obrigatório):")
            
            if descontos_aa > 0 or descontos_cs > 0:
                st.warning(f"Deduções calculadas: -{descontos_aa:.1f} pts em AA e -{descontos_cs:.1f} pts em CS.")
                
            registrar = st.form_submit_button("💾 Salvar Registro na Planilha", use_container_width=True)
            
            if registrar:
                if not selecoes_aa and not selecoes_cs:
                    st.error("Selecione pelo menos um critério.")
                elif not observacoes.strip():
                    st.error("Descreva os detalhes da ocorrência.")
                else:
                    novo_id = int(df_ocorrencias["id"].max() + 1) if not df_ocorrencias.empty and "id" in df_ocorrencias.columns else 1
                    novo_reg = {
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
                    df_novo = pd.DataFrame([novo_reg])
                    for col in df_ocorrencias.columns:
                        if col not in df_novo.columns:
                            df_novo[col] = None
                    df_novo = df_novo[df_ocorrencias.columns]
                    df_consolidado = pd.concat([df_ocorrencias, df_novo], ignore_index=True)
                    
                    try:
                        conn.update(worksheet="Ocorrencias", data=df_consolidado)
                        st.success("✅ Ocorrência registrada no Google Sheets com sucesso!")
                        import time
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    # ==================== ABA 2: ANÁLISE DE OCORRÊNCIAS ====================
    elif selection == '📊 Análise de Ocorrências':
        st.markdown("<h1>📊 Análise de Ocorrências</h1>", unsafe_allow_html=True)
        if df_ocorrencias.empty:
            st.info("Nenhuma ocorrência registrada na planilha.")
        else:
            st.dataframe(df_ocorrencias, use_container_width=True)

    # ==================== ABA 3: ADMINISTRAÇÃO (CADASTROS) ====================
    elif selection == '⚙️ Administração':
        st.markdown("<h1>⚙️ Painel de Administração</h1>", unsafe_allow_html=True)
        st.write("Use esta aba para testar a gravação no Google Sheets preenchendo os parâmetros.")
        
        tab_cad_prof, tab_cad_aluno, tab_cad_crit = st.tabs(["Professores", "Alunos", "Critérios"])
        
        # 1. Cadastro de Professor
        with tab_cad_prof:
            st.subheader("Cadastrar Novo Professor")
            with st.form("form_cad_prof", clear_on_submit=True):
                p_nome = st.text_input("Nome completo:")
                p_email = st.text_input("E-mail institucional:")
                p_viagem = st.text_input("Destino da Viagem (Ex: MG):")
                p_onibus = st.text_input("Ônibus designado (Ex: Ônibus 1):")
                sub_p = st.form_submit_button("💾 Salvar Professor no Sheets")
                
                if sub_p:
                    if not p_nome.strip() or not p_email.strip():
                        st.error("Nome e E-mail são obrigatórios.")
                    else:
                        novo_p = {
                            "nome": p_nome.strip(),
                            "email": p_email.strip().lower(),
                            "viagem": p_viagem.strip().upper(),
                            "onibus": p_onibus.strip()
                        }
                        df_novo_p = pd.DataFrame([novo_p])
                        df_final_p = pd.concat([df_professores, df_novo_p], ignore_index=True)
                        try:
                            conn.update(worksheet="Professores", data=df_final_p)
                            st.success(f"✅ Professor {p_nome} gravado no Google Sheets!")
                            import time
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar: {e}")
                            
            st.write("---")
            st.write("### Professores Atuais na Planilha")
            st.dataframe(df_professores, use_container_width=True)

        # 2. Cadastro de Aluno
        with tab_cad_aluno:
            st.subheader("Cadastrar Novo Aluno")
            with st.form("form_cad_aluno", clear_on_submit=True):
                a_ra = st.text_input("RA do Aluno:")
                a_nome = st.text_input("Nome do Aluno:")
                a_ano = st.text_input("Ano/Turma (Ex: 9º Ano A):")
                a_viagem = st.text_input("Destino do Aluno (Ex: MG):")
                a_onibus = st.text_input("Ônibus do Aluno (Ex: Ônibus 1):")
                sub_a = st.form_submit_button("💾 Salvar Aluno no Sheets")
                
                if sub_a:
                    if not a_ra.strip() or not a_nome.strip():
                        st.error("RA e Nome são obrigatórios.")
                    else:
                        novo_a = {
                            "ra": a_ra.strip(),
                            "nome": a_nome.strip(),
                            "ano": a_ano.strip(),
                            "viagem_destino": a_viagem.strip().upper(),
                            "onibus": a_onibus.strip()
                        }
                        df_novo_a = pd.DataFrame([novo_a])
                        df_final_a = pd.concat([df_alunos, df_novo_a], ignore_index=True)
                        try:
                            conn.update(worksheet="Alunos", data=df_final_a)
                            st.success(f"✅ Aluno {a_nome} gravado no Google Sheets!")
                            import time
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar: {e}")
                            
            st.write("---")
            st.write("### Alunos Atuais na Planilha")
            st.dataframe(df_alunos, use_container_width=True)

        # 3. Cadastro de Critério
        with tab_cad_crit:
            st.subheader("Cadastrar Novo Critério")
            with st.form("form_cad_crit", clear_on_submit=True):
                c_rubrica = st.text_input("Rubrica (Ex: Geral, 2ª série, 3ª série):")
                c_tipo = st.selectbox("Tipo de Critério:", ["AA", "CS"])
                c_desc = st.text_area("Descrição da Ocorrência:")
                col_d1, col_d2, col_d3 = st.columns(3)
                with col_d1:
                    c_l = st.number_input("Dedução Leve:", min_value=0.0, max_value=5.0, value=0.1, step=0.1)
                with col_d2:
                    c_m = st.number_input("Dedução Moderada:", min_value=0.0, max_value=5.0, value=0.3, step=0.1)
                with col_d3:
                    c_g = st.number_input("Dedução Grave:", min_value=0.0, max_value=5.0, value=0.5, step=0.1)
                    
                sub_c = st.form_submit_button("💾 Salvar Critério no Sheets")
                
                if sub_c:
                    if not c_rubrica.strip() or not c_desc.strip():
                        st.error("Rubrica e Descrição são obrigatórias.")
                    else:
                        novo_c = {
                            "rubrica": c_rubrica.strip(),
                            "tipo": c_tipo,
                            "descricao": c_desc.strip(),
                            "desconto_leve": float(c_l),
                            "desconto_moderado": float(c_m),
                            "desconto_grave": float(c_g)
                        }
                        df_novo_c = pd.DataFrame([novo_c])
                        df_final_c = pd.concat([df_criterios, df_novo_c], ignore_index=True)
                        try:
                            conn.update(worksheet="Criterios", data=df_final_c)
                            st.success("✅ Critério gravado no Google Sheets!")
                            import time
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar: {e}")
                            
            st.write("---")
            st.write("### Critérios Atuais na Planilha")
            st.dataframe(df_criterios, use_container_width=True)


if __name__ == "__main__":
    main()
