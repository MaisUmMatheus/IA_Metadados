from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import google.generativeai as genai
import json
import pandas as pd
import sqlite3
import xml.etree.ElementTree as ET

app = Flask(__name__)
CORS(app)
genai.configure(api_key='AIzaSyDgaiDqmjd4aScETKWkChUjz8XsL7AlFKU')

# Conectar ao banco de dados SQLite
def init_db():
    conn = sqlite3.connect('db_dados.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metadado (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TIMESTAMP,
            nomeArquivo TEXT,
            formatoArquivo TEXT,
            colunas TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_metadado INTEGER,
            nomeColuna TEXT,
            tipoDado TEXT,
            valor TEXT,
            FOREIGN KEY (id_metadado) REFERENCES metadado(id)
        )
    ''')
    conn.commit()
    conn.close()


def classificar_conteudo_arquivo(conteudo):
    try:
        model = genai.GenerativeModel('gemini-1.0-pro')
        prompt = f"Classifique o coteudo do arquivo e o que vc acha que são: '{conteudo[:500]}...'"

        response = model.generate_content(prompt)
        print(f"Resposta completa da API: {response}")

        if response and hasattr(response, 'candidates') and len(response.candidates) > 0:
            content = response.candidates[0].content
            categoria = content.parts[0].text if content.parts else "Não foi possível classificar o conteúdo."
        else:
            categoria = "Não foi possível classificar o conteúdo."

        return categoria
    except Exception as e:
        return f"Erro ao classificar o conteúdo: {str(e)}"


@app.route('/classificar', methods=['POST'])
def api_classificar():
    if 'file' not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado na requisição."}), 400

    file = request.files['file']
    format_type = file.filename.split('.')[-1]

    # Processamento do arquivo conforme o tipo
    try:
        if format_type == 'csv':
            data = pd.read_csv(file)
        elif format_type == 'json':
            data = pd.DataFrame(json.load(file))
        elif format_type == 'xml':
            tree = ET.parse(file)
            root = tree.getroot()
            all_records = []

            for record in root:
                record_data = {}
                for item in record:
                    record_data[item.tag] = item.text
                all_records.append(record_data)

            data = pd.DataFrame(all_records)
        elif format_type == 'txt':
            data = pd.read_csv(file, delimiter="\t")
        else:
            return jsonify({"erro": "Formato de arquivo não suportado."}), 400
    except Exception as e:
        return jsonify({"erro": f"Erro ao processar o arquivo: {str(e)}"}), 400

    # Classificar o conteúdo do arquivo
    conteudo = data.to_string()
    categoria = classificar_conteudo_arquivo(conteudo)

    return jsonify({"categoria": categoria})

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    format_type = file.filename.split('.')[-1]

    # Processamento do arquivo conforme o tipo
    if format_type == 'csv':
        data = pd.read_csv(file)
    elif format_type == 'json':
        data = pd.DataFrame(json.load(file))
    elif format_type == 'xml':
        try:
            # Usar o ElementTree para parsear o XML e converter para DataFrame
            tree = ET.parse(file)
            root = tree.getroot()
            all_records = []

            # Assumindo que cada sub-elemento de "root" representa um registro
            for record in root:
                record_data = {}
                for item in record:
                    record_data[item.tag] = item.text
                all_records.append(record_data)

            data = pd.DataFrame(all_records)
        except ET.ParseError as e:
            return jsonify({"error": f"Erro ao processar o arquivo XML: {str(e)}"}), 400
    elif format_type == 'txt':
        data = pd.read_csv(file, delimiter="\t")
    else:
        return jsonify({"error": "Formato de arquivo não suportado"}), 400

    # Verificar se o arquivo já foi processado anteriormente
    conn = sqlite3.connect('db_dados.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM metadado WHERE nomeArquivo = ? AND formatoArquivo = ?
    ''', (file.filename, format_type))
    metadado_existente = cursor.fetchone()

    if metadado_existente:
        conn.close()
        return jsonify({"message": "O arquivo já foi enviado anteriormente."}), 409

    # Salvar metadados se não for duplicado
    colunas = ', '.join(data.columns)
    metadado = {
        "data": datetime.now(),
        "nomeArquivo": file.filename,
        "formatoArquivo": format_type,
        "colunas": colunas
    }

    cursor.execute('''
        INSERT INTO metadado (data, nomeArquivo, formatoArquivo, colunas)
        VALUES (?, ?, ?, ?)
    ''', (metadado["data"], metadado["nomeArquivo"], metadado["formatoArquivo"], metadado["colunas"]))
    metadado_id = cursor.lastrowid

    # Salvar dados associados ao metadado
    for _, row in data.iterrows():
        for col in data.columns:
            cursor.execute('''
                INSERT INTO dados (id_metadado, nomeColuna, tipoDado, valor)
                VALUES (?, ?, ?, ?)
            ''', (metadado_id, col, str(type(row[col]).__name__), str(row[col])))

    conn.commit()
    conn.close()

    return jsonify({"message": "Arquivo enviado e processado com sucesso"}), 200

@app.route('/metadados', methods=['GET'])
def get_metadados():
    conn = sqlite3.connect('db_dados.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM metadado')
    metadados = cursor.fetchall()
    conn.close()
    return jsonify(metadados)

@app.route('/dados/<int:metadado_id>', methods=['GET'])
def get_dados(metadado_id):
    conn = sqlite3.connect('db_dados.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dados WHERE id_metadado = ?', (metadado_id,))
    dados = cursor.fetchall()
    conn.close()
    return jsonify(dados)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
