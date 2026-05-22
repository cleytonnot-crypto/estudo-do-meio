import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Text, text
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

def inicializar_banco():
    """Cria as tabelas no banco de dados se elas não existirem e adiciona colunas necessárias."""
    Base.metadata.create_all(bind=engine)
    
    # Migração dinâmica para colunas que podem estar ausentes
    db = SessionLocal()
    try:
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
    finally:
        db.close()
    print("Banco de dados inicializado com sucesso!")

if __name__ == "__main__":
    inicializar_banco()
