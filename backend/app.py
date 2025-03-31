from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
import requests
import os

# Defina basedir ANTES de usar
basedir = os.path.abspath(os.path.dirname(__file__))

# Cria a pasta instance se não existir - AGORA COM basedir DEFINIDO
if not os.path.exists(os.path.join(basedir, 'instance')):
    os.makedirs(os.path.join(basedir, 'instance'))

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuração do banco de dados (usando basedir que já está definido)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance/idosos.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Idoso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    nome_responsavel = db.Column(db.String(100), nullable=False)
    celular_responsavel = db.Column(db.String(15), nullable=False)
    cep = db.Column(db.String(9), nullable=False)
    logradouro = db.Column(db.String(100))
    numero = db.Column(db.String(10))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    uf = db.Column(db.String(2))

# Cria o banco de dados
db_path = Path("idosos.db")
if db_path.exists():
    db_path.unlink()  # Remove o arquivo vazio

# Criação do banco de dados
with app.app_context():
    db.create_all()
    db_path = os.path.join(basedir, 'instance/idosos.db')
    if os.path.exists(db_path):
        print(f"Banco criado em: {db_path}")
    else:
        print("Banco de dados não foi criado!")

# Adicione esta rota temporária para teste
@app.route('/teste')
def teste():
    return jsonify({"status": "API operacional", "banco": "Conectado"})

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "API está funcionando", "rotas": {
        "cadastrar_idoso": "POST /idosos",
        "buscar_cep": "GET /cep/<cep>",
        "listar_idosos": "GET /idosos"
    }})

@app.route('/caminho_banco')
def mostra_caminho():
    return jsonify({
        "caminho_absoluto": os.path.abspath('instance/idosos.db'),
        "existe": os.path.exists('instance/idosos.db')
    })

@app.route('/idosos/<int:id>', methods=['DELETE'])
def deletar_idoso(id):
    try:
        idoso = db.session.get(Idoso, id)
        if not idoso:
            return jsonify({"erro": "Idoso não encontrado"}), 404

        db.session.delete(idoso)
        db.session.commit()
        return jsonify({"mensagem": "Idoso deletado com sucesso!"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500

@app.route('/idosos', methods=['POST'])
def cadastrar_idoso():
    try:
        dados = request.json
        print("Dados recebidos no backend:", dados)
        
        # Validação
        campos_obrigatorios = ['nome', 'idade', 'nome_responsavel', 'celular_responsavel', 'cep']
        if not all(campo in dados for campo in campos_obrigatorios):
            return jsonify({"erro": "Campos obrigatórios faltando"}), 400

        novo_idoso = Idoso(
            nome=dados['nome'],
            idade=dados['idade'],
            nome_responsavel=dados['nome_responsavel'],
            celular_responsavel=dados['celular_responsavel'],
            cep=dados['cep'],
            logradouro=dados.get('logradouro', ''),
            numero=dados.get('numero', ''),
            bairro=dados.get('bairro', ''),
            cidade=dados.get('cidade', ''),
            uf=dados.get('uf', '')
        )

        db.session.add(novo_idoso)
        db.session.commit()

        idoso_salvo = db.session.get(Idoso, novo_idoso.id)
        print("Dados salvos no banco:", {
            "logradouro": idoso_salvo.numero,
            "numero": idoso_salvo.logradouro,
            "bairro": idoso_salvo.bairro,
            "cidade": idoso_salvo.cidade,
            "uf": idoso_salvo.uf
        })

        return jsonify({"mensagem": "Idoso cadastrado com sucesso!", "id": novo_idoso.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500

@app.route('/cep/<cep>', methods=['GET'])
def buscar_endereco(cep):
    try:
        response = requests.get(f'https://viacep.com.br/ws/{cep}/json/')
        
        if response.status_code != 200 or 'erro' in response.json():
            return jsonify({"erro": "CEP não encontrado"}), 404

        endereco = response.json()
        return jsonify({
            "logradouro": endereco.get('logradouro', ''),
            "numero": endereco.get('numero', ''),
            "bairro": endereco.get('bairro', ''),
            "cidade": endereco.get('localidade', ''),
            "uf": endereco.get('uf', ''),
            "cep": endereco.get('cep', '')
        })

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/idosos', methods=['GET'])
def listar_idosos():
    try:
        idosos = Idoso.query.all()
        return jsonify([{
            "id": idoso.id,
            "nome": idoso.nome,
            "idade": idoso.idade,
            "nome_responsavel": idoso.nome_responsavel,
            "celular_responsavel": idoso.celular_responsavel,
            "cep": idoso.cep,
            "logradouro": idoso.logradouro,
            "numero": idoso.numero,
            "bairro": idoso.bairro,
            "cidade": idoso.cidade,
            "uf": idoso.uf
        } for idoso in idosos])
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    

@app.route('/idosos/<int:id>', methods=['DELETE'])
def deletar_idoso(id):
    try:
        idoso = db.session.get(Idoso, id)
        if not idoso:
            return jsonify({"erro": "Idoso não encontrado"}), 404

        db.session.delete(idoso)
        db.session.commit()
        return jsonify({"mensagem": "Idoso deletado com sucesso!"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)