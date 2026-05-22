import streamlit as st
import pandas as pd
import io
from datetime import datetime
from contextlib import contextmanager
from database import inicializar_banco, SessionLocal, Professor, Aluno, Avaliacao, Feedback
from sqlalchemy import func

def limpar_valor_excel(val):
    if pd.isna(val):
        return None
    val_str = str(val).strip()
    if val_str.endswith('.0'):
        part_before = val_str[:-2]
        if part_before.isdigit() or (part_before.startswith('-') and part_before[1:].isdigit()):
            return part_before
    return val_str

def limpar_email(val):
    if pd.isna(val):
        return None
    return str(val).strip().lower()

def limpar_nome(val):
    if pd.isna(val):
        return ""
    return str(val).strip()

def processar_excel_professores(df, db):
    expected = ['nome', 'email', 'viagem']
    if not all(col in df.columns for col in expected):
        raise ValueError(f"O arquivo deve conter as colunas: {expected}")
        
    count = 0
    duplicates_skipped = 0
    existing_emails = set(str(p[0]).strip().lower() for p in db.query(Professor.email).all() if p[0])
    
    for _, r in df.iterrows():
        if pd.isna(r['nome']) or pd.isna(r['email']):
            continue
        
        nome_val = limpar_nome(r['nome'])
        email_val = limpar_email(r['email'])
        
        if not nome_val or not email_val:
            continue
            
        if email_val not in existing_emails:
            on_val = limpar_valor_excel(r['onibus']) if 'onibus' in df.columns else None
            try:
                novo_prof = Professor(
                    nome=nome_val,
                    email=email_val,
                    viagem=limpar_valor_excel(r['viagem']),
                    onibus=on_val
                )
                db.add(novo_prof)
                db.commit()
                existing_emails.add(email_val)
                count += 1
            except Exception:
                db.rollback()
                duplicates_skipped += 1
        else:
            duplicates_skipped += 1
            
    return count, duplicates_skipped

def processar_excel_alunos(df, db):
    expected = ['nome', 'ra', 'email', 'ano', 'viagem_destino']
    if not all(col in df.columns for col in expected):
        raise ValueError(f"O arquivo deve conter as colunas: {expected}")
        
    count = 0
    duplicates_skipped = 0
    existing_ras = set(str(a[0]).strip().lower() for a in db.query(Aluno.ra).all() if a[0])
    existing_emails = set(str(a[0]).strip().lower() for a in db.query(Aluno.email).all() if a[0])
    
    for _, r in df.iterrows():
        if pd.isna(r['nome']) or pd.isna(r['ra']) or pd.isna(r['email']):
            continue
        
        nome_val = limpar_nome(r['nome'])
        ra_val = limpar_valor_excel(r['ra'])
        email_val = limpar_email(r['email'])
        
        if not nome_val or not ra_val or not email_val:
            continue
            
        if ra_val.lower() not in existing_ras and email_val not in existing_emails:
            on_val = limpar_valor_excel(r['onibus']) if 'onibus' in df.columns else None
            try:
                novo_aluno = Aluno(
                    nome=nome_val,
                    ra=ra_val,
                    email=email_val,
                    ano=limpar_valor_excel(r['ano']),
                    viagem_destino=limpar_valor_excel(r['viagem_destino']),
                    onibus=on_val
                )
                db.add(novo_aluno)
                db.commit()
                existing_ras.add(ra_val.lower())
                existing_emails.add(email_val)
                count += 1
            except Exception:
                db.rollback()
                duplicates_skipped += 1
        else:
            duplicates_skipped += 1
            
    return count, duplicates_skipped

# Inicializa o banco de dados
inicializar_banco()

