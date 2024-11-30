import os
from flask import Flask, request, render_template, redirect, url_for, send_file, session
import pandas as pd
from scrape import crawl_website
from llm import analyze_with_llm

# Configuration de l'application Flask
app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER

# Création des dossiers nécessaires
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

@app.route('/')
def index():
    """
    Page d'accueil pour soumettre une URL et des informations utilisateur.
    """
    return render_template('index.html')

@app.route('/process_text', methods=['POST'])
def process_text():
    """
    Gère la soumission de l'utilisateur, lance le scraping, 
    puis passe à la page de statut.
    """
    input_text = request.form.get('site_url')
    user_name = request.form.get('name')
    user_surname = request.form.get('surname')
    user_domain = request.form.get('domain')
    max_pages = int(request.form.get('max_pages', 20))  # Limite de pages

    if not input_text or not user_name.strip() or not user_surname.strip() or not user_domain.strip():
        return render_template('status.html', message="Champs utilisateur invalides. Veuillez remplir correctement.")

    session['user_name'] = user_name
    session['user_surname'] = user_surname
    session['user_domain'] = user_domain

    try:
        scraped_data, page_titles = crawl_website(input_text, max_pages=max_pages)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], "scraped_data.txt")
        with open(temp_path, "w", encoding="utf-8") as f:
            for url, content in scraped_data.items():
                f.write(f"Page URL: {url}\n\n")
                f.write("\n".join(content))
                f.write("\n\n---\n\n")

        session['scraped_file'] = temp_path
        session['page_titles'] = page_titles
        return render_template('status.html', titles=page_titles, next_step_url=url_for('analyze_results'))

    except Exception as e:
        return render_template('status.html', message=f"Erreur lors du scraping : {str(e)}")

@app.route('/analyze_results', methods=['GET'])
def analyze_results():
    """
    Analyse les données scrappées avec le LLM.
    """
    file_path = session.get('scraped_file')
    if not file_path or not os.path.exists(file_path):
        return render_template('status.html', message="Erreur : Fichier de données scrappées introuvable.")

    try:
        result = analyze_with_llm(file_path, session.get('user_domain', ''))
        csv_path = os.path.join(app.config['RESULTS_FOLDER'], "results_analysis.csv")
        results_df = pd.DataFrame([{
            "Name": session.get('user_name', 'N/A'),
            "Surname": session.get('user_surname', 'N/A'),
            "Domain": session.get('user_domain', 'N/A'),
            "Ecological Transition (Score/30)": result["transition_ecologique"]["score"],
            "Ecological Transition Justification": result["transition_ecologique"]["justification"],
            "CSR Strategy (Score/30)": result["strategie_rse"]["score"],
            "CSR Strategy Justification": result["strategie_rse"]["justification"],
            "CSRD Mention (Score/40)": result["mention_csrd"]["score"],
            "CSRD Mention Justification": result["mention_csrd"]["justification"],
            "Global Score (/100)": result["score_global"]
        }])
        results_df.to_csv(csv_path, index=False)
        return redirect(url_for('results'))

    except Exception as e:
        return render_template('status.html', message=f"Erreur lors de l'analyse avec le LLM : {str(e)}")

@app.route('/results', methods=['GET'])
def results():
    """
    Affiche les résultats finaux de l'analyse.
    """
    csv_path = os.path.join(app.config['RESULTS_FOLDER'], "results_analysis.csv")
    if os.path.exists(csv_path):
        results_df = pd.read_csv(csv_path)
        results = results_df.to_dict(orient="records")
        return render_template('results.html', results=results, csv_path=csv_path)

    return render_template('status.html', message="Aucun fichier de résultats disponible.")

@app.route('/download_results', methods=['GET'])
def download_results():
    """
    Permet de télécharger les résultats sous forme de fichier CSV.
    """
    csv_path = os.path.join(app.config['RESULTS_FOLDER'], "results_analysis.csv")
    if os.path.exists(csv_path):
        return send_file(csv_path, as_attachment=True)

    return "Aucun fichier de résultats disponible pour le téléchargement.", 404

if __name__ == '__main__':
    app.run(debug=True)