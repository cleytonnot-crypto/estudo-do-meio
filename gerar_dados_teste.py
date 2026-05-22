import pandas as pd
import sqlite3
import os

def main():
    # 1. Dados de Professores para a Planilha Excel
    professores_data = [
        {"nome": "Cleyton Alves", "email": "cleyton.alves@escola.com.br", "viagem": "MG", "onibus": "Ônibus 1"},
        {"nome": "Mariana Costa", "email": "mariana.costa@escola.com.br", "viagem": "RJ", "onibus": "Ônibus 2"},
        {"nome": "Roberto Dias", "email": "roberto.dias@escola.com.br", "viagem": "BSB", "onibus": "Ônibus 3"},
        {"nome": "Luciana Silva", "email": "luciana.silva@escola.com.br", "viagem": "MG", "onibus": "Ônibus 2"},
        {"nome": "Renato Souza", "email": "renato.souza@escola.com.br", "viagem": "RJ", "onibus": "Ônibus 1"}
    ]
    df_prof = pd.DataFrame(professores_data)
    prof_file = "dados_teste_professores.xlsx"
    df_prof.to_excel(prof_file, index=False)
    print(f"Planilha de professores gerada: '{prof_file}'")

    # 2. Dados de Alunos para a Planilha Excel
    alunos_data = [
        {"nome": "Bruno Gomes", "ra": "202401", "email": "bruno.gomes@escola.com.br", "ano": "9º Ano A", "viagem_destino": "MG", "onibus": "Ônibus 1"},
        {"nome": "Camila Rocha", "ra": "202402", "email": "camila.rocha@escola.com.br", "ano": "9º Ano A", "viagem_destino": "MG", "onibus": "Ônibus 1"},
        {"nome": "Daniel Lima", "ra": "202403", "email": "daniel.lima@escola.com.br", "ano": "9º Ano B", "viagem_destino": "RJ", "onibus": "Ônibus 2"},
        {"nome": "Eduardo Souza", "ra": "202404", "email": "eduardo.souza@escola.com.br", "ano": "9º Ano B", "viagem_destino": "RJ", "onibus": "Ônibus 2"},
        {"nome": "Fernanda Dias", "ra": "202405", "email": "fernanda.dias@escola.com.br", "ano": "9º Ano A", "viagem_destino": "BSB", "onibus": "Ônibus 3"},
        {"nome": "Gabriel Silva", "ra": "202406", "email": "gabriel.silva@escola.com.br", "ano": "9º Ano A", "viagem_destino": "BSB", "onibus": "Ônibus 3"},
        {"nome": "Helena Santos", "ra": "202407", "email": "helena.santos@escola.com.br", "ano": "9º Ano B", "viagem_destino": "MG", "onibus": "Ônibus 2"},
        {"nome": "Igor Martins", "ra": "202408", "email": "igor.martins@escola.com.br", "ano": "9º Ano B", "viagem_destino": "MG", "onibus": "Ônibus 1"},
        {"nome": "Julia Ribeiro", "ra": "202409", "email": "julia.ribeiro@escola.com.br", "ano": "9º Ano A", "viagem_destino": "RJ", "onibus": "Ônibus 2"},
        {"nome": "Kevin Oliveira", "ra": "202410", "email": "kevin.oliveira@escola.com.br", "ano": "9º Ano A", "viagem_destino": "BSB", "onibus": "Ônibus 3"}
    ]
    df_aluno = pd.DataFrame(alunos_data)
    aluno_file = "dados_teste_alunos.xlsx"
    df_aluno.to_excel(aluno_file, index=False)
    print(f"Planilha de alunos gerada: '{aluno_file}'")

    print("\nPronto! Você pode usar esses arquivos Excel para fazer o upload na aba 'Administração' do aplicativo Streamlit.")
    print("Se quiser limpar os dados posteriormente, acesse a sub-aba 'Limpeza de Dados' na seção 'Administração' do aplicativo.")

if __name__ == "__main__":
    main()