# Configuração inicial da página
st.set_page_config(
    page_title="Avaliação de Estudo do Meio",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização Premium via CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1 {
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {
        color: #e2e8f0 !important;
    }
    
    [data-testid="stSidebar"] div[data-testid="stRadio"] label p {
        color: #cbd5e1 !important;
        font-size: 1.05rem !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] caption,
    [data-testid="stSidebar"] span {
        color: #94a3b8 !important;
    }
    

    h1 {
        color: #1e3a8a;
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        margin-bottom: 1.5rem;
    }
    
    h2, h3 {
        color: #2563eb;
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
    }
    
    .stAlert {
        border-radius: 12px;
    }
    
    .metric-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border-left: 5px solid #2563eb;
        border-top: 1px solid #f1f5f9;
        border-right: 1px solid #f1f5f9;
        border-bottom: 1px solid #f1f5f9;
        margin-bottom: 15px;
    }
    
    .metric-title {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .metric-value {
        font-size: 1.75rem;
        color: #0f172a;
        font-weight: 700;
        margin-top: 5px;
    }
    
    .floating-feedback-btn {
        position: fixed;
        bottom: 25px;
        right: 25px;
        width: 60px;
        height: 60px;
        background-color: #ef4444 !important;
        color: white !important;
        border-radius: 50%;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        z-index: 999999;
        display: flex;
        align-items: center;
        justify-content: center;
        text-decoration: none !important;
        font-size: 26px !important;
        transition: transform 0.2s, background-color 0.2s;
    }
    .floating-feedback-btn:hover {
        transform: scale(1.1);
        background-color: #dc2626 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Renderiza o botão flutuante de feedback
st.markdown(
    '<a href="?feedback=abrir" target="_self" class="floating-feedback-btn" title="Reportar Erro ou Sugestão">💬</a>',
    unsafe_allow_html=True
)

# Lógica para abrir o formulário de feedback/sugestão
if st.query_params.get("feedback") == "abrir":
    if hasattr(st, "dialog"):
        @st.dialog("💬 Reportar Erro ou Sugestão")
        def feedback_dialog():
            st.write("Ajude-nos a melhorar o sistema! Descreva o erro ou a sugestão abaixo.")
            tipo = st.selectbox("Tipo de Reporte:", ["Erro / Bug", "Sugestão", "Dúvida", "Outro"])
            secao = st.selectbox("Seção Relacionada:", ["Geral", "Registrar Ocorrência", "Dashboard da Coordenação", "Administração"])
            nome = st.text_input("Seu Nome (Opcional):", placeholder="Anônimo")
            descricao = st.text_area("Descrição Detalhada:", placeholder="Escreva aqui...")
            
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("Enviar Reporte", type="primary", key="btn_send_fb"):
                    if not descricao.strip():
                        st.error("Por favor, descreva o erro ou sugestão.")
                    else:
                        with get_db() as db:
                            novo_fb = Feedback(
                                nome=nome.strip() if nome.strip() else None,
                                tipo=tipo,
                                secao=secao,
                                descricao=descricao.strip()
                            )
                            db.add(novo_fb)
                            db.commit()
                        st.success("Obrigado! Seu feedback foi enviado com sucesso.")
                        st.query_params.clear()
                        st.rerun()
            with col_d2:
                if st.button("Cancelar", key="btn_cancel_fb"):
                    st.query_params.clear()
                    st.rerun()
        feedback_dialog()
    else:
        # Fallback caso não possua st.dialog
        st.info("💬 **Formulário de Feedback / Sugestão**")
        with st.form("form_feedback_fallback"):
            st.write("Ajude-nos a melhorar o sistema! Descreva o erro ou a sugestão abaixo.")
            tipo = st.selectbox("Tipo de Reporte:", ["Erro / Bug", "Sugestão", "Dúvida", "Outro"])
            secao = st.selectbox("Seção Relacionada:", ["Geral", "Registrar Ocorrência", "Dashboard da Coordenação", "Administração"])
            nome = st.text_input("Seu Nome (Opcional):", placeholder="Anônimo")
            descricao = st.text_area("Descrição Detalhada:", placeholder="Escreva aqui...")
            
            col_fb1, col_fb2 = st.columns(2)
            with col_fb1:
                sub_fb = st.form_submit_button("Enviar Reporte")
            with col_fb2:
                canc_fb = st.form_submit_button("Cancelar / Fechar")
                
            if sub_fb:
                if not descricao.strip():
                    st.error("Por favor, descreva o erro ou sugestão.")
                else:
                    with get_db() as db:
                        novo_fb = Feedback(
                            nome=nome.strip() if nome.strip() else None,
                            tipo=tipo,
                            secao=secao,
                            descricao=descricao.strip()
                        )
                        db.add(novo_fb)
                        db.commit()
                    st.success("Obrigado! Seu feedback foi enviado com sucesso.")
                    st.query_params.clear()
                    st.rerun()
            if canc_fb:
                st.query_params.clear()
                st.rerun()

# Critérios Oficiais de Avaliação
CRITERIOS_AA = [
    "Atenção às explicações dos monitores, guias, palestrantes e professores.",
    "Anotações sempre que possível.",
    "Registros fotográficos.",
    "Participação ativa com perguntas e considerações sobre os temas ao longo da viagem.",
    "Demonstração de interesse e curiosidade pelos espaços visitados e temas discutidos."
]

CRITERIOS_CS = [
    "Respeito aos motoristas, guias, monitores, palestrantes, professores, 'corujas' e demais trabalhadores e colegas.",
    "Ônibus: limpeza; manter-se sentado; uso do cinto de segurança; música apenas no fone de ouvido.",
    "Horários e atrasos: café da manhã, almoço, intervalos, recolhimento ao quarto à noite.",
    "Uso adequado de todas as dependências dos hotéis e demais espaços visitados.",
    "Uso adequado do celular.",
    "Respeito aos combinados gerais ao longo da viagem."
]

# Helper context manager para sessões do SQLAlchemy
@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper para carregar dados consolidados para a Coordenação
def carregar_dados_coordenacao():
    with get_db() as db:
        avaliacoes = db.query(Avaliacao).all()
        dados = []
        for a in avaliacoes:
            dados.append({
                "ID": a.id,
                "Aluno": a.aluno.nome if a.aluno else "N/A",
                "RA": a.aluno.ra if a.aluno else "N/A",
                "Ano/Turma": a.aluno.ano if a.aluno else "N/A",
                "Destino": a.aluno.viagem_destino if a.aluno else "N/A",
                "Ônibus": a.aluno.onibus if a.aluno else "Sem Ônibus",
                "Atitudes (AA)": a.atitude_aa or "",
                "Comportamento (CS)": a.comportamento_cs or "",
                "Observações / Detalhamento": a.observacoes or "",
                "Registrado por": a.professor.nome if a.professor else "N/A",
                "Data/Hora": a.data_hora.strftime("%d/%m/%Y %H:%M:%S") if a.data_hora else "N/A",
                "data_hora_raw": a.data_hora
            })
        return pd.DataFrame(dados)

# Helper para gerar templates Excel
def criar_template_excel(colunas):
    output = io.BytesIO()
    df = pd.DataFrame(columns=colunas)
    # Adiciona uma linha de exemplo fictícia
    if 'ra' in colunas:
        df.loc[0] = ['Ana Silva', '10203040', 'ana.silva@escola.com.br', '9º Ano A', 'MG', 'Ônibus 1']
    else:
        df.loc[0] = ['Professor Marcos', 'marcos@escola.com.br', 'MG', 'Ônibus 1']
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# Navegação Lateral
st.sidebar.title("📌 Menu Principal")
menu_options = ['📝 Registrar Ocorrência', '📊 Dashboard da Coordenação', '⚙️ Administração']
selection = st.sidebar.radio("Navegue pelas seções:", menu_options)

# Lógica de exibição baseada na seleção
if selection == '📝 Registrar Ocorrência':
    st.title("📝 Registro de Ocorrência (AA & CS)")
    st.write("Módulo para professores e monitores registrarem ocorrências de Atitude Frente à Aprendizagem (AA) e Comportamento Social (CS) por veículo de viagem.")
    
    # Busca professores
    with get_db() as db:
        professores = db.query(Professor).all()
        alunos = db.query(Aluno).all()
        
    if not professores:
        st.warning("⚠️ Nenhum professor cadastrado no sistema. Acesse a seção 'Administração' para cadastrar professores.")
    elif not alunos:
        st.warning("⚠️ Nenhum aluno cadastrado no sistema. Acesse a seção 'Administração' para importar ou cadastrar alunos.")
    else:
        # Perfil do Professor Avaliador
        prof_dict = {f"{p.nome} (Destino: {p.viagem or 'Qualquer'} | {p.onibus or 'Sem Ônibus'})": p.id for p in professores}
        prof_selecionado = st.selectbox("👤 Selecione quem está registrando a ocorrência:", list(prof_dict.keys()))
        professor_id = prof_dict[prof_selecionado]
        
        # Recupera informações do professor para filtros inteligentes
        with get_db() as db:
            prof_obj = db.query(Professor).filter(Professor.id == professor_id).first()
            prof_viagem = prof_obj.viagem
            prof_onibus = prof_obj.onibus
            
        st.markdown("---")
        
        # Filtros para busca de aluno
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtrar_mesmo_destino = st.checkbox("Filtrar alunos do mesmo destino do professor", value=True)
        with col_f2:
            onibus_existentes = list(set([a.onibus for a in alunos if a.onibus]))
            onibus_filtro = st.selectbox("Filtrar lista de alunos por Ônibus:", ["Todos"] + onibus_existentes)
            
        # Aplica os filtros na listagem de alunos
        alunos_filtrados = alunos
        if filtrar_mesmo_destino and prof_viagem:
            alunos_filtrados = [a for a in alunos_filtrados if a.viagem_destino == prof_viagem]
        if onibus_filtro != "Todos":
            alunos_filtrados = [a for a in alunos_filtrados if a.onibus == onibus_filtro]
            
        if not alunos_filtrados:
            st.info("ℹ️ Nenhum aluno atende aos filtros de destino e ônibus selecionados.")
        else:
            # Seleção do aluno
            aluno_dict = {f"{a.nome} (RA: {a.ra} | Destino: {a.viagem_destino} | {a.onibus or 'Sem Ônibus'})": a.id for a in alunos_filtrados}
            aluno_selecionado = st.selectbox("🎓 Selecione o Aluno:", list(aluno_dict.keys()))
            aluno_id = aluno_dict[aluno_selecionado]
            
            with get_db() as db:
                aluno_obj = db.query(Aluno).filter(Aluno.id == aluno_id).first()
                
            # Card de detalhes do aluno
            st.markdown(f"""
            <div style="background-color: #eff6ff; padding: 15px; border-radius: 10px; border-left: 5px solid #2563eb; margin-bottom: 20px;">
                <h4 style="margin: 0; color: #1e3a8a; font-size: 1.1rem;">🎓 {aluno_obj.nome}</h4>
                <p style="margin: 5px 0 0 0; color: #4b5563; font-size: 0.9rem;">
                    <b>RA:</b> {aluno_obj.ra} | <b>Ano/Turma:</b> {aluno_obj.ano} | <b>Destino de Viagem:</b> {aluno_obj.viagem_destino} | <b>Veículo/Ônibus:</b> {aluno_obj.onibus or 'Não informado'}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Formulário de Ocorrência
            st.subheader("📋 Detalhes da Ocorrência")
            st.write("Assinale abaixo quais os critérios do regulamento motivaram este registro:")
            
            tab_aa, tab_cs = st.tabs(["Atitude Frente à Aprendizagem (AA)", "Comportamento Social (CS)"])
            
            with tab_aa:
                st.write("**Selecione as ocorrências de Atitude Frente à Aprendizagem (AA):**")
                aa_selecionados = []
                for crit in CRITERIOS_AA:
                    if st.checkbox(crit, key=f"aa_{crit}"):
                        aa_selecionados.append(crit)
                        
            with tab_cs:
                st.write("**Selecione as ocorrências de Comportamento Social (CS):**")
                cs_selecionados = []
                for crit in CRITERIOS_CS:
                    if st.checkbox(crit, key=f"cs_{crit}"):
                        cs_selecionados.append(crit)
                        
            observacoes = st.text_area(
                "📝 Detalhamento e Contextualização do Ocorrido (Obrigatório):", 
                placeholder="Descreva o que aconteceu em detalhes (ações, horários, atitudes, etc.) para justificar os critérios assinalados acima."
            )
            
            if st.button("💾 Registrar Ocorrência", type="primary"):
                if not aa_selecionados and not cs_selecionados:
                    st.error("❌ Erro: Selecione ao menos um critério de AA ou CS para registrar a ocorrência.")
                elif not observacoes.strip():
                    st.error("❌ Erro: O detalhamento/descrição da ocorrência é obrigatório.")
                else:
                    with get_db() as db:
                        try:
                            nova_oco = Avaliacao(
                                professor_id=professor_id,
                                aluno_id=aluno_id,
                                atitude_aa="; ".join(aa_selecionados) if aa_selecionados else None,
                                comportamento_cs="; ".join(cs_selecionados) if cs_selecionados else None,
                                observacoes=observacoes.strip()
                            )
                            db.add(nova_oco)
                            db.commit()
                            st.success(f"✅ Sucesso! Ocorrência registrada para o aluno **{aluno_obj.nome}**.")
                            st.rerun()
                        except Exception as e:
                            db.rollback()
                            st.error(f"❌ Erro ao salvar ocorrência: {e}")
            
            # Histórico individual do Aluno
            with get_db() as db:
                historico = db.query(Avaliacao).filter(Avaliacao.aluno_id == aluno_id).order_by(Avaliacao.data_hora.desc()).all()
                
                if historico:
                    st.markdown("---")
                    st.subheader(f"📜 Histórico de Ocorrências Gravadas - {aluno_obj.nome}")
                    for h in historico:
                        data_str = h.data_hora.strftime("%d/%m/%Y %H:%M")
                        prof_nome = h.professor.nome if h.professor else "N/A"
                        st.markdown(f"""
                        <div style="background-color: #fafafa; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; margin-bottom: 12px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.85rem;">
                                <span style="font-weight: 600; color: #334155;">👤 Registrador: {prof_nome}</span>
                                <span style="color: #64748b;">📅 {data_str}</span>
                            </div>
                            {f'<p style="margin: 2px 0; color: #1e3a8a; font-size: 0.9rem;"><b>AA:</b> {h.atitude_aa}</p>' if h.atitude_aa else ''}
                            {f'<p style="margin: 2px 0; color: #b45309; font-size: 0.9rem;"><b>CS:</b> {h.comportamento_cs}</p>' if h.comportamento_cs else ''}
                            <p style="margin: 8px 0 0 0; font-size: 0.95rem; color: #0f172a; border-top: 1px dashed #e2e8f0; padding-top: 8px;">
                                <i>"{h.observacoes}"</i>
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

elif selection == '📊 Dashboard da Coordenação':
    st.title("📊 Dashboard de Monitoramento Pedagógico")
    st.write("Visão consolidada das ocorrências registradas para coordenação, acompanhamento em tempo real e exportação de relatórios.")
    
    # Carrega métricas gerais
    with get_db() as db:
        total_alunos = db.query(Aluno).count()
        total_profs = db.query(Professor).count()
        total_ocorrencias = db.query(Avaliacao).count()
        # Quantidade de alunos com pelo menos 1 ocorrência
        alunos_com_ocorrencia = db.query(Avaliacao.aluno_id).distinct().count()
        
    perc_alunos = (alunos_com_ocorrencia / total_alunos * 100) if total_alunos > 0 else 0.0
    
    # KPIs com Cards Estilizados
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Total Alunos</div><div class="metric-value">{total_alunos}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card" style="border-left-color: #10b981;"><div class="metric-title">Total Professores</div><div class="metric-value">{total_profs}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card" style="border-left-color: #f59e0b;"><div class="metric-title">Total Ocorrências</div><div class="metric-value">{total_ocorrencias}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card" style="border-left-color: #ec4899;"><div class="metric-title">Alunos Avaliados (%)</div><div class="metric-value">{perc_alunos:.1f}%</div></div>', unsafe_allow_html=True)
        
    df_oco = carregar_dados_coordenacao()
    
    if df_oco.empty:
        st.info("ℹ️ Nenhuma ocorrência registrada no banco de dados até o momento.")
    else:
        st.markdown("---")
        
        # Gráficos em Colunas
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("🚌 Ocorrências por Veículo (Ônibus)")
            df_onibus = df_oco["Ônibus"].value_counts().reset_index()
            df_onibus.columns = ["Ônibus", "Registros"]
            st.bar_chart(df_onibus.set_index("Ônibus"), color="#3b82f6")
            
        with col_g2:
            st.subheader("📍 Ocorrências por Destino")
            df_destino = df_oco["Destino"].value_counts().reset_index()
            df_destino.columns = ["Destino", "Registros"]
            st.bar_chart(df_destino.set_index("Destino"), color="#10b981")
            
        st.markdown("---")
        
        # Ranking de Ocorrências (Mais frequentes de AA e CS)
        all_aa = []
        all_cs = []
        for _, row in df_oco.iterrows():
            if row["Atitudes (AA)"]:
                all_aa.extend([x.strip() for x in row["Atitudes (AA)"].split(";") if x.strip()])
            if row["Comportamento (CS)"]:
                all_cs.extend([x.strip() for x in row["Comportamento (CS)"].split(";") if x.strip()])
                
        st.subheader("📊 Frequência por Critério de Regulamento")
        col_r1, col_r2 = st.columns(2)
        
        with col_r1:
            st.markdown("**🚨 Atitude Frente à Aprendizagem (AA)**")
            if all_aa:
                df_aa_counts = pd.Series(all_aa).value_counts().reset_index()
                df_aa_counts.columns = ["Critério", "Frequência"]
                st.dataframe(df_aa_counts, use_container_width=True, hide_index=True)
            else:
                st.caption("Nenhum critério AA registrado ainda.")
                
        with col_r2:
            st.markdown("**🚨 Comportamento Social (CS)**")
            if all_cs:
                df_cs_counts = pd.Series(all_cs).value_counts().reset_index()
                df_cs_counts.columns = ["Critério", "Frequência"]
                st.dataframe(df_cs_counts, use_container_width=True, hide_index=True)
            else:
                st.caption("Nenhum critério CS registrado ainda.")
                
        st.markdown("---")
        
        st.subheader("🏆 Ranking de Alunos com Mais Ocorrências Registradas")
        if not df_oco.empty:
            df_ranking = df_oco.groupby(["Aluno", "RA", "Ônibus", "Destino"]).size().reset_index(name="Total Ocorrências")
            df_ranking = df_ranking.sort_values(by="Total Ocorrências", ascending=False).reset_index(drop=True)
            df_ranking.index = df_ranking.index + 1  # 1-indexed
            df_ranking = df_ranking.reset_index().rename(columns={"index": "Posição"})
            st.dataframe(df_ranking, use_container_width=True, hide_index=True)
        else:
            st.caption("Nenhum registro no ranking.")
            
        st.markdown("---")
        
        # Filtros Avançados & Histórico
        st.subheader("🔍 Histórico e Filtros do Relatório")
        
        col_filtro_onibus, col_filtro_destino, col_filtro_prof, col_filtro_ano = st.columns(4)
        with col_filtro_onibus:
            lista_onibus = ["Todos"] + sorted(list(df_oco["Ônibus"].unique()))
            f_onibus = st.selectbox("Filtro por Ônibus:", lista_onibus)
        with col_filtro_destino:
            lista_destinos = ["Todos"] + sorted(list(df_oco["Destino"].unique()))
            f_destino = st.selectbox("Filtro por Destino:", lista_destinos)
        with col_filtro_prof:
            lista_profs = ["Todos"] + sorted(list(df_oco["Registrado por"].unique()))
            f_prof = st.selectbox("Filtro por Professor:", lista_profs)
        with col_filtro_ano:
            lista_anos = ["Todos"] + sorted(list(df_oco["Ano/Turma"].unique()))
            f_ano = st.selectbox("Filtro por Ano/Turma:", lista_anos)
            
        col_cat, col_datas, col_ordem = st.columns(3)
        with col_cat:
            f_categoria = st.selectbox("Filtrar por Categoria:", ["Todas", "Apenas Atitude (AA)", "Apenas Comportamento (CS)"])
        with col_datas:
            # Pega as datas mínima e máxima reais para definir o range
            min_dt = df_oco["data_hora_raw"].min().date()
            max_dt = df_oco["data_hora_raw"].max().date()
            
            datas_sel = st.date_input(
                "Filtro por Período / Data:",
                value=(min_dt, max_dt),
                min_value=min_dt - pd.Timedelta(days=30),
                max_value=max_dt + pd.Timedelta(days=30)
            )
        with col_ordem:
            f_ordem = st.selectbox(
                "Ordenar resultados por:",
                [
                    "Mais Recentes Primeiro",
                    "Mais Antigos Primeiro",
                    "Aluno (A-Z)",
                    "Professor (A-Z)"
                ]
            )
            
        col_criterios, col_busca_ra = st.columns([2, 1])
        with col_criterios:
            criterios_selecionados = st.multiselect(
                "Filtro por Critério do Regulamento (AA / CS):",
                options=CRITERIOS_AA + CRITERIOS_CS,
                placeholder="Selecione um ou mais critérios..."
            )
        with col_busca_ra:
            busca = st.text_input("🔍 Buscar por Nome do Aluno ou RA:")
        
        # Aplica filtros dinamicamente
        df_filtrado = df_oco.copy()
        if f_onibus != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Ônibus"] == f_onibus]
        if f_destino != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Destino"] == f_destino]
        if f_prof != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Registrado por"] == f_prof]
        if f_ano != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Ano/Turma"] == f_ano]
        if f_categoria == "Apenas Atitude (AA)":
            df_filtrado = df_filtrado[df_filtrado["Atitudes (AA)"].str.strip() != ""]
        elif f_categoria == "Apenas Comportamento (CS)":
            df_filtrado = df_filtrado[df_filtrado["Comportamento (CS)"].str.strip() != ""]
            
        # Filtragem por período/data
        if isinstance(datas_sel, (tuple, list)) and len(datas_sel) == 2:
            data_inicio, data_fim = datas_sel
            df_filtrado = df_filtrado[
                (df_filtrado["data_hora_raw"].dt.date >= data_inicio) &
                (df_filtrado["data_hora_raw"].dt.date <= data_fim)
            ]
        elif not isinstance(datas_sel, (tuple, list)):
            df_filtrado = df_filtrado[df_filtrado["data_hora_raw"].dt.date == datas_sel]
            
        # Filtragem por critérios específicos
        if criterios_selecionados:
            mask = df_filtrado.apply(
                lambda r: any(
                    crit in r["Atitudes (AA)"] or crit in r["Comportamento (CS)"]
                    for crit in criterios_selecionados
                ),
                axis=1
            )
            df_filtrado = df_filtrado[mask]
            
        if busca.strip():
            df_filtrado = df_filtrado[
                df_filtrado["Aluno"].str.contains(busca, case=False, na=False) |
                df_filtrado["RA"].str.contains(busca, case=False, na=False)
            ]
            
        # Aplica ordenação
        if f_ordem == "Mais Recentes Primeiro":
            df_filtrado = df_filtrado.sort_values(by="data_hora_raw", ascending=False)
        elif f_ordem == "Mais Antigos Primeiro":
            df_filtrado = df_filtrado.sort_values(by="data_hora_raw", ascending=True)
        elif f_ordem == "Aluno (A-Z)":
            df_filtrado = df_filtrado.sort_values(by="Aluno", ascending=True)
        elif f_ordem == "Professor (A-Z)":
            df_filtrado = df_filtrado.sort_values(by="Registrado por", ascending=True)
            
        st.markdown(f"**Registros encontrados:** {len(df_filtrado)}")
        
        # Remove coluna auxiliar de data raw antes de exibir
        df_exibicao = df_filtrado.drop(columns=["data_hora_raw"]) if "data_hora_raw" in df_filtrado.columns else df_filtrado
        st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
        
        # Exportação para Excel (sem coluna auxiliar)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_exibicao.to_excel(writer, index=False, sheet_name="Ocorrências_Estudo_Meio")
        excel_data = buffer.getvalue()
        
        st.download_button(
            label="📥 Baixar Histórico Filtrado em Excel (.xlsx)",
            data=excel_data,
            file_name=f"relatorio_ocorrencias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

elif selection == '⚙️ Administração':
    st.title("⚙️ Painel de Administração")
    st.write("Gerencie os cadastros do sistema de forma unitária ou em lote (via arquivo do Excel).")
    
    admin_tab1, admin_tab2, admin_tab3, admin_tab4, admin_tab5 = st.tabs([
        "📋 Registros Atuais", 
        "➕ Cadastro Manual", 
        "📤 Importação em Lote (.xlsx)", 
        "💬 Feedbacks e Sugestões",
        "🚨 Limpeza de Dados"
    ])
    
    with admin_tab1:
        st.subheader("Visualizar Cadastros do Sistema")
        
        with get_db() as db:
            profs_cadastrados = db.query(Professor).all()
            alunos_cadastrados = db.query(Aluno).all()
            
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.markdown(f"#### 👨‍🏫 Professores ({len(profs_cadastrados)})")
            if profs_cadastrados:
                df_profs = pd.DataFrame([{
                    "ID": p.id,
                    "Nome": p.nome,
                    "E-mail": p.email,
                    "Destino": p.viagem,
                    "Ônibus": p.onibus
                } for p in profs_cadastrados])
                st.dataframe(df_profs, use_container_width=True, hide_index=True)
            else:
                st.caption("Nenhum professor cadastrado.")
                
        with col_v2:
            st.markdown(f"#### 🎓 Alunos ({len(alunos_cadastrados)})")
            if alunos_cadastrados:
                df_alunos = pd.DataFrame([{
                    "ID": a.id,
                    "Nome": a.nome,
                    "RA": a.ra,
                    "E-mail": a.email,
                    "Ano/Turma": a.ano,
                    "Destino": a.viagem_destino,
                    "Ônibus": a.onibus
                } for a in alunos_cadastrados])
                st.dataframe(df_alunos, use_container_width=True, hide_index=True)
            else:
                st.caption("Nenhum aluno cadastrado.")
                
    with admin_tab2:
        st.subheader("Cadastro Manual de Usuários")
        col_man1, col_man2 = st.columns(2)
        
        with col_man1:
            st.markdown("#### ➕ Adicionar Professor")
            with st.form("form_prof", clear_on_submit=True):
                p_nome = st.text_input("Nome do Professor/Monitor:")
                p_email = st.text_input("E-mail:")
                p_viagem = st.text_input("Destino da Viagem (Ex: MG, RJ, BSB):")
                p_onibus = st.text_input("Ônibus/Veículo (Ex: Ônibus 1, Ônibus 2):")
                
                btn_p = st.form_submit_button("Cadastrar Professor")
                if btn_p:
                    if not p_nome.strip() or not p_email.strip():
                        st.error("Nome e E-mail são campos obrigatórios.")
                    else:
                        with get_db() as db:
                            try:
                                # Verifica duplicado de forma case-insensitive e com strip
                                p_email_clean = p_email.strip().lower()
                                duplicate = db.query(Professor).filter(
                                    func.lower(Professor.email) == p_email_clean
                                ).first()
                                if duplicate:
                                    st.error("Professor com este e-mail já está cadastrado.")
                                else:
                                    novo_p = Professor(
                                        nome=p_nome.strip(),
                                        email=p_email_clean,
                                        viagem=p_viagem.strip() if p_viagem.strip() else None,
                                        onibus=p_onibus.strip() if p_onibus.strip() else None
                                    )
                                    db.add(novo_p)
                                    db.commit()
                                    st.success(f"Professor '{p_nome}' adicionado com sucesso!")
                                    st.rerun()
                            except Exception as e:
                                db.rollback()
                                st.error(f"Erro ao salvar: {e}")
                                
        with col_man2:
            st.markdown("#### ➕ Adicionar Aluno")
            with st.form("form_aluno", clear_on_submit=True):
                a_nome = st.text_input("Nome do Aluno:")
                a_ra = st.text_input("RA:")
                a_email = st.text_input("E-mail:")
                a_ano = st.text_input("Ano/Turma (Ex: 9º Ano A):")
                a_viagem = st.text_input("Destino da Viagem (Ex: MG, RJ, BSB):")
                a_onibus = st.text_input("Ônibus/Veículo (Ex: Ônibus 1, Ônibus 2):")
                
                btn_a = st.form_submit_button("Cadastrar Aluno")
                if btn_a:
                    if not a_nome.strip() or not a_ra.strip() or not a_email.strip():
                        st.error("Nome, RA e E-mail são obrigatórios.")
                    else:
                        with get_db() as db:
                            try:
                                # Verifica duplicado de forma case-insensitive e com strip
                                a_ra_clean = a_ra.strip()
                                a_email_clean = a_email.strip().lower()
                                duplicate = db.query(Aluno).filter(
                                    (func.lower(Aluno.ra) == a_ra_clean.lower()) | 
                                    (func.lower(Aluno.email) == a_email_clean)
                                ).first()
                                if duplicate:
                                    st.error("Aluno com este RA ou e-mail já está cadastrado.")
                                else:
                                    novo_a = Aluno(
                                        nome=a_nome.strip(),
                                        ra=a_ra_clean,
                                        email=a_email_clean,
                                        ano=a_ano.strip() if a_ano.strip() else None,
                                        viagem_destino=a_viagem.strip() if a_viagem.strip() else None,
                                        onibus=a_onibus.strip() if a_onibus.strip() else None
                                    )
                                    db.add(novo_a)
                                    db.commit()
                                    st.success(f"Aluno '{a_nome}' adicionado com sucesso!")
                                    st.rerun()
                            except Exception as e:
                                db.rollback()
                                st.error(f"Erro ao salvar: {e}")
                                
    with admin_tab3:
        st.subheader("Carga em Lote por Arquivo Excel")
        st.write("Faça o download do modelo, preencha-o e envie o arquivo preenchido para cadastrar múltiplos registros rapidamente.")
        
        col_import_p, col_import_a = st.columns(2)
        
        with col_import_p:
            st.markdown("#### 👨‍🏫 Importação de Professores")
            cols_prof_excel = ['nome', 'email', 'viagem', 'onibus']
            prof_tpl = criar_template_excel(cols_prof_excel)
            st.download_button(
                label="⬇️ Baixar Modelo Excel - Professores",
                data=prof_tpl,
                file_name="modelo_professores.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            uploaded_p_file = st.file_uploader("Upload da Lista de Professores", type=['xlsx'], key='up_prof_p')
            if uploaded_p_file:
                try:
                    df = pd.read_excel(uploaded_p_file)
                    with get_db() as db:
                        count, duplicates_skipped = processar_excel_professores(df, db)
                    if duplicates_skipped > 0:
                        st.success(f"✅ {count} novos professores cadastrados com sucesso! ({duplicates_skipped} registros duplicados foram ignorados)")
                    else:
                        st.success(f"✅ {count} novos professores cadastrados!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao processar: {e}")
                    
        with col_import_a:
            st.markdown("#### 🎓 Importação de Alunos")
            cols_aluno_excel = ['nome', 'ra', 'email', 'ano', 'viagem_destino', 'onibus']
            aluno_tpl = criar_template_excel(cols_aluno_excel)
            st.download_button(
                label="⬇️ Baixar Modelo Excel - Alunos",
                data=aluno_tpl,
                file_name="modelo_alunos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            uploaded_a_file = st.file_uploader("Upload da Lista de Alunos", type=['xlsx'], key='up_aluno_a')
            if uploaded_a_file:
                try:
                    df = pd.read_excel(uploaded_a_file)
                    with get_db() as db:
                        count, duplicates_skipped = processar_excel_alunos(df, db)
                    if duplicates_skipped > 0:
                        st.success(f"✅ {count} novos alunos cadastrados com sucesso! ({duplicates_skipped} registros duplicados ou inválidos foram ignorados)")
                    else:
                        st.success(f"✅ {count} novos alunos cadastrados!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao processar: {e}")
                    
    with admin_tab4:
        st.subheader("💬 Feedbacks, Erros e Sugestões Reportados")
        st.write("Abaixo estão os reportes enviados pelos usuários através do botão flutuante no canto da tela.")
        
        with get_db() as db:
            fbs = db.query(Feedback).order_by(Feedback.data_hora.desc()).all()
            
        if not fbs:
            st.info("ℹ️ Nenhum feedback cadastrado até o momento.")
        else:
            fb_filtro_status = st.selectbox("Filtrar por Status:", ["Todos", "Pendentes", "Resolvidos"], key="fb_filter_status")
            
            dados_fb = []
            for f in fbs:
                status_str = "Resolvido" if f.resolvido == 1 else "Pendente"
                if fb_filtro_status == "Pendentes" and f.resolvido != 0:
                    continue
                if fb_filtro_status == "Resolvidos" and f.resolvido != 1:
                    continue
                
                dados_fb.append({
                    "ID": f.id,
                    "Data/Hora": f.data_hora.strftime("%d/%m/%Y %H:%M:%S"),
                    "Nome": f.nome or "Anônimo",
                    "Tipo": f.tipo,
                    "Seção": f.secao,
                    "Descrição": f.descricao,
                    "Status": status_str
                })
                
            if not dados_fb:
                st.caption("Nenhum feedback corresponde ao filtro selecionado.")
            else:
                df_fb_show = pd.DataFrame(dados_fb)
                st.dataframe(df_fb_show, use_container_width=True, hide_index=True)
                
                # Ações individuais
                st.markdown("#### 🛠️ Gerenciar Reporte")
                fb_ids = [str(d["ID"]) for d in dados_fb]
                sel_fb_id = st.selectbox("Selecione o ID do reporte para atualizar:", fb_ids, key="sel_fb_id")
                
                if sel_fb_id:
                    fb_id_int = int(sel_fb_id)
                    with get_db() as db:
                        fb_obj = db.query(Feedback).filter(Feedback.id == fb_id_int).first()
                        
                    if fb_obj:
                        st.markdown(f"""
                        <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 15px; border-radius: 8px; margin-bottom: 15px; color: #0f172a;">
                            <b>Enviado por:</b> {fb_obj.nome or 'Anônimo'} | <b>Tipo:</b> {fb_obj.tipo} | <b>Seção:</b> {fb_obj.secao}<br>
                            <b>Descrição:</b> <i>"{fb_obj.descricao}"</i>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_act1, col_act2 = st.columns(2)
                        with col_act1:
                            if fb_obj.resolvido == 0:
                                if st.button("✔️ Marcar como Resolvido", key="btn_solve_fb"):
                                    with get_db() as db:
                                        db.query(Feedback).filter(Feedback.id == fb_id_int).update({"resolvido": 1})
                                        db.commit()
                                    st.success(f"Reporte #{fb_id_int} marcado como resolvido!")
                                    st.rerun()
                            else:
                                if st.button("🔄 Reabrir Reporte", key="btn_reopen_fb"):
                                    with get_db() as db:
                                        db.query(Feedback).filter(Feedback.id == fb_id_int).update({"resolvido": 0})
                                        db.commit()
                                    st.success(f"Reporte #{fb_id_int} reaberto!")
                                    st.rerun()
                        with col_act2:
                            if st.button("🗑️ Excluir Reporte", key="btn_delete_fb"):
                                with get_db() as db:
                                    db.query(Feedback).filter(Feedback.id == fb_id_int).delete()
                                    db.commit()
                                st.success(f"Reporte #{fb_id_int} excluído com sucesso!")
                                st.rerun()
                                
    with admin_tab5:
        st.subheader("🚨 Perigo: Limpeza do Banco de Dados")
        st.warning("Essas ações são permanentes e não podem ser desfeitas. Use com cautela durante testes.")
        
        c_r1, c_r2, c_r3, c_r4 = st.columns(4)
        with c_r1:
            st.write("**Ocorrências**")
            btn_clean_o = st.button("🚨 Apagar Todas as Ocorrências", key="clean_oco")
            if btn_clean_o:
                with get_db() as db:
                    try:
                        db.query(Avaliacao).delete()
                        db.commit()
                        st.success("Histórico de ocorrências apagado!")
                        st.rerun()
                    except Exception as e:
                        db.rollback()
                        st.error(f"Erro: {e}")
                        
        with c_r2:
            st.write("**Alunos**")
            btn_clean_a = st.button("🚨 Apagar Todos os Alunos", key="clean_alu")
            if btn_clean_a:
                with get_db() as db:
                    try:
                        db.query(Avaliacao).delete()  # Deleta avaliações ligadas (cascade)
                        db.query(Aluno).delete()
                        db.commit()
                        st.success("Todos os alunos e histórico apagados!")
                        st.rerun()
                    except Exception as e:
                        db.rollback()
                        st.error(f"Erro: {e}")
                        
        with c_r3:
            st.write("**Professores**")
            btn_clean_p = st.button("🚨 Apagar Todos os Professores", key="clean_prof")
            if btn_clean_p:
                with get_db() as db:
                    try:
                        db.query(Avaliacao).delete()  # Deleta avaliações ligadas (cascade)
                        db.query(Professor).delete()
                        db.commit()
                        st.success("Todos os professores e histórico apagados!")
                        st.rerun()
                    except Exception as e:
                        db.rollback()
                        st.error(f"Erro: {e}")
                        
        with c_r4:
            st.write("**Feedbacks**")
            btn_clean_f = st.button("🚨 Apagar Todos os Feedbacks", key="clean_feed")
            if btn_clean_f:
                with get_db() as db:
                    try:
                        db.query(Feedback).delete()
                        db.commit()
                        st.success("Todos os feedbacks apagados!")
                        st.rerun()
                    except Exception as e:
                        db.rollback()
                        st.error(f"Erro: {e}")

# Rodapé lateral
st.sidebar.markdown("---")
st.sidebar.caption("Desenvolvido por cleytonnot-crypto & Antigravity v1.0")
st.sidebar.caption(
    "A concepção pedagógica, critérios de avaliação e autoria intelectual do sistema são de cleytonnot-crypto. "
    "A implementação técnica e o refinamento de sintaxe deste sistema contaram com o auxílio de ferramentas de "
    "Inteligência Artificial, seguindo os termos de serviço dos respectivos provedores."
)
