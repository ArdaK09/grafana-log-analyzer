
from flask import Flask, jsonify, render_template

from QueryTracking import *

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/SubMethods/<path:method>', methods=['GET'])
def search_byMethod(method):
    result = searchByMethodName(method)
    return jsonify(result)

@app.route('/insertQueries', methods=["GET"])
def insertQuery_fromFolder():
    # Gets the data from the Datapath in config.yaml
    try:
        return insertQueryTraceFromPath(), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ParentMethods/<method>', methods=["GET"])
def search_byParentMethod(method):
    result = searchForParentMethods(method)
    return jsonify(result)

@app.route('/RepeatingSubMethods/<path:method>', methods=["GET"])
def repeated_methods(method):
    result = searchByMethodNameRepeating(method)
    return result

@app.route('/RepeatingSubMethods', methods=["GET"])
def repeated_methods_all():
    result = RepeatingMethodsAllFiles()
    return result


if __name__ == "__main__":
    host = db_access.HOST or "0.0.0.0"  # default values
    port = db_access.PORT or 2000
    app.run(host=host, port=port, debug=True)
