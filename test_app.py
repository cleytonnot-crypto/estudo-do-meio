import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Garante que o diretório do projeto esteja no path para importar database
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_path)

from database import Base, Professor, Aluno, Avaliacao, Feedback, inicializar_banco

# Configuração de banco de dados em memória para testes isolados
TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture(name="db_session", scope="function")
def fixture_db_session():
    """Cria tabelas em um banco temporário em memória e disponibiliza uma sessão."""
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Cria todas as tabelas no banco de teste
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_criar_professor(db_session):
    """Testa a criação de um professor no banco de dados e valida os atributos."""
    novo_prof = Professor(
        nome="Professor Teste Pytest",
        email="pytest.prof@escola.com.br",
        viagem="BSB",
        onibus="Ônibus 1"
    )
    db_session.add(novo_prof)
    db_session.commit()
    
    prof_db = db_session.query(Professor).filter(Professor.email == "pytest.prof@escola.com.br").first()
    assert prof_db is not None
    assert prof_db.nome == "Professor Teste Pytest"
    assert prof_db.viagem == "BSB"
    assert prof_db.onibus == "Ônibus 1"

def test_criar_aluno(db_session):
    """Testa a criação de um aluno no banco de dados, incluindo RA e Ônibus."""
    novo_aluno = Aluno(
        nome="Aluno Teste Pytest",
        ra="888888",
        email="pytest.aluno@escola.com.br",
        ano="9º Ano C",
        viagem_destino="RJ",
        onibus="Ônibus 2"
    )
    db_session.add(novo_aluno)
    db_session.commit()
    
    aluno_db = db_session.query(Aluno).filter(Aluno.ra == "888888").first()
    assert aluno_db is not None
    assert aluno_db.nome == "Aluno Teste Pytest"
    assert aluno_db.email == "pytest.aluno@escola.com.br"
    assert aluno_db.ano == "9º Ano C"
    assert aluno_db.viagem_destino == "RJ"
    assert aluno_db.onibus == "Ônibus 2"

def test_criar_ocorrencia(db_session):
    """Testa o registro de uma ocorrência (Avaliação) ligada a um professor e um aluno."""
    # Cria professor e aluno de teste
    prof = Professor(nome="Prof Ocorrência", email="prof.oco@escola.com.br", viagem="MG")
    aluno = Aluno(nome="Aluno Ocorrência", ra="777777", email="aluno.oco@escola.com.br", viagem_destino="MG")
    db_session.add_all([prof, aluno])
    db_session.commit()
    
    # Registra ocorrência
    ocorrencia = Avaliacao(
        professor_id=prof.id,
        aluno_id=aluno.id,
        atitude_aa="Anotações sempre que possível",
        comportamento_cs="Uso adequado de todas as dependências dos hotéis",
        observacoes="Fez excelentes anotações e se comportou muito bem no hotel."
    )
    db_session.add(ocorrencia)
    db_session.commit()
    
    # Busca e valida
    oco_db = db_session.query(Avaliacao).filter(Avaliacao.aluno_id == aluno.id).first()
    assert oco_db is not None
    assert oco_db.professor_id == prof.id
    assert oco_db.atitude_aa == "Anotações sempre que possível"
    assert oco_db.comportamento_cs == "Uso adequado de todas as dependências dos hotéis"
    assert oco_db.observacoes == "Fez excelentes anotações e se comportou muito bem no hotel."
    assert oco_db.aluno.nome == "Aluno Ocorrência"
    assert oco_db.professor.nome == "Prof Ocorrência"

def test_criar_feedback(db_session):
    """Testa a criação de um relato de feedback no banco de dados."""
    novo_fb = Feedback(
        nome="Usuário Teste",
        tipo="Erro / Bug",
        secao="Dashboard",
        descricao="O gráfico de ocorrências por ônibus está quebrando quando não há dados."
    )
    db_session.add(novo_fb)
    db_session.commit()
    
    fb_db = db_session.query(Feedback).filter(Feedback.nome == "Usuário Teste").first()
    assert fb_db is not None
    assert fb_db.tipo == "Erro / Bug"
    assert fb_db.secao == "Dashboard"
    assert fb_db.descricao == "O gráfico de ocorrências por ônibus está quebrando quando não há dados."
    assert fb_db.resolvido == 0

