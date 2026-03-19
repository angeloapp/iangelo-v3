import os
import json
import re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

app = Flask(__name__, static_folder='static')
CORS(app)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

MASTER_HMI_PROMPT = """Actua como el motor central de iAngelo V3.0.1, un asistente tipo Perplexity especializado en investigacion, creacion de contenido y soporte operativo en tiempo real. Tu prioridad absoluta es la experiencia humano-maquina de mas alto nivel: respuestas claras, accionables, con controles explicitos para que la persona sienta dominio total sobre el flujo."""

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/api/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        query = data.get('query', '')
        if not query:
            return jsonify({'error': 'Query is required'}), 400

        # Web search with DuckDuckGo
        search_results = []
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
                for r in results:
                    search_results.append({
                        'title': r.get('title', ''),
                        'url': r.get('href', ''),
                        'snippet': r.get('body', '')
                    })
        except Exception as e:
            search_results = []

        # Build context from search results
        context = '\n'.join([f"[{i+1}] {r['title']}: {r['snippet']}" for i, r in enumerate(search_results)])

        # Generate AI response
        messages = [
            {"role": "system", "content": MASTER_HMI_PROMPT},
            {"role": "user", "content": f"Pregunta: {query}\n\nResultados de busqueda web:\n{context}\n\nProporciona una respuesta completa citando las fuentes con [1], [2], etc."}
        ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=2000,
            temperature=0.7
        )

        answer = response.choices[0].message.content

        return jsonify({
            'answer': answer,
            'sources': search_results,
            'query': query
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        messages_history = data.get('messages', [])
        if not messages_history:
            return jsonify({'error': 'Messages are required'}), 400

        full_messages = [{"role": "system", "content": MASTER_HMI_PROMPT}] + messages_history

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=full_messages,
            max_tokens=2000,
            temperature=0.7
        )

        answer = response.choices[0].message.content
        return jsonify({'answer': answer})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'version': 'iAngelo V3.0.1'})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
