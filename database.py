import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Text, text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy import event
from datetime import datetime, timezone, timedelta
import pandas as pd

# Configuração do Engine e Base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "banco_viagens.db")
DB_URL = f"sqlite:///{db_path}"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def agora_br():
    """Retorna a data e hora atual no fuso de Brasília (UTC-3) sem tzinfo para o SQLite."""
    fuso_br = timezone(timedelta(hours=-3))
    return datetime.now(fuso_br).replace(tzinfo=None)

class Professor(Base):
    __tablename__ = "professores"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    viagem = Column(String(50)) # ex: RJ, BSB, MG
    onibus = Column(String(50), nullable=True) # ex: Ônibus 1, Ônibus 2

class Aluno(Base):
    __tablename__ = "alunos"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    ra = Column(String(20), unique=True) # Registro Acadêmico
    email = Column(String(100), unique=True)
    ano = Column(String(20)) # ex: 9º Ano A
    viagem_destino = Column(String(50))
    onibus = Column(String(50), nullable=True) # ex: Ônibus 1, Ônibus 2

class Avaliacao(Base):
    __tablename__ = "avaliacoes"
    
    id = Column(Integer, primary_key=True, index=True)
    professor_id = Column(Integer, ForeignKey("professores.id"), nullable=False)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=False)
    data_hora = Column(DateTime, default=agora_br)
    atitude_aa = Column(String(255)) # Critérios selecionados
    comportamento_cs = Column(String(255)) # Critérios selecionados
    desconto_aa = Column(Float, default=0.0) # Pontos perdidos em AA
    desconto_cs = Column(Float, default=0.0) # Pontos perdidos em CS
    observacoes = Column(Text)

    professor = relationship("Professor")
    aluno = relationship("Aluno")

class Feedback(Base):
    __tablename__ = "feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=True)
    tipo = Column(String(50), nullable=False)  # Erro / Bug, Sugestão, Dúvida, Outro
    secao = Column(String(50), nullable=False)  # Geral, Registrar Ocorrência, Dashboard, Administração
    descricao = Column(Text, nullable=False)
    data_hora = Column(DateTime, default=agora_br)
    resolvido = Column(Integer, default=0)  # 0 = Pendente, 1 = Resolvido

class Configuracao(Base):
    __tablename__ = "configuracoes"
    
    id = Column(Integer, primary_key=True, index=True)
    chave = Column(String(50), unique=True, nullable=False)
    valor = Column(String(255), nullable=False)

class Rubrica(Base):
    __tablename__ = "rubricas"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), unique=True, nullable=False)
    max_aa = Column(Float, nullable=False, default=1.0)
    max_cs = Column(Float, nullable=False, default=1.0)
    termos_mapeamento = Column(Text, nullable=True) # Semicolon-separated keywords
    
    criterios = relationship("CriterioRubrica", back_populates="rubrica", cascade="all, delete-orphan")

class CriterioRubrica(Base):
    __tablename__ = "criterios_rubrica"
    
    id = Column(Integer, primary_key=True, index=True)
    rubrica_id = Column(Integer, ForeignKey("rubricas.id"), nullable=False)
    tipo = Column(String(2), nullable=False) # "AA" or "CS"
    descricao = Column(Text, nullable=False)
    desconto_padrao = Column(Float, nullable=False, default=0.2)
    desconto_leve = Column(Float, nullable=False, default=0.1)
    desconto_moderado = Column(Float, nullable=False, default=0.3)
    desconto_grave = Column(Float, nullable=False, default=0.5)
    
    rubrica = relationship("Rubrica", back_populates="criterios")


# ==============================================================================
# SISTEMA DE SINCRONIZAÇÃO COM O GOOGLE SHEETS
# ==============================================================================

SHEET_MAP = {
    "professores": "Professores",
    "alunos": "Alunos",
    "criterios_rubrica": "Criterios",
    "avaliacoes": "Ocorrencias",
    "feedbacks": "Feedbacks",
    "configuracoes": "Configuracoes"
}

def get_gsheets_conn():
    import streamlit as st
    from streamlit_gsheets import GSheetsConnection
    try:
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        print(f"Erro ao conectar com Google Sheets: {e}")
        return None

