import openai
import os
from flask import Flask, render_template, request, redirect, session
import database as db
import json
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import TfidfTransformer

openai.api_key = "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"
openai.organization = "org-OB4THAkEBAWQWhxKZhodli7j"


app = Flask(__name__, static_folder='static')
app.secret_key = '1234'

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
    conn = db.create_connection()

    # Obtener el usuario de la base de datos
    user = db.get_user(conn, username, password)
    print(user)

    if user:
        # Redirigir al chatbot del usuario existente
        conversation_id = user['id']
        session['user_id'] = conversation_id
        conn.close()
        return redirect('/chat')
    else:
        error_message_i = "El usuario no existe. Comprueba los credenciales."
        return render_template('inicio.html', error_message_i=error_message_i)
    
@app.route('/create', methods=['POST'])
def create():
    username = request.form['username_new']
    password = request.form['password_new']

    # Crear conexión con la base de datos
    conn = db.create_connection()

    # Obtener el usuario de la base de datos
    name = db.user_ava(conn,username)
    print(name)
    if name:
        # Redirigir al index ya que el usuario ya esta creado
        error_message = "El usuario ya existe. Por favor, elige otro nombre de usuario."
        return render_template('inicio.html', error_message=error_message)
    else:
        # Crear un nuevo usuario en la base de datos
        db.insert_user(conn, username, password, '')
        user = db.get_user(conn, username, password)
        conversation_id = user['id']
        session['user_id'] = conversation_id
        conn.close()
        return redirect('/chat')

@app.route('/appointment.html')
def appointment():
    return render_template('appointment.html')

@app.route('/guardar_datos', methods=['POST'])
def guardar_datos():
    conn = db.create_connection()
    conversation_id = session.get('user_id')
    lugar = request.form.get('lugar')
    fecha = request.form.get('hora')
    print("Parametros: ", conversation_id, fecha, lugar)
    db.insert_appointment(conn, conversation_id, fecha, lugar)
    return "Datos guardados"

@app.route('/history.html')
def history():
    return render_template('history.html')

@app.route('/guardar_historial', methods=['POST'])
def guardar_historial():
    conn = db.create_connection()
    conversation_id = session.get('user_id')
    text = request.form.get('text')
    print("Parametros: ", conversation_id, text)
    db.insert_history(conn, conversation_id, text)
    return "Datos guardados"

@app.route('/reminders.html')
def reminders():
    return render_template('reminders.html')

@app.route('/guardar_recordatorio', methods=['POST'])
def guardar_recordatorio():
    conn = db.create_connection()
    conversation_id = session.get('user_id')
    name = request.form.get('name')
    fecha = request.form.get('fecha')
    frecuencia = request.form.get('frecuencia')
    print("Parametros: ", conversation_id, name, fecha, frecuencia)
    db.insert_reminders(conn, conversation_id, name, fecha, frecuencia)
    return "Datos guardados"

@app.route('/citas', methods=['GET'])
def citas():
    conn = db.create_connection()
    conversation_id = session.get('user_id')
    appo = db.get_user_appointments(conn, conversation_id)
    string ="<br><strong>Citas</strong><br>"
    for cad in appo:
        fecha = str(cad['date']).split("T") 
        print(str(fecha))
        string += "Dia: " + str(fecha[0]) + " Hora: " + str(fecha[1]) +"<br>"
        string += "Lugar: " + str(cad['place']) + "<br>"
        string += "<br>"
    print("APOINTEMENT" , appo)
    return string

@app.route('/recordatorios', methods=['GET'])
def recordatorios():
    conn = db.create_connection()
    conversation_id = session.get('user_id')
    remin = db.get_user_reminders(conn, conversation_id)
    print(remin)
    string ="<br><strong>Recordatorios</strong><br>"
    for cad in remin:
        fecha = str(cad['date']).split("T") 
        print(str(fecha))
        string += "Nombre: " + str(cad['name']) + "<br>"
        string += "Dia: " + str(fecha[0]) + " Hora: " + str(fecha[1]) +"<br>"
        string += "Frecuencia: " + str(cad['frecuency']) + "<br>"
        string += "<br>"
    return string

@app.route('/historial', methods=['GET'])
def historial():
    conn = db.create_connection()
    conversation_id = session.get('user_id')
    his = db.get_user_history(conn, conversation_id)
    string ="<br><strong>Historial Médico</strong><br>"
    for cad in his:
        string += "Entrada: " + str(cad['text']) + "<br>"
        string += "<br>"
    return string

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    conversation_id = session.get('user_id')
    if request.method == 'POST':
        print(request.form)
        question = request.form['question']
        conversation_text = request.form['conversation']

        # Obtener el usuario de la base de datos
        conn = db.create_connection()
        user = db.get_user_id(conn, conversation_id)
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
            db.update_conversation(conn, conversation_id, conversation_text)

            conn.close()

        return {
            'conversation': conversation_text,
            'id' : conversation_id
        }

    else:
        return render_template('index.html', conversation_id = conversation_id)

if __name__ == '__main__':
    # Crear conexión con la base de datos
    conn = db.create_connection()

    # Crear tabla de usuarios
    db.create_table(conn)

    # Iniciar la aplicación Flask
    app.run(debug=True)

    # Cerrar la conexión con la base de datos
    conn.close()