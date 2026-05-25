import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# ==============================================================================
# CONFIGURAÇÃO DE SEGURANÇA E SECRETS.TOML
# O st-gsheets-connection exige configuração no arquivo `.streamlit/secrets.toml`.
# Veja abaixo o formato esperado para conexões privadas e públicas:
#
# Opção A: Conexão com planilha pública (Apenas visualização/leitura):
# [connections.gsheets]
# spreadsheet = "https://docs.google.com/spreadsheets/d/SUA_PLANILHA_ID/edit"
#
# Opção B: Conexão com planilha privada (Leitura e Escrita - RECOMENDADO):
# [connections.gsheets]
# spreadsheet = "https://docs.google.com/spreadsheets/d/SUA_PLANILHA_ID/edit"
# type = "service_account"
# project_id = "seu-projeto-gcp"
# private_key_id = "sua-chave-privada-id"
# private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC..."
# client_email = "seu-service-account@seu-projeto-gcp.iam.gserviceaccount.com"
# client_id = "seu-client-id"
# auth_uri = "https://accounts.google.com/o/oauth2/auth"
# token_uri = "https://oauth2.googleapis.com/token"
# auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
# client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
# ==============================================================================

# Configuração da página Streamlit com visual premium
st.set_page_config(
    page_title="Registro de Ocorrências - Estudo do Meio",
    page_icon="📝",
    layout="centered"
)