def test_case_insensitive_aluno_email(db_session):
    """Testa se a restrição de email do aluno é case-insensitive no fluxo do app."""
    from sqlalchemy import func
    from database import Aluno
    
    # Adiciona primeiro aluno
    aluno1 = Aluno(nome="Aluno A", ra="123", email="teste@escola.com.br")
    db_session.add(aluno1)
    db_session.commit()
    
    # Tenta verificar se existe duplicado de forma case-insensitive
    email_novo = "TESTE@ESCOLA.COM.BR"
    duplicate = db_session.query(Aluno).filter(
        func.lower(Aluno.email) == email_novo.lower()
    ).first()
    
    assert duplicate is not None
    assert duplicate.nome == "Aluno A"

def test_limpar_valor_excel_helper():
    """Testa a função de limpeza de valores do Excel."""
    from app import limpar_valor_excel, limpar_email, limpar_nome
    
    assert limpar_valor_excel("12345.0") == "12345"
    assert limpar_valor_excel("12345") == "12345"
    assert limpar_valor_excel("Ônibus 1.0") == "Ônibus 1.0"
    assert limpar_valor_excel(None) is None
    assert limpar_valor_excel("None") is None
    assert limpar_valor_excel("nan") is None
    assert limpar_valor_excel("n/a") is None
    
    assert limpar_email("  TESTE@Escola.com.br  ") == "teste@escola.com.br"
    assert limpar_email("None") is None
    assert limpar_email("n/a") is None
    
    assert limpar_nome("None") == ""
    assert limpar_nome("  Fulano  ") == "Fulano"


def test_processar_excel_alunos_duplicados(db_session):
    """Testa se processar_excel_alunos atualiza duplicados (RA/Email) sem falhar com IntegrityError."""
    import pandas as pd
    from app import processar_excel_alunos
    from database import Aluno
    
    # Cria aluno pré-existente
    aluno_existente = Aluno(nome="Aluno Antigo", ra="111111", email="antigo@escola.com.br", ano="9º Ano A", viagem_destino="MG")
    db_session.add(aluno_existente)
    db_session.commit()
    
    # DataFrame com:
    # 1. Aluno válido novo
    # 2. Aluno com RA duplicado em relação ao banco (atualiza)
    # 3. Aluno com Email duplicado em relação ao banco (atualiza)
    # 4. Aluno com Email duplicado dentro do próprio arquivo (atualiza)
    data = {
        "nome": ["Aluno Novo", "Aluno RA Duplicado", "Aluno Email Duplicado", "Aluno Interno Duplicado"],
        "ra": ["222222", "111111", "333333", "444444"],
        "email": ["novo@escola.com.br", "diferente1@escola.com.br", "antigo@escola.com.br", "novo@escola.com.br"],
        "ano": ["9º Ano B", "9º Ano A", "9º Ano B", "9º Ano C"],
        "viagem_destino": ["MG", "MG", "MG", "MG"],
        "onibus": ["Ônibus 1", "Ônibus 1", "Ônibus 1", "Ônibus 1"]
    }
    df = pd.DataFrame(data)
    
    # Processa
    count, duplicates_skipped = processar_excel_alunos(df, db_session)
    
    # Todos os 4 devem ser processados (inseridos ou atualizados)
    assert count == 4
    assert duplicates_skipped == 0
    
    # Verifica no banco
    alunos = db_session.query(Aluno).all()
    # Total de alunos deve ser 2 (o pré-existente + o novo válido, ambos atualizados)
    assert len(alunos) == 2
    
    nomes = [a.nome for a in alunos]
    assert "Aluno Email Duplicado" in nomes
    assert "Aluno Interno Duplicado" in nomes
    assert "Aluno Antigo" not in nomes


