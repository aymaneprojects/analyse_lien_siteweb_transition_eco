import os
import pandas as pd
from flask import Flask, request, render_template, redirect, url_for, send_file, session
from scrape import crawl_website
from llm import analyze_with_llm
from urllib.parse import urlparse
from data import validate_and_process_file

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

def validate_and_fix_url(url):
    """
    Valide et corrige une URL en ajoutant un schéma si nécessaire.
    """
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        corrected_url = f"https://{url}"
        print(f"[INFO] URL corrigée : {corrected_url}")
        return corrected_url
    return url

@app.route('/')
def index():
    print("[LOG] Chargement de la page d'accueil.")
    return render_template('index.html')

@app.route('/process_file', methods=['POST'])
def process_file():
    file = request.files.get('file')
    if not file:
        print("[ERREUR] Aucun fichier sélectionné.")
        return render_template('status.html', message="Aucun fichier sélectionné.", titles=[])

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    print(f"[LOG] Fichier téléchargé et sauvegardé : {file_path}")

    try:
        result = validate_and_process_file(file_path)
        if "error" in result:
            print(f"[ERREUR] {result['error']}")
            return render_template('status.html', message=result['error'], titles=[])

        session['file_path'] = file_path
        print(f"[LOG] Chemin du fichier sauvegardé dans la session : {file_path}")
        return redirect(url_for('process_sites'))

    except Exception as e:
        print(f"[ERREUR] Exception lors de la validation du fichier : {e}")
        return render_template('status.html', message=f"Erreur : {e}", titles=[])

@app.route('/process_sites', methods=['GET'])
def process_sites():
    print("[LOG] Début du traitement des sites...")
    file_path = session.get('file_path')
    if not file_path or not os.path.exists(file_path):
        print("[ERREUR] Fichier introuvable.")
        return render_template('status.html', message="Erreur : Fichier introuvable.", titles=[])

    try:
        validation_result = validate_and_process_file(file_path)
        if "error" in validation_result:
            print(f"[ERREUR] {validation_result['error']}")
            return render_template('status.html', message=validation_result["error"], titles=[])

        data = validation_result["data"]
        print(f"[LOG] Données validées : {len(data)} entrées.")

        results = []
        problematic_sites = []

        # Récupérer la limite de pages globale ou définir une valeur par défaut
        global_max_pages = request.args.get("max_pages", default=20, type=int)

        for entry in data:
            site_url = entry.get("SITE_WEB", "N/A")
            domain = entry.get("DOMAINE", "N/A")
            name = entry.get("NOM", "N/A")
            surname = entry.get("PRÉNOM", "N/A")

            # Priorité : limite spécifique à un site dans le fichier, sinon utiliser la limite globale
            max_pages = entry.get("MAX_PAGES", global_max_pages)

            # Validation et correction des URL
            site_url = validate_and_fix_url(site_url)
            if site_url == "N/A":
                print(f"[INFO] Ignoré : URL invalide pour {name} {surname}.")
                problematic_sites.append({"URL": site_url, "Reason": "URL invalide"})
                continue

            try:
                # Scraping
                print(f"[INFO] Début du scraping pour : {site_url} avec une limite de {max_pages} pages.")
                scraped_data, _ = crawl_website(site_url, max_pages=max_pages)
                if not scraped_data:
                    raise ValueError("Aucune donnée récupérée.")

                temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{name}_{surname}_scraped.txt")
                with open(temp_path, "w", encoding="utf-8") as f:
                    for url, content in scraped_data.items():
                        f.write(f"Page URL: {url}\n\n")
                        f.write("\n".join(content))
                        f.write("\n\n---\n\n")

                print(f"[INFO] Analyse avec LLM : {site_url}")
                result = analyze_with_llm(temp_path, domain)
                print(f"[INFO] Résultats : {result}")

                results.append({
                    "Name": name,
                    "Surname": surname,
                    "Domain": domain,
                    "Site URL": site_url,
                    "Ecological Transition (Score/30)": result["transition_ecologique"]["score"],
                    "Ecological Transition Justification": result["transition_ecologique"]["justification"],
                    "CSR Strategy (Score/30)": result["strategie_rse"]["score"],
                    "CSR Strategy Justification": result["strategie_rse"]["justification"],
                    "CSRD Mention (Score/40)": result["mention_csrd"]["score"],
                    "CSRD Mention Justification": result["mention_csrd"]["justification"],
                    "Global Score (/100)": result["score_global"]
                })

            except Exception as e:
                print(f"[ERREUR] Erreur pour {site_url} : {e}")
                problematic_sites.append({"URL": site_url, "Reason": str(e)})

        # Sauvegarde des résultats
        print("[LOG] Sauvegarde des résultats.")
        results_df = pd.DataFrame(results)
        results_path = os.path.join(app.config['RESULTS_FOLDER'], "results_analysis.csv")
        results_df.to_csv(results_path, index=False)
        session['results_path'] = results_path

        # Sauvegarde des sites problématiques
        if problematic_sites:
            print("[LOG] Sauvegarde des sites problématiques.")
            problematic_path = os.path.join(app.config['RESULTS_FOLDER'], "problematic_sites.csv")
            pd.DataFrame(problematic_sites).to_csv(problematic_path, index=False)

        print("[LOG] Traitement terminé.")
        return redirect(url_for('results'))

    except Exception as e:
        print(f"[ERREUR] Exception : {e}")
        return render_template('status.html', message=f"Erreur : {e}", titles=[])

@app.route('/results', methods=['GET'])
def results():
    results_path = session.get('results_path')
    if results_path and os.path.exists(results_path):
        results_df = pd.read_csv(results_path)
        results = results_df.to_dict(orient='records')
        return render_template('results.html', results=results)
    return render_template('status.html', message="Aucun résultat disponible.", titles=[])

@app.route('/download_results', methods=['GET'])
def download_results():
    results_path = session.get('results_path')
    if results_path and os.path.exists(results_path):
        return send_file(results_path, as_attachment=True)
    return "Aucun fichier de résultats à télécharger.", 404

if __name__ == '__main__':
    app.run(debug=True)