def pull_all_from_sheets():
    """
    Baixa os dados do Google Sheets e sincroniza no banco SQLite local.
    Roda apenas uma vez no início da sessão do Streamlit.
    """
    import streamlit as st
    if not st.runtime.exists():
        return
        
    conn = get_gsheets_conn()
    if not conn:
        print("Google Sheets indisponível para sincronização de pull.")
        return
        
    db = SessionLocal()
    try:
        print("=== INICIANDO PULL DO GOOGLE SHEETS PARA SQLITE ===")
        # Puxa na ordem correta de chaves estrangeiras (professores e alunos primeiro)
        for table_name in ["professores", "alunos", "criterios_rubrica", "avaliacoes", "feedbacks", "configuracoes"]:
            sheet_name = SHEET_MAP[table_name]
            try:
                df = conn.read(worksheet=sheet_name, ttl=0)
                df = df.dropna(how="all").reset_index(drop=True)
                df.columns = [str(col).strip().lower() for col in df.columns]
                
                if not df.empty:
                    db.execute(text(f"DELETE FROM {table_name}"))
                    
                    if table_name == "professores":
                        for col in ["nome", "email", "viagem", "onibus"]:
                            if col not in df.columns:
                                df[col] = None
                        df["id"] = range(1, len(df) + 1)
                        df[["id", "nome", "email", "viagem", "onibus"]].to_sql(name="professores", con=engine, if_exists="append", index=False)
                        
                    elif table_name == "alunos":
                        for col in ["ra", "nome", "ano", "viagem_destino", "onibus"]:
                            if col not in df.columns:
                                df[col] = None
                        df["id"] = range(1, len(df) + 1)
                        if "email" not in df.columns:
                            df["email"] = df["ra"].astype(str) + "@aluno.cmc.com.br"
                        else:
                            df["email"] = df["email"].fillna(df["ra"].astype(str) + "@aluno.cmc.com.br")
                        df[["id", "nome", "ra", "email", "ano", "viagem_destino", "onibus"]].to_sql(name="alunos", con=engine, if_exists="append", index=False)
                        
                    elif table_name == "criterios_rubrica":
                        db.execute(text("DELETE FROM criterios_rubrica"))
                        db.execute(text("DELETE FROM rubricas"))
                        
                        unique_rubricas = df["rubrica"].unique()
                        rubrica_ids = {}
                        for name in unique_rubricas:
                            if not name or pd.isna(name):
                                continue
                            max_aa, max_cs = 1.0, 1.0
                            termos = ""
                            name_clean = str(name).strip().lower()
                            if "3" in name_clean:
                                max_aa, max_cs = 0.4, 1.6
                                termos = "3ª SÉRIE; 3ª SERIE; 3 SÉRIE; 3 SERIE; 3EM; 3º EM; 3ºEM; 3 ANO; 3º ANO"
                            elif "2" in name_clean:
                                max_aa, max_cs = 1.0, 1.0
                                termos = "2ª SÉRIE; 2ª SERIE; 2 SÉRIE; 2 SERIE; 2EM; 2º EM; 2ºEM"
                            
                            db.execute(text("INSERT INTO rubricas (nome, max_aa, max_cs, termos_mapeamento) VALUES (:nome, :max_aa, :max_cs, :termos)"),
                                       {"nome": str(name).strip(), "max_aa": max_aa, "max_cs": max_cs, "termos": termos})
                            r_id = db.execute(text("SELECT last_insert_rowid()")).scalar()
                            rubrica_ids[str(name).strip().lower()] = r_id
                            
                        criteria_data = []
                        for idx, row in df.iterrows():
                            rub_name = row["rubrica"]
                            if not rub_name or pd.isna(rub_name):
                                continue
                            rid = rubrica_ids.get(str(rub_name).strip().lower())
                            if not rid:
                                continue
                            criteria_data.append({
                                "id": idx + 1,
                                "rubrica_id": rid,
                                "tipo": str(row["tipo"]).strip().upper(),
                                "descricao": str(row["descricao"]).strip(),
                                "desconto_padrao": float(row.get("desconto_moderado", 0.3) if pd.notna(row.get("desconto_moderado")) else 0.3),
                                "desconto_leve": float(row.get("desconto_leve", 0.1) if pd.notna(row.get("desconto_leve")) else 0.1),
                                "desconto_moderado": float(row.get("desconto_moderado", 0.3) if pd.notna(row.get("desconto_moderado")) else 0.3),
                                "desconto_grave": float(row.get("desconto_grave", 0.5) if pd.notna(row.get("desconto_grave")) else 0.5)
                            })
                        if criteria_data:
                            pd.DataFrame(criteria_data).to_sql(name="criterios_rubrica", con=engine, if_exists="append", index=False)
                            
                    elif table_name == "avaliacoes":
                        records = []
                        for idx, row in df.iterrows():
                            prof_email_val = str(row.get("professor_email", "")).strip().lower()
                            prof_id = db.execute(text("SELECT id FROM professores WHERE LOWER(email) = :email"), {"email": prof_email_val}).scalar()
                            if not prof_id:
                                prof_id = db.execute(text("SELECT id FROM professores LIMIT 1")).scalar() or 1
                                
                            aluno_ra_val = str(row.get("aluno_ra", "")).strip()
                            aluno_id = db.execute(text("SELECT id FROM alunos WHERE ra = :ra"), {"ra": aluno_ra_val}).scalar()
                            if not aluno_id:
                                aluno_id = db.execute(text("SELECT id FROM alunos LIMIT 1")).scalar() or 1
                                
                            dt_str = str(row["data_hora"]).strip()
                            try:
                                dt = datetime.strptime(dt_str, "%d/%m/%Y %H:%M:%S")
                            except Exception:
                                try:
                                    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                                except Exception:
                                    dt = datetime.now()
                                    
                            records.append({
                                "id": int(row["id"]) if pd.notna(row["id"]) and str(row["id"]).replace(".0","").isdigit() else (idx + 1),
                                "professor_id": prof_id,
                                "aluno_id": aluno_id,
                                "data_hora": dt.strftime("%Y-%m-%d %H:%M:%S"),
                                "atitude_aa": row["criterios_aa"] if pd.notna(row["criterios_aa"]) and row["criterios_aa"] != "Nenhum" else None,
                                "comportamento_cs": row["criterios_cs"] if pd.notna(row["criterios_cs"]) and row["criterios_cs"] != "Nenhum" else None,
                                "desconto_aa": float(row.get("desconto_aa", 0.0) if pd.notna(row.get("desconto_aa")) else 0.0),
                                "desconto_cs": float(row.get("desconto_cs", 0.0) if pd.notna(row.get("desconto_cs")) else 0.0),
                                "observacoes": row["observacoes"] if pd.notna(row["observacoes"]) else ""
                            })
                        if records:
                            pd.DataFrame(records).to_sql(name="avaliacoes", con=engine, if_exists="append", index=False)
                            
                    elif table_name == "feedbacks":
                        records = []
                        for idx, row in df.iterrows():
                            dt_str = str(row["data_hora"]).strip()
                            try:
                                dt = datetime.strptime(dt_str, "%d/%m/%Y %H:%M:%S")
                            except Exception:
                                try:
                                    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                                except Exception:
                                    dt = datetime.now()
                            records.append({
                                "id": int(row["id"]) if pd.notna(row["id"]) and str(row["id"]).replace(".0","").isdigit() else (idx + 1),
                                "nome": row["nome"] if pd.notna(row["nome"]) else "Anônimo",
                                "tipo": row["tipo"] if pd.notna(row["tipo"]) else "Sugestão",
                                "secao": row["secao"] if pd.notna(row["secao"]) else "Geral",
                                "descricao": row["descricao"] if pd.notna(row["descricao"]) else "",
                                "data_hora": dt.strftime("%Y-%m-%d %H:%M:%S"),
                                "resolvido": 1 if str(row["resolvido"]).lower() in ["1", "true", "resolvido"] else 0
                            })
                        if records:
                            pd.DataFrame(records).to_sql(name="feedbacks", con=engine, if_exists="append", index=False)
                            
                    elif table_name == "configuracoes":
                        df[["id", "chave", "valor"]].to_sql(name="configuracoes", con=engine, if_exists="append", index=False)
                        
                else:
                    # Planilha vazia, envia dados locais semeados
                    push_table_to_sheets(table_name)
                    
            except Exception as e:
                # Planilha não existe, envia e cria a aba
                print(f"Erro ao ler/aba inexistente {sheet_name}: {e}. Criando aba...")
                push_table_to_sheets(table_name)
                
        db.commit()
        print("=== PULL CONCLUÍDO COM SUCESSO ===")
    except Exception as e:
        db.rollback()
        print(f"Erro no pull geral: {e}")
    finally:
        db.close()

