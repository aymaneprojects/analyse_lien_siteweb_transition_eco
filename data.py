import pandas as pd
from difflib import get_close_matches

REQUIRED_COLUMNS = ["NOM", "PRÉNOM", "SITE_WEB"]
DEFAULT_VALUES = {"NOM": "N/A", "PRÉNOM": "N/A", "SITE_WEB": "N/A"}

def validate_and_process_file(file_path):
    """
    Valide et traite un fichier en vérifiant les colonnes obligatoires.
    Ajoute les colonnes manquantes et gère les similitudes.
    """
    try:
        # Déterminer le format du fichier
        file_extension = file_path.split('.')[-1]
        if file_extension == 'csv':
            data = pd.read_csv(file_path)
        elif file_extension == 'xlsx':
            data = pd.read_excel(file_path)
        else:
            return {"error": "Unsupported file format. Please upload a CSV or XLSX file."}

        # Convertir les colonnes en majuscules
        print("[LOG] Conversion des colonnes en majuscules...")
        data.columns = [col.upper() for col in data.columns]

        # Identifier les colonnes manquantes
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in data.columns]
        print(f"[LOG] Colonnes manquantes : {missing_columns}")
        
        if missing_columns:
            # Recherche de colonnes similaires
            for missing_col in missing_columns:
                print(f"[LOG] Recherche de colonnes similaires pour : {missing_col}")
                similar_cols = get_close_matches(missing_col, data.columns, n=1, cutoff=0.8)
                if similar_cols:
                    print(f"[LOG] Correspondance trouvée : {missing_col} ≈ {similar_cols[0]}")
                    data[missing_col] = data[similar_cols[0]]
                else:
                    print(f"[LOG] Aucune correspondance trouvée pour {missing_col}. Ajout avec valeur par défaut.")
                    data[missing_col] = DEFAULT_VALUES[missing_col]

        # Vérification finale
        final_columns = [col for col in REQUIRED_COLUMNS if col in data.columns]
        if not final_columns:
            return {"error": "Validation failed. No valid columns found."}

        print("[LOG] Validation réussie.")
        return {"data": data[REQUIRED_COLUMNS].to_dict(orient='records')}
    
    except Exception as e:
        print(f"[ERREUR] Erreur lors du traitement du fichier : {e}")
        return {"error": f"Error processing file: {e}"}