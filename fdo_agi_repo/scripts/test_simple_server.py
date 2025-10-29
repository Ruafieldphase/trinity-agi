#!/usr/bin/env python3
"""간단한 Flask 서버 테스트"""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/test')
def test():
    return jsonify({"status": "ok", "message": "Server is working"})

if __name__ == '__main__':
    print("Simple test server starting on http://localhost:8092")
    app.run(host='0.0.0.0', port=8092, debug=False, use_reloader=False)
