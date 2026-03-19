import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

app = Flask(__name__, static_folder='static')
CORS(app)

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
                results = list(ddgs.text(query, max_results=6))
                for r in results:
                    search_results.append({
                        'title': r.get('title', ''),
                        'url': r.get('href', ''),
                        'snippet': r.get('body', '')
                    })
        except Exception as e:
            return jsonify({'error': f'Search error: {str(e)}'}), 500

        # Build answer from search results (no AI needed)
        if not search_results:
            return jsonify({
                'answer': f'No encontre resultados para "{query}". Intenta con otros terminos.',
                'sources': [],
                'query': query
            })

        # Generate simple answer from search snippets
        answer_parts = [f'Encontre informacion sobre "{query}":\n\n']
        
        for i, result in enumerate(search_results, 1):
            answer_parts.append(f'[{i}] **{result["title"]}**\n{result["snippet"]}\n')
        
        answer = '\n'.join(answer_parts)
        answer += '\n\nFuentes completas disponibles abajo.'

        return jsonify({
            'answer': answer,
            'sources': search_results,
            'query': query
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'version': 'iAngelo V3.0.1 - Simple Edition'})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