def test_processar_excel_professores_duplicados(db_session):
    """Testa se processar_excel_professores atualiza duplicados sem falhar."""
    import pandas as pd
    from app import processar_excel_professores
    from database import Professor
    
    # Cria professor pré-existente
    prof_existente = Professor(nome="Prof Antigo", email="antigo.prof@escola.com.br", viagem="MG")
    db_session.add(prof_existente)
    db_session.commit()
    
    # DataFrame com:
    # 1. Professor válido novo
    # 2. Professor com Email duplicado em relação ao banco (atualiza)
    # 3. Professor com Email duplicado dentro do próprio arquivo (atualiza)
    data = {
        "nome": ["Prof Novo", "Prof Duplicado Banco", "Prof Duplicado Interno"],
        "email": ["novo.prof@escola.com.br", "antigo.prof@escola.com.br", "novo.prof@escola.com.br"],
        "viagem": ["MG", "MG", "MG"],
        "onibus": ["Ônibus 1", "Ônibus 1", "Ônibus 1"]
    }
    df = pd.DataFrame(data)
    
    # Processa
    count, duplicates_skipped = processar_excel_professores(df, db_session)
    
    # Todos os 3 devem ser processados (inseridos ou atualizados)
    assert count == 3
    assert duplicates_skipped == 0
    
    # Verifica no banco
    profs = db_session.query(Professor).all()
    assert len(profs) == 2
    
    nomes = [p.nome for p in profs]
    assert "Prof Duplicado Banco" in nomes
    assert "Prof Duplicado Interno" in nomes


def test_normalizar_coluna_helper():
    """Testa a normalização de nomes de colunas do Excel, incluindo acentuação e sinônimos."""
    from app import normalizar_coluna
    
    # Básicos e acentos
    assert normalizar_coluna("Nome") == "nome"
    assert normalizar_coluna("E-mail") == "email"
    assert normalizar_coluna("email") == "email"
    assert normalizar_coluna("Ônibus") == "onibus"
    assert normalizar_coluna("ônibus") == "onibus"
    assert normalizar_coluna("ONIBUS") == "onibus"
    
    # Sinônimos
    assert normalizar_coluna("Destino") == "viagem_destino"
    assert normalizar_coluna("viagem_destino") == "viagem_destino"
    assert normalizar_coluna("Turma") == "ano"
    assert normalizar_coluna("Série") == "ano"
    assert normalizar_coluna("Classe") == "ano"


def test_processar_excel_alunos_sem_coluna_onibus(db_session):
    """Testa que a importação de alunos sem a coluna 'ônibus' preserva os ônibus já cadastrados no banco."""
    import pandas as pd
    from app import processar_excel_alunos
    from database import Aluno
    
    # Cria aluno pré-existente com ônibus
    aluno_existente = Aluno(
        nome="Aluno Antigo",
        ra="111111",
        email="antigo@escola.com.br",
        ano="9º Ano A",
        viagem_destino="MG",
        onibus="Ônibus Original"
    )
    db_session.add(aluno_existente)
    db_session.commit()
    
    # DataFrame sem a coluna 'onibus'
    data = {
        "nome": ["Aluno Antigo"],
        "ra": ["111111"],
        "email": ["antigo@escola.com.br"],
        "ano": ["9º Ano A"],
        "viagem_destino": ["MG"]
    }
    df = pd.DataFrame(data)
    
    count, duplicates_skipped = processar_excel_alunos(df, db_session)
    assert count == 1
    assert duplicates_skipped == 0
    
    # Verifica que o ônibus original NÃO foi apagado/sobrescrito
    aluno_db = db_session.query(Aluno).filter(Aluno.ra == "111111").first()
    assert aluno_db.onibus == "Ônibus Original"


def test_processar_excel_professores_sem_coluna_onibus(db_session):
    """Testa que a importação de professores sem a coluna 'ônibus' preserva os ônibus já cadastrados no banco."""
    import pandas as pd
    from app import processar_excel_professores
    from database import Professor
    
    # Cria professor pré-existente com ônibus
    prof_existente = Professor(
        nome="Prof Antigo",
        email="antigo.prof@escola.com.br",
        viagem="MG",
        onibus="Ônibus Original"
    )
    db_session.add(prof_existente)
    db_session.commit()
    
    # DataFrame sem a coluna 'onibus'
    data = {
        "nome": ["Prof Antigo"],
        "email": ["antigo.prof@escola.com.br"],
        "viagem": ["MG"]
    }
    df = pd.DataFrame(data)
    
    count, duplicates_skipped = processar_excel_professores(df, db_session)
    assert count == 1
    assert duplicates_skipped == 0
    
    # Verifica que o ônibus original NÃO foi apagado/sobrescrito
    prof_db = db_session.query(Professor).filter(Professor.email == "antigo.prof@escola.com.br").first()
    assert prof_db.onibus == "Ônibus Original"