def push_table_to_sheets(table_name):
    """Grava os dados locais do SQLite de volta no Google Sheets."""
    import streamlit as st
    if not st.runtime.exists():
        return
        
    conn = get_gsheets_conn()
    if not conn:
        return
        
    sheet_name = SHEET_MAP.get(table_name)
    if not sheet_name:
        return
        
    print(f"Puxando {table_name} do SQLite para salvar no Google Sheets ({sheet_name})...")
    try:
        if table_name == "professores":
            df_sqlite = pd.read_sql("SELECT nome, email, viagem, onibus FROM professores", con=engine)
            
        elif table_name == "alunos":
            df_sqlite = pd.read_sql("SELECT ra, nome, ano, viagem_destino, onibus FROM alunos", con=engine)
            
        elif table_name == "criterios_rubrica":
            df_sqlite = pd.read_sql("""
                SELECT r.nome as rubrica, c.tipo, c.descricao, c.desconto_leve, c.desconto_moderado, c.desconto_grave
                FROM criterios_rubrica c
                JOIN rubricas r ON c.rubrica_id = r.id
            """, con=engine)
            
        elif table_name == "avaliacoes":
            df_sqlite = pd.read_sql("""
                SELECT 
                    a.id,
                    a.data_hora,
                    p.email as professor_email,
                    p.nome as professor_nome,
                    al.ra as aluno_ra,
                    al.nome as aluno_nome,
                    al.ano as aluno_turma,
                    al.viagem_destino as destino,
                    al.onibus,
                    COALESCE(a.atitude_aa, 'Nenhum') as criterios_aa,
                    a.desconto_aa,
                    COALESCE(a.comportamento_cs, 'Nenhum') as criterios_cs,
                    a.desconto_cs,
                    a.observacoes
                FROM avaliacoes a
                JOIN professores p ON a.professor_id = p.id
                JOIN alunos al ON a.aluno_id = al.id
            """, con=engine)
            if not df_sqlite.empty:
                df_sqlite["data_hora"] = pd.to_datetime(df_sqlite["data_hora"]).dt.strftime("%d/%m/%Y %H:%M:%S")
                
        elif table_name == "feedbacks":
            df_sqlite = pd.read_sql("SELECT id, data_hora, nome, tipo, secao, descricao, resolvido FROM feedbacks", con=engine)
            if not df_sqlite.empty:
                df_sqlite["data_hora"] = pd.to_datetime(df_sqlite["data_hora"]).dt.strftime("%d/%m/%Y %H:%M:%S")
                df_sqlite["resolvido"] = df_sqlite["resolvido"].apply(lambda r: "Resolvido" if r == 1 else "Pendente")
                
        elif table_name == "configuracoes":
            df_sqlite = pd.read_sql("SELECT id, chave, valor FROM configuracoes", con=engine)
            
        else:
            return
            
        # Garante colunas de cabeçalho mesmo se vazio
        if df_sqlite.empty:
            colunas_vazias = {
                "professores": ["nome", "email", "viagem", "onibus"],
                "alunos": ["ra", "nome", "ano", "viagem_destino", "onibus"],
                "criterios_rubrica": ["rubrica", "tipo", "descricao", "desconto_leve", "desconto_moderado", "desconto_grave"],
                "avaliacoes": ["id", "data_hora", "professor_email", "professor_nome", "aluno_ra", "aluno_nome", "aluno_turma", "destino", "onibus", "criterios_aa", "desconto_aa", "criterios_cs", "desconto_cs", "observacoes"],
                "feedbacks": ["id", "data_hora", "nome", "tipo", "secao", "descricao", "resolvido"],
                "configuracoes": ["id", "chave", "valor"]
            }
            df_sqlite = pd.DataFrame(columns=colunas_vazias[table_name])
            
        conn.update(worksheet=sheet_name, data=df_sqlite)
        print(f"Google Sheets atualizado para {sheet_name}.")
    except Exception as e:
        print(f"Erro ao empurrar {table_name} para GSheets: {e}")

