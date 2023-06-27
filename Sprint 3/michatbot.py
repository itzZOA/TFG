import openai
import os
from flask import Flask, render_template, request, redirect
from database import create_connection, create_table, insert_user, get_user, update_conversation, get_user_id, user_ava
import json
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import TfidfTransformer

openai.api_key = "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"
openai.organization = "org-OB4THAkEBAWQWhxKZhodli7j"

app = Flask(__name__, static_folder='static')

conversation = []  # Definimos conversation como una lista vacía

# Obtén la ruta absoluta del directorio actual
dir_path = os.path.dirname(os.path.realpath(__file__))

# Construye la ruta completa al archivo 'entrenamiento.json'
file_path = os.path.join(dir_path, 'data/entrenamiento.json')

# Lee el archivo JSON
with open(file_path, 'r') as file:
    data = json.load(file)

# Obtener las preguntas y respuestas
examples = data['examples']
preguntas = [example['question'] for example in examples]
respuestas = [example['answer'] for example in examples]

# Preprocesamiento de texto
stop_words = set(stopwords.words('spanish'))

def preprocess_text(text):
    tokens = word_tokenize(text.lower())
    filtered_tokens = [token for token in tokens if token.isalnum() and token not in stop_words]
    return ' '.join(filtered_tokens)

preguntas_preprocesadas = [preprocess_text(pregunta) for pregunta in preguntas]

vectorizer = TfidfVectorizer()
X_train = vectorizer.fit_transform(preguntas_preprocesadas)
transformer = TfidfTransformer()
X_train_transformed = transformer.fit_transform(X_train)

@app.route('/')
def home():
    return render_template('inicio.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Crear conexión con la base de datos
    conn = create_connection()

    # Obtener el usuario de la base de datos
    user = get_user(conn, username, password)
    print(user)

    if user:
        # Redirigir al chatbot del usuario existente
        conversation_id = user['id']
        conn.close()
        return redirect('/chat/' + str(conversation_id))
    else:
        error_message_i = "El usuario no existe. Comprueba los credenciales."
        return render_template('inicio.html', error_message_i=error_message_i)
    
@app.route('/create', methods=['POST'])
def create():
    username = request.form['username_new']
    password = request.form['password_new']

    # Crear conexión con la base de datos
    conn = create_connection()

    # Obtener el usuario de la base de datos
    name = user_ava(conn,username)
    print(name)
    if name:
        # Redirigir al index ya que el usuario ya esta creado
        error_message = "El usuario ya existe. Por favor, elige otro nombre de usuario."
        return render_template('inicio.html', error_message=error_message)
    else:
        # Crear un nuevo usuario en la base de datos
        insert_user(conn, username, password, '')
        user = get_user(conn, username, password)
        conversation_id = user['id']
        conn.close()
        return redirect('/chat/'+ str(conversation_id))
    
@app.route('/chat/<conversation_id>', methods=['GET', 'POST'])
def chat(conversation_id):
    print(conversation_id)
    if request.method == 'POST':
        print(request.form)
        question = request.form['question']
        conversation_text = request.form['conversation']

        # Obtener el usuario de la base de datos
        conn = create_connection()
        user = get_user_id(conn, conversation_id)
        print(user)

        if user:
            conversation_text += "<br><strong>Human:</strong> " + question + "<br><br><strong>AI:</strong>"
            question_preprocesada = preprocess_text(question)

            # Calcular la similitud de coseno entre la pregunta del usuario y las preguntas almacenadas
            question_vector = vectorizer.transform([question_preprocesada])
            question_vector_transformed = transformer.transform(question_vector)
            similarities = cosine_similarity(question_vector_transformed, X_train_transformed)[0]
            max_similarity = max(similarities)
            index = similarities.tolist().index(max_similarity)

            # Obtener la respuesta correspondiente a la pregunta con mayor similitud
            if max_similarity > 0.6:
                answer = respuestas[index]
            else:
                response = openai.Completion.create(
                    model="text-davinci-003",
                    prompt=conversation_text,
                    temperature=0.9,
                    max_tokens=150,
                    top_p=1,
                    frequency_penalty=0.0,
                    presence_penalty=0.6,
                    stop=[" Human:", " AI:"]
                )
                answer = response.choices[0].text.strip()

            conversation_text += answer + "<br>"

            # Actualizar la conversación del usuario en la base de datos
            update_conversation(conn, conversation_id, conversation_text)

            conn.close()

        return {
            'conversation': conversation_text,
            'id' : conversation_id
        }

    else:
        return render_template('index.html', conversation_id = conversation_id)

if __name__ == '__main__':
    # Crear conexión con la base de datos
    conn = create_connection()

    # Crear tabla de usuarios
    create_table(conn)

    # Iniciar la aplicación Flask
    app.run(debug=True)

    # Cerrar la conexión con la base de datos
    conn.close()