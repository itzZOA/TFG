import openai
import os
from flask import Flask, render_template, request
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

# Cargar el archivo JSON
with open('data/entrenamiento.json', 'r') as file:
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
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    question = request.form['question']
    conversation = request.form['conversation']
    conversation += "<br><strong>Human:</strong> " + question + "<br><br><strong>AI:</strong>"
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
            prompt=conversation,
            temperature=0.9,
            max_tokens=150,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.6,
            stop=[" Human:", " AI:"]
        )
        answer = response.choices[0].text.strip()

    conversation += answer + "<br>"

    return {
        'conversation': conversation,
    }

if __name__ == '__main__':
    app.run(debug=True)