# Estilização CSS premium (fontes modernas, cores harmoniosas e cantos arredondados)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .main-title {
        color: #1e293b;
        font-weight: 700;
        font-size: 2.25rem;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .subtitle {
        color: #64748b;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    
    /* Formulários e cartões brancos com sombras suaves */
    div[data-testid="stForm"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 16px !important;
        padding: 28px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
    }
    </style>
""", unsafe_allow_html=True)


def inicializar_conexao():
    """
    Configura a conexão com o Google Sheets usando a biblioteca st-gsheets-connection.
    Esta função busca automaticamente os dados sob a seção [connections.gsheets]
    no arquivo .streamlit/secrets.toml.
    """
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn
    except Exception as e:
        st.error(f"Erro ao configurar conexão com o Google Sheets: {e}")
        st.info("Verifique se as credenciais estão configuradas corretamente em `.streamlit/secrets.toml`.")
        return None


def ler_dados_planilha(conn):
    """
    Lê os dados atuais da planilha do Google Sheets.
    Usa ttl=0 para evitar ler dados em cache (garantindo dados sempre atualizados).
    """
    try:
        # Lê os dados da planilha padrão
        df = conn.read(ttl=0)
        # Limpa colunas ou linhas completamente vazias que possam vir da leitura
        df = df.dropna(how="all")
        return df
    except Exception as e:
        st.error(f"Erro ao ler dados do Google Sheets: {e}")
        # Retorna um DataFrame vazio com as colunas esperadas em caso de erro/planilha vazia
        colunas_esperadas = [
            "id", "data_hora", "professor_email", "professor_nome", 
            "aluno_ra", "aluno_nome", "aluno_turma", "destino", "onibus", 
            "criterios_aa", "desconto_aa", "criterios_cs", "desconto_cs", "observacoes"
        ]
        return pd.DataFrame(columns=colunas_esperadas)


def salvar_dados_planilha(conn, df_atualizado):
    """
    Atualiza a planilha do Google Sheets com o DataFrame consolidado.
    """
    try:
        conn.update(data=df_atualizado)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados no Google Sheets: {e}")
        return False


def main():
    st.markdown('<h1 class="main-title">📝 Registro de Ocorrência</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Banco de Dados: Google Sheets (st-gsheets-connection)</p>', 
        unsafe_allow_html=True
    )
    
    # 1. Configura/conecta ao Google Sheets
    conn = inicializar_conexao()
    if not conn:
        return
        
    # 2. Lê os dados atuais
    df_atual = ler_dados_planilha(conn)
    
    st.info(f"📊 Total de ocorrências registradas na planilha: {len(df_atual)}")
    
    # 3. Criação do Formulário de Registro
    with st.form("form_ocorrencia", clear_on_submit=True):
        st.subheader("Informações do Registro")
        
        col1, col2 = st.columns(2)
        with col1:
            professor_nome = st.text_input("Nome do Professor/Monitor:", placeholder="Ex: Cleyton Alves")
            professor_email = st.text_input("E-mail do Professor:", placeholder="Ex: cleyton.alves@escola.com")
        with col2:
            aluno_nome = st.text_input("Nome do Aluno:", placeholder="Ex: Bruno Gomes")
            aluno_ra = st.text_input("RA do Aluno (Registro Acadêmico):", placeholder="Ex: 202401")
            
        col3, col4, col5 = st.columns(3)
        with col3:
            aluno_turma = st.text_input("Ano / Turma:", placeholder="Ex: 9º Ano A")
        with col4:
            destino = st.text_input("Destino da Viagem:", placeholder="Ex: MG, RJ, BSB")
        with col5:
            onibus = st.text_input("Ônibus do Aluno (Opcional):", placeholder="Ex: Ônibus 1")
            
        st.divider()
        st.subheader("Detalhes da Ocorrência")
        
        col6, col7 = st.columns(2)
        with col6:
            criterios_aa = st.text_area(
                "Critérios de Atitude Frente à Aprendizagem (AA):",
                placeholder="Ex: Falta de atenção ou conversa paralela durante explicações."
            )
            desconto_aa = st.number_input("Desconto de Pontos em AA (Dedução):", min_value=0.0, max_value=10.0, step=0.1)
        with col7:
            criterios_cs = st.text_area(
                "Critérios de Comportamento Social (CS):",
                placeholder="Ex: Atraso não justificado nos horários combinados."
            )
            desconto_cs = st.number_input("Desconto de Pontos em CS (Dedução):", min_value=0.0, max_value=10.0, step=0.1)
            
        observacoes = st.text_area(
            "Detalhamento e Contextualização do Ocorrido (Obrigatório):",
            placeholder="Descreva as ações, horários e contexto para justificar o registro."
        )
        
        # Botão de envio do formulário
        submetido = st.form_submit_button("💾 Salvar Registro na Planilha", use_container_width=True)
        
        if submetido:
            # 4. Validação de campos obrigatórios
            campos_faltando = []
            if not professor_nome.strip():
                campos_faltando.append("Nome do Professor/Monitor")
            if not professor_email.strip():
                campos_faltando.append("E-mail do Professor")
            if not aluno_nome.strip():
                campos_faltando.append("Nome do Aluno")
            if not aluno_ra.strip():
                campos_faltando.append("RA do Aluno")
            if not observacoes.strip():
                campos_faltando.append("Detalhamento e Contextualização")
                
            # Verifica se pelo menos um critério foi preenchido
            if not criterios_aa.strip() and not criterios_cs.strip():
                st.error("❌ Erro: Você deve descrever pelo menos um critério em Atitude (AA) ou Comportamento (CS).")
            elif campos_faltando:
                st.error(f"❌ Erro: Preencha todos os campos obrigatórios: {', '.join(campos_faltando)}")
            else:
                # 5. Criação do novo registro
                novo_id = int(df_atual["id"].max() + 1) if not df_atual.empty and "id" in df_atual.columns else 1
                
                novo_registro = {
                    "id": novo_id,
                    "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "professor_email": professor_email.strip(),
                    "professor_nome": professor_nome.strip(),
                    "aluno_ra": aluno_ra.strip(),
                    "aluno_nome": aluno_nome.strip(),
                    "aluno_turma": aluno_turma.strip(),
                    "destino": destino.strip(),
                    "onibus": onibus.strip() if onibus.strip() else "Sem ônibus",
                    "criterios_aa": criterios_aa.strip() if criterios_aa.strip() else "Nenhum",
                    "desconto_aa": float(desconto_aa),
                    "criterios_cs": criterios_cs.strip() if criterios_cs.strip() else "Nenhum",
                    "desconto_cs": float(desconto_cs),
                    "observacoes": observacoes.strip()
                }
                
                # Transforma o novo registro em DataFrame
                df_novo = pd.DataFrame([novo_registro])
                
                # Assegura a consistência das colunas
                for col in df_atual.columns:
                    if col not in df_novo.columns:
                        df_novo[col] = None
                for col in df_novo.columns:
                    if col not in df_atual.columns:
                        df_atual[col] = None
                        
                # Reordena colunas para bater com o padrão
                df_novo = df_novo[df_atual.columns]
                
                # Concatena o novo registro com o DataFrame original
                df_consolidado = pd.concat([df_atual, df_novo], ignore_index=True)
                
                # Salva de volta no Google Sheets
                sucesso = salvar_dados_planilha(conn, df_consolidado)
                
                if sucesso:
                    st.success("✅ Registro adicionado e sincronizado com o Google Sheets com sucesso!")
                    # Recarrega a página para exibir os novos dados atualizados
                    st.rerun()


if __name__ == "__main__":
    main()