# SQLAlchemy Listeners para empurrar alterações de forma transparente
@event.listens_for(Session, 'before_commit')
def receive_before_commit(session):
    modified_tables = set()
    for obj in session.new.union(session.dirty).union(session.deleted):
        if hasattr(obj, "__tablename__"):
            t_name = obj.__tablename__
            # Mapeamento do tablename do SQLAlchemy para a sincronização
            modified_tables.add(t_name)
    session.info['modified_tables'] = modified_tables

@event.listens_for(Session, 'after_commit')
def receive_after_commit(session):
    modified_tables = session.info.get('modified_tables', set())
    for t_name in modified_tables:
        # Se for rubrica ou criterio, atualiza a aba Criterios
        if t_name in ["rubricas", "criterios_rubrica"]:
            push_table_to_sheets("criterios_rubrica")
        else:
            push_table_to_sheets(t_name)


def inicializar_banco():
    """Cria as tabelas no banco de dados se elas não existirem e adiciona colunas necessárias."""
    Base.metadata.create_all(bind=engine)
    
    # Seeding inicial de Rubricas se a tabela estiver vazia
    db = SessionLocal()
    try:
        try:
            rubricas_count = db.query(Rubrica).count()
        except Exception:
            rubricas_count = 0
            
        if rubricas_count == 0:
            print("Populando rubricas padrão no SQLite...")
            defaults = [
                {
                    "nome": "3ª série",
                    "max_aa": 0.4,
                    "max_cs": 1.6,
                    "termos_mapeamento": "3ª SÉRIE; 3ª SERIE; 3 SÉRIE; 3 SERIE; 3EM; 3º EM; 3ºEM; 3 ANO; 3º ANO",
                    "AA": [
                        ("Apresenta oscilações pontuais de atenção", 0.2),
                        ("Demonstra desinteresse frequente nas explicações/atividades", 0.4),
                    ],
                    "CS": [
                        ("Apresenta pequenas falhas pontuais no cumprimento de regras/orientações", 0.2),
                        ("Descumpre regras ou necessita intervenções frequentes", 0.4),
                        ("Apresenta atrasos ou desorganização ocasionais com horários e pertences", 0.2),
                        ("Compromete o andamento das atividades por atrasos ou desorganização", 0.4),
                        ("Apresenta dificuldades ocasionais de convivência", 0.2),
                        ("Envolve-se em conflitos, provocações ou atitudes desrespeitosas", 0.4),
                        ("Necessita lembretes pontuais sobre postura nos espaços visitados", 0.2),
                        ("Tem atitudes inadequadas em ambientes institucionais ou públicos", 0.4),
                    ]
                },
                {
                    "nome": "2ª série",
                    "max_aa": 1.0,
                    "max_cs": 1.0,
                    "termos_mapeamento": "2ª SÉRIE; 2ª SERIE; 2 SÉRIE; 2 SERIE; 2EM; 2º EM; 2ºEM",
                    "AA": [
                        ("Falta de atenção ou conversa paralela durante explicações dos monitores/professores", 0.2),
                        ("Falta de empenho ou recusa em realizar anotações e registros solicitados", 0.2),
                        ("Ausência de registros fotográficos de pontos relevantes da visita (quando solicitado)", 0.2),
                        ("Desinteresse geral ou apatia nas atividades e discussões propostas", 0.2),
                        ("Ações dispersivas ou recusa de engajamento com o espaço visitado", 0.2),
                    ],
                    "CS": [
                        ("Falta de respeito ou grosseria com motoristas, guias, professores ou colegas", 0.2),
                        ("Descumpre regras no ônibus (sujeira, levantar-se em movimento, não usar cinto, som alto sem fone)", 0.2),
                        ("Atraso não justificado nos horários de refeição, reuniões ou recolhimento ao quarto", 0.2),
                        ("Uso inadequado, barulho excessivo ou danos nas dependências dos hotéis e visitas", 0.2),
                        ("Uso inadequado do celular em momentos não permitidos", 0.2),
                        ("Quebra de combinados ou desobediência a instruções diretas da equipe", 0.2),
                    ]
                },
                {
                    "nome": "Geral",
                    "max_aa": 1.0,
                    "max_cs": 1.0,
                    "termos_mapeamento": "",
                    "AA": [
                        ("Falta de atenção ou conversa paralela durante explicações dos monitores/professores", 0.2),
                        ("Falta de empenho ou recusa em realizar anotações e registros solicitados", 0.2),
                        ("Ausência de registros fotográficos de pontos relevantes da visita (quando solicitado)", 0.2),
                        ("Desinteresse geral ou apatia nas atividades e discussões propostas", 0.2),
                        ("Ações dispersivas ou recusa de engajamento com o espaço visitado", 0.2),
                    ],
                    "CS": [
                        ("Falta de respeito ou grosseria com motoristas, guias, professores ou colegas", 0.2),
                        ("Descumpre regras no ônibus (sujeira, levantar-se em movimento, não usar cinto, som alto sem fone)", 0.2),
                        ("Atraso não justificado nos horários de refeição, reuniões ou recolhimento ao quarto", 0.2),
                        ("Uso inadequado, barulho excessivo ou danos nas dependências dos hotéis e visitas", 0.2),
                        ("Uso inadequado do celular em momentos não permitidos", 0.2),
                        ("Quebra de combinados ou desobediência a instruções diretas da equipe", 0.2),
                    ]
                }
            ]
            for r_data in defaults:
                rubrica = Rubrica(
                    nome=r_data["nome"],
                    max_aa=r_data["max_aa"],
                    max_cs=r_data["max_cs"],
                    termos_mapeamento=r_data["termos_mapeamento"]
                )
                db.add(rubrica)
                db.flush()
                
                for desc, desc_padrao in r_data["AA"]:
                    crit = CriterioRubrica(
                        rubrica_id=rubrica.id,
                        tipo="AA",
                        descricao=desc,
                        desconto_padrao=desc_padrao
                    )
                    db.add(crit)
                for desc, desc_padrao in r_data["CS"]:
                    crit = CriterioRubrica(
                        rubrica_id=rubrica.id,
                        tipo="CS",
                        descricao=desc,
                        desconto_padrao=desc_padrao
                    )
                    db.add(crit)
            db.commit()

        # Seeding inicial de Configurações
        try:
            config_count = db.query(Configuracao).count()
        except Exception:
            config_count = 0
            
        if config_count == 0:
            db.add(Configuracao(chave="observacoes_obrigatorias", valor="false"))
            db.commit()

        # Colunas necessárias para 'alunos'
        colunas_alunos = {
            "onibus": "VARCHAR(50)",
            "ra": "VARCHAR(20)",
            "email": "VARCHAR(100)"
        }
        with engine.connect() as conn:
            colunas_existentes_alunos = [info[1] for info in conn.execute(text("PRAGMA table_info(alunos)")).fetchall()]
            for col, tipo in colunas_alunos.items():
                if col not in colunas_existentes_alunos:
                    try:
                        conn.execute(text(f"ALTER TABLE alunos ADD COLUMN {col} {tipo}"))
                    except Exception as e:
                        print(f"Erro coluna alunos '{col}': {e}")
                        
        # Colunas para 'professores'
        colunas_profs = {
            "onibus": "VARCHAR(50)"
        }
        with engine.connect() as conn:
            colunas_existentes_profs = [info[1] for info in conn.execute(text("PRAGMA table_info(professores)")).fetchall()]
            for col, tipo in colunas_profs.items():
                if col not in colunas_existentes_profs:
                    try:
                        conn.execute(text(f"ALTER TABLE professores ADD COLUMN {col} {tipo}"))
                    except Exception as e:
                        print(f"Erro coluna professores '{col}': {e}")
                        
        # Colunas para 'avaliacoes'
        colunas_avaliacoes = {
            "desconto_aa": "FLOAT DEFAULT 0.0",
            "desconto_cs": "FLOAT DEFAULT 0.0"
        }
        with engine.connect() as conn:
            colunas_existentes_ava = [info[1] for info in conn.execute(text("PRAGMA table_info(avaliacoes)")).fetchall()]
            for col, tipo in colunas_avaliacoes.items():
                if col not in colunas_existentes_ava:
                    try:
                        conn.execute(text(f"ALTER TABLE avaliacoes ADD COLUMN {col} {tipo}"))
                    except Exception as e:
                        print(f"Erro coluna avaliacoes '{col}': {e}")
                        
        # Colunas para 'criterios_rubrica'
        colunas_criterios = {
            "desconto_leve": "FLOAT DEFAULT 0.1",
            "desconto_moderado": "FLOAT DEFAULT 0.3",
            "desconto_grave": "FLOAT DEFAULT 0.5"
        }
        with engine.connect() as conn:
            colunas_existentes_crit = [info[1] for info in conn.execute(text("PRAGMA table_info(criterios_rubrica)")).fetchall()]
            for col, tipo in colunas_criterios.items():
                if col not in colunas_existentes_crit:
                    try:
                        conn.execute(text(f"ALTER TABLE criterios_rubrica ADD COLUMN {col} {tipo}"))
                    except Exception as e:
                        print(f"Erro coluna criterios '{col}': {e}")
    finally:
        db.close()
    print("Banco de dados local inicializado.")

if __name__ == "__main__":
    inicializar_banco()
