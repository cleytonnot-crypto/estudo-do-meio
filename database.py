import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Text, text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Configuração do Engine e Base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "banco_viagens.db")
DB_URL = f"sqlite:///{db_path}"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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
    data_hora = Column(DateTime, default=datetime.now)
    atitude_aa = Column(String(255)) # Critérios selecionados
    comportamento_cs = Column(String(255)) # Critérios selecionados
    desconto_aa = Column(Float, default=0.0) # Pontos perdidos em AA
    desconto_cs = Column(Float, default=0.0) # Pontos perdidos em CS
    observacoes = Column(Text)

    # Relacionamentos para facilitar consultas (Opcional, mas recomendado)
    professor = relationship("Professor")
    aluno = relationship("Aluno")

class Feedback(Base):
    __tablename__ = "feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=True)
    tipo = Column(String(50), nullable=False)  # Erro / Bug, Sugestão, Dúvida, Outro
    secao = Column(String(50), nullable=False)  # Geral, Registrar Ocorrência, Dashboard, Administração
    descricao = Column(Text, nullable=False)
    data_hora = Column(DateTime, default=datetime.now)
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

def inicializar_banco():
    """Cria as tabelas no banco de dados se elas não existirem e adiciona colunas necessárias."""
    Base.metadata.create_all(bind=engine)
    
    # Migração dinâmica para colunas que podem estar ausentes
    db = SessionLocal()
    try:
        # Seeding inicial de Rubricas se a tabela estiver vazia
        try:
            rubricas_count = db.query(Rubrica).count()
        except Exception:
            rubricas_count = 0
            
        if rubricas_count == 0:
            print("Populando rubricas padrão...")
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
            print("Populando configurações padrão...")
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
                        print(f"Coluna '{col}' adicionada com sucesso à tabela 'alunos'.")
                    except Exception as e:
                        print(f"Erro ao adicionar coluna '{col}' na tabela 'alunos': {e}")
                        
        # Colunas necessárias para 'professores'
        colunas_profs = {
            "onibus": "VARCHAR(50)"
        }
        with engine.connect() as conn:
            colunas_existentes_profs = [info[1] for info in conn.execute(text("PRAGMA table_info(professores)")).fetchall()]
            for col, tipo in colunas_profs.items():
                if col not in colunas_existentes_profs:
                    try:
                        conn.execute(text(f"ALTER TABLE professores ADD COLUMN {col} {tipo}"))
                        print(f"Coluna '{col}' adicionada com sucesso à tabela 'professores'.")
                    except Exception as e:
                        print(f"Erro ao adicionar coluna '{col}' na tabela 'professores': {e}")
                        
        # Colunas necessárias para 'avaliacoes'
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
                        print(f"Coluna '{col}' adicionada com sucesso à tabela 'avaliacoes'.")
                    except Exception as e:
                        print(f"Erro ao adicionar coluna '{col}' na tabela 'avaliacoes': {e}")

        # Colunas necessárias para 'criterios_rubrica'
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
                        print(f"Coluna '{col}' adicionada com sucesso à tabela 'criterios_rubrica'.")
                    except Exception as e:
                        print(f"Erro ao adicionar coluna '{col}' na tabela 'criterios_rubrica': {e}")
    finally:
        db.close()
    print("Banco de dados inicializado com sucesso!")

if __name__ == "__main__":
    inicializar_banco()
