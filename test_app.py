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


def test_processar_excel_colunas_sinonimos(db_session):
    """Testa se os sinônimos de coluna ('destino', 'viagem_destino', 'viagem') são normalizados/renomeados corretamente."""
    import pandas as pd
    from app import processar_excel_professores, processar_excel_alunos
    from database import Professor, Aluno
    
    # 1. Professores com coluna "destino" e "viagem_destino"
    data_prof_destino = {
        "nome": ["Prof Destino"],
        "email": ["prof.destino@escola.com.br"],
        "Destino": ["MG"]
    }
    df_prof_destino = pd.DataFrame(data_prof_destino)
    count, dup = processar_excel_professores(df_prof_destino, db_session)
    assert count == 1
    p_db = db_session.query(Professor).filter(Professor.email == "prof.destino@escola.com.br").first()
    assert p_db is not None
    assert p_db.viagem == "MG"

    data_prof_viagem_destino = {
        "nome": ["Prof Viagem Destino"],
        "email": ["prof.vdestino@escola.com.br"],
        "viagem_destino": ["RJ"]
    }
    df_prof_viagem_destino = pd.DataFrame(data_prof_viagem_destino)
    count, dup = processar_excel_professores(df_prof_viagem_destino, db_session)
    assert count == 1
    p_db2 = db_session.query(Professor).filter(Professor.email == "prof.vdestino@escola.com.br").first()
    assert p_db2 is not None
    assert p_db2.viagem == "RJ"

    # 2. Alunos com coluna "destino" e "viagem"
    data_aluno_destino = {
        "nome": ["Aluno Destino"],
        "ra": ["111222"],
        "email": ["aluno.destino@escola.com.br"],
        "ano": ["9º Ano A"],
        "Destino": ["MG"]
    }
    df_aluno_destino = pd.DataFrame(data_aluno_destino)
    count, dup = processar_excel_alunos(df_aluno_destino, db_session)
    assert count == 1
    a_db = db_session.query(Aluno).filter(Aluno.ra == "111222").first()
    assert a_db is not None
    assert a_db.viagem_destino == "MG"

    data_aluno_viagem = {
        "nome": ["Aluno Viagem"],
        "ra": ["222333"],
        "email": ["aluno.viagem@escola.com.br"],
        "ano": ["9º Ano B"],
        "viagem": ["RJ"]
    }
    df_aluno_viagem = pd.DataFrame(data_aluno_viagem)
    count, dup = processar_excel_alunos(df_aluno_viagem, db_session)
    assert count == 1
    a_db2 = db_session.query(Aluno).filter(Aluno.ra == "222333").first()
    assert a_db2 is not None
    assert a_db2.viagem_destino == "RJ"


def test_obter_rubrica_por_ano():
    """Testa se a função obter_rubrica_por_ano normaliza e mapeia corretamente as séries."""
    from app import obter_rubrica_por_ano, RUBRICAS

    # Verificar que as rubricas possuem os limites corretos
    assert RUBRICAS["2ª série"]["max_aa"] == 1.0
    assert RUBRICAS["2ª série"]["max_cs"] == 1.0
    assert RUBRICAS["3ª série"]["max_aa"] == 0.4
    assert RUBRICAS["3ª série"]["max_cs"] == 1.6
    assert RUBRICAS["Geral"]["max_aa"] == 1.0
    assert RUBRICAS["Geral"]["max_cs"] == 1.0

    # Deve mapear para a rubrica da 2ª série (Vale do Paraíba)
    assert obter_rubrica_por_ano("2ª série") == RUBRICAS["2ª série"]
    assert obter_rubrica_por_ano("2ª SERIE") == RUBRICAS["2ª série"]
    assert obter_rubrica_por_ano("2 SÉRIE") == RUBRICAS["2ª série"]
    assert obter_rubrica_por_ano("2EM") == RUBRICAS["2ª série"]
    assert obter_rubrica_por_ano("2º EM") == RUBRICAS["2ª série"]
    assert obter_rubrica_por_ano("2ºEM") == RUBRICAS["2ª série"]

    # Deve mapear 3ª série para a rubrica da 3ª série (Brasília)
    assert obter_rubrica_por_ano("3ª série") == RUBRICAS["3ª série"]
    assert obter_rubrica_por_ano("3ª SERIE") == RUBRICAS["3ª série"]
    assert obter_rubrica_por_ano("3 SÉRIE") == RUBRICAS["3ª série"]
    assert obter_rubrica_por_ano("3EM") == RUBRICAS["3ª série"]
    assert obter_rubrica_por_ano("3º EM") == RUBRICAS["3ª série"]
    assert obter_rubrica_por_ano("3ºEM") == RUBRICAS["3ª série"]
    assert obter_rubrica_por_ano("3 ano") == RUBRICAS["3ª série"]
    assert obter_rubrica_por_ano("3º Ano") == RUBRICAS["3ª série"]

    # Deve cair na rubrica Geral (fallback)
    assert obter_rubrica_por_ano("9º Ano A") == RUBRICAS["Geral"]
    assert obter_rubrica_por_ano("8º Ano B") == RUBRICAS["Geral"]
    assert obter_rubrica_por_ano(None) == RUBRICAS["Geral"]
    assert obter_rubrica_por_ano("") == RUBRICAS["Geral"]


def test_rubrica_database_crud(db_session):
    """Testa o CRUD de rubricas e critérios no banco de dados de teste."""
    from database import Rubrica, CriterioRubrica
    
    # 1. Create a Rubrica
    nova_r = Rubrica(
        nome="1ª série - Teste",
        max_aa=2.0,
        max_cs=3.0,
        termos_mapeamento="1ª SÉRIE; 1ª SERIE; 1EM"
    )
    db_session.add(nova_r)
    db_session.commit()
    
    # Verify creation
    r_db = db_session.query(Rubrica).filter(Rubrica.nome == "1ª série - Teste").first()
    assert r_db is not None
    assert r_db.max_aa == 2.0
    assert r_db.max_cs == 3.0
    assert r_db.termos_mapeamento == "1ª SÉRIE; 1ª SERIE; 1EM"
    
    # 2. Add Criteria
    crit1 = CriterioRubrica(rubrica_id=r_db.id, tipo="AA", descricao="Falta de foco", desconto_padrao=0.5)
    crit2 = CriterioRubrica(rubrica_id=r_db.id, tipo="CS", descricao="Conversa excessiva", desconto_padrao=0.25)
    db_session.add_all([crit1, crit2])
    db_session.commit()
    
    # Verify criteria
    criterios = db_session.query(CriterioRubrica).filter(CriterioRubrica.rubrica_id == r_db.id).all()
    assert len(criterios) == 2
    types = [c.tipo for c in criterios]
    assert "AA" in types
    assert "CS" in types
    
    # 3. Update
    r_db.max_aa = 1.5
    crit1.desconto_padrao = 0.4
    db_session.commit()
    
    # Verify update
    r_db_updated = db_session.query(Rubrica).filter(Rubrica.nome == "1ª série - Teste").first()
    assert r_db_updated.max_aa == 1.5
    crit1_db = db_session.query(CriterioRubrica).filter(CriterioRubrica.descricao == "Falta de foco").first()
    assert crit1_db.desconto_padrao == 0.4
    
    # 4. Delete
    db_session.delete(r_db_updated)
    db_session.commit()
    
    # Verify cascading delete of criteria
    assert db_session.query(Rubrica).filter(Rubrica.nome == "1ª série - Teste").first() is None
    assert db_session.query(CriterioRubrica).filter(CriterioRubrica.rubrica_id == r_db.id).first() is None




