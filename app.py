from flask import Flask, Response, render_template, send_file, request, jsonify, session, send_from_directory
from scraper.hosting_scraper import stream_hosting_scraper
import os
import pandas as pd
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev')

SEARCH_TERMS_FILE = 'output/search_terms.json'
COMPANIES_JSON = 'output/companies.json'
LOG_FILE = 'output/scrape_debug.log'

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start-scrape", methods=["POST"])
def start_scrape():
    data = request.get_json()
    search_terms = data.get("search_terms", [])
    source = data.get("source", "directory")
    with open(SEARCH_TERMS_FILE, "w", encoding="utf-8") as f:
        json.dump(search_terms, f)
    session['search_terms'] = search_terms
    session['scrape_source'] = source
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    session['log_file'] = f"output/scrape_log_{timestamp}.log"
    return '', 204

@app.route("/scrape-stream")
def scrape_stream():
    # Read session before generator starts
    source = session.get('scrape_source', 'directory')
    log_path = session.get('log_file', LOG_FILE)
    def generate():
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'w', encoding='utf-8') as log_f:
            try:
                for line in stream_hosting_scraper(mode=source):
                    ts_line = f"{datetime.utcnow().isoformat()} - {line}"
                    log_f.write(ts_line + "\n")
                    log_f.flush()
                    yield f"data: {ts_line}\n\n"
            except Exception as e:
                err = f"{datetime.utcnow().isoformat()} - [LOG] Scraper failed: {e}"
                log_f.write(err + "\n")
                yield f"data: {err}\n\n"
    return Response(generate(), mimetype="text/event-stream")

@app.route("/download")
def download():
    fmt = request.args.get("format", "xlsx")
    if fmt == "csv":
        df = pd.read_excel("output/us_hosting_companies.xlsx")
        csv_path = "output/us_hosting_companies.csv"
        df.to_csv(csv_path, index=False)
        return send_file(csv_path, as_attachment=True)
    elif fmt == "json":
        df = pd.read_excel("output/us_hosting_companies.xlsx")
        json_path = COMPANIES_JSON
        df.to_json(json_path, orient="records", force_ascii=False)
        return send_file(json_path, as_attachment=True)
    elif fmt == "log":
        log_path = session.get('log_file', LOG_FILE)
        return send_file(log_path, as_attachment=True)
    else:
        return send_file("output/us_hosting_companies.xlsx", as_attachment=True)

@app.route("/output/companies.json")
def companies_json():
    if os.path.exists(COMPANIES_JSON):
        with open(COMPANIES_JSON, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    # Fallback: try final_results.xlsx
    fallback_xlsx = "output/final_results.xlsx"
    if os.path.exists(fallback_xlsx):
        df = pd.read_excel(fallback_xlsx)
        return jsonify(df.to_dict(orient="records"))
    # If both missing, log and return empty
    print("[WARN] companies.json and final_results.xlsx missing!")
    return jsonify([])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
