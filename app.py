# Importações necessárias para o funcionamento do Flask, SQLAlchemy, CORS e autenticação com Flask-Login
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user

# Criação da aplicação Flask
app = Flask(__name__)
# Configurações da chave secreta e banco de dados SQLite
app.config['SECRET_KEY'] = "minha_chave_123"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'

# Configuração do gerenciador de login
login_manager = LoginManager()
login_manager.init_app(app)  # Inicializa o gerenciador de login com a aplicação Flask
login_manager.login_view = 'login'  # Define a rota de login

# Inicia a conexão com o banco de dados usando SQLAlchemy
db = SQLAlchemy(app)
# Ativa o CORS para permitir requisições de diferentes origens
CORS(app)

# Modelagem de dados para o banco de dados
# Definição do modelo User (usuário)
class User(db.Model, UserMixin):
    # Definição das colunas da tabela User
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

    # Relacionamento com a tabela CartItem
    cart = db.relationship('CartItem', backref='user', lazy=True)

# Definição do modelo Product (produto)
class Product(db.Model):
    # Definição das colunas da tabela Product
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)

# Definição do modelo CartItem (item do carrinho)
class CartItem(db.Model):
    # Definição das colunas da tabela CartItem
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)

# Carregamento do usuário a partir do ID para autenticação
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rota para login
@app.route('/login', methods=['POST'])
def login():
    data = request.json  # Obtém os dados da requisição JSON
    user = User.query.filter_by(username=data.get("username")).first()  # Busca o usuário pelo nome de usuário

    # Verifica se o usuário existe e se a senha está correta
    if user and data.get("password") == user.password:
        login_user(user)  # Autentica o usuário
        return jsonify({'message': "Logged in successfully"})
    return jsonify({'message': "Unauthorized. Invalid credentials"}), 401  # Resposta de erro se a autenticação falhar

# Rota para logout
@app.route('/logout', methods=['POST'])
@login_required  # Requer que o usuário esteja autenticado
def logout():
    logout_user()  # Desloga o usuário atual
    return jsonify({'message': "Logout successfully"})

# Rota para adicionar um produto
@app.route('/api/products/add', methods=['POST'])
@login_required
def add_product():
    data = request.json  # Obtém os dados da requisição JSON

    # Verifica se o nome e o preço do produto foram fornecidos
    if 'name' in data and 'price' in data:
        product = Product(name=data['name'], price=data['price'], description=data.get('description', ""))
        db.session.add(product)  # Adiciona o produto ao banco de dados
        db.session.commit()  # Confirma as mudanças
        return jsonify({"message": "Product added successfully"})
    return jsonify({"message": "Invalid product data"}), 400  # Resposta de erro se os dados estiverem inválidos

# Rota para deletar um produto pelo ID
@app.route('/api/products/delete/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    # Recupera o produto do banco de dados
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)  # Remove o produto do banco de dados
        db.session.commit()  # Confirma a remoção
        return jsonify({"message": "Product deleted successfully"})
    return jsonify({"message": "Product not found"}), 404  # Resposta de erro se o produto não for encontrado

# Rota para obter detalhes de um produto pelo ID
@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product_details(product_id):
    product = Product.query.get(product_id)  # Recupera o produto do banco de dados
    if product:
        return jsonify({
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "description": product.description
        })
    return jsonify({"message": "Product not found"}), 404  # Resposta de erro se o produto não for encontrado

# Rota para atualizar detalhes de um produto pelo ID
@app.route('/api/products/update/<int:product_id>', methods=['PUT'])
@login_required
def update_product_details(product_id):
    product = Product.query.get(product_id)  # Recupera o produto do banco de dados
    if not product:
        return jsonify({"message": "Product not found"}), 404

    data = request.json  # Obtém os dados da requisição JSON
    if 'name' in data:
        product.name = data['name']  # Atualiza o nome do produto

    if 'price' in data:
        product.price = data['price']  # Atualiza o preço do produto

    if 'description' in data:
        product.description = data['description']  # Atualiza a descrição do produto

    db.session.commit()  # Confirma as mudanças
    return jsonify({'message': 'Product updated successfully'})

# Rota para listar todos os produtos
@app.route('/api/products/', methods=['GET'])
def get_products():
    products = Product.query.all()  # Recupera todos os produtos do banco de dados
    product_list = []  # Lista para armazenar os produtos
    for product in products:
        product_data = {
            "id": product.id,
            "name": product.name,
            "price": product.price,
        }
        product_list.append(product_data)  # Adiciona cada produto à lista

    return jsonify(product_list)  # Retorna a lista de produtos em formato JSON

# Rota para adicionar um produto ao carrinho pelo ID do produto
@app.route('/api/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    user = User.query.get(int(current_user.id))  # Obtém o usuário autenticado
    product = Product.query.get(product_id)  # Obtém o produto pelo ID

    if user and product:
        cart_item = CartItem(user_id=user.id, product_id=product.id)  # Cria um novo item no carrinho
        db.session.add(cart_item)  # Adiciona o item ao banco de dados
        db.session.commit()  # Confirma a adição
        return jsonify({'message': 'Item added successfully'})
    return jsonify({'message': 'Failed to add item to the cart'}), 400  # Resposta de erro se falhar

# Rota para remover um produto do carrinho pelo ID do produto
@app.route('/api/cart/remove/<int:product_id>', methods=['DELETE'])
@login_required
def remove_from_cart(product_id):
    # Obtém o item do carrinho para o usuário autenticado e o produto especificado
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        db.session.delete(cart_item)  # Remove o item do carrinho
        db.session.commit()  # Confirma a remoção
        return jsonify({'message': 'Item removed from the cart successfully'})
    return jsonify({'message': 'Failed to remove item from the cart'}), 400  # Resposta de erro se falhar

# Rota para visualizar os itens do carrinho do usuário autenticado
@app.route('/api/cart', methods=['GET'])
@login_required
def view_cart():
    user = User.query.get(int(current_user.id))  # Obtém o usuário autenticado
    cart_items = user.cart  # Recupera todos os itens do carrinho do usuário
    cart_content = []  # Lista para armazenar o conteúdo do carrinho
    for cart_item in cart_items:
        product = Product.query.get(cart_item.product_id)  # Obtém o produto correspondente a cada item
        cart_content.append({
            "id": cart_item.id,
            "user_id": cart_item.user_id,
            "product_id": cart_item.product_id,
            "product_name": product.name,
            "product_price": product.price
        })
    return jsonify(cart_content)  # Retorna o conteúdo do carrinho em formato JSON

# Rota para finalizar a compra (checkout) do usuário autenticado
@app.route('/api/cart/checkout', methods=['POST'])
@login_required
def checkout():
    user = User.query.get(current_user.id)  # Obtém o usuário autenticado
    cart_items = user.cart
    for cart_item in cart_items:
        db.session.delete(cart_item)
    db.session.commit()
    return jsonify({'message': 'Checkout sucessfull. Cart has been cleared.'})
