from together import Together
import os
import requests
import json

# Clé API à insérer ici
API_KEY = "61f3aee12215d2555803ef1f1eb20c67fd694e547be9c22f2ae203a6910645c9"

def truncate_content(content, max_tokens=120000):
    """
    Truncate the content to ensure it stays within the token limit for the LLM.
    """
    tokens = content.split()
    if len(tokens) > max_tokens:
        print(f"Truncating content from {len(tokens)} tokens to {max_tokens} tokens.")
        return " ".join(tokens[:max_tokens])
    return content

def analyze_with_llm(file_path, domain):
    """
    Analyze a file's content using Together AI's LLM.
    """
    if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
        print(f"File is empty or does not exist: {file_path}")
        return {
            "transition_ecologique": {"score": "Données insuffisantes", "justification": ""},
            "strategie_rse": {"score": "Données insuffisantes", "justification": ""},
            "mention_csrd": {"score": "Données insuffisantes", "justification": ""},
            "score_global": "Données insuffisantes"
        }

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Truncate content if necessary
    content = truncate_content(content)

    # Initialisation du client Together
    try:
        client = Together(api_key=API_KEY)
    except Exception as e:
        print(f"Erreur lors de l'initialisation du client Together : {e}")
        return {
            "transition_ecologique": {"score": "Erreur", "justification": "Erreur lors de l'initialisation du client."},
            "strategie_rse": {"score": "Erreur", "justification": "Erreur lors de l'initialisation du client."},
            "mention_csrd": {"score": "Erreur", "justification": "Erreur lors de l'initialisation du client."},
            "score_global": "Erreur"
        }

    # Construction du prompt
    prompt = f"""
    Analyze the following text and evaluate it based on these criteria:
    1. Ecological transition: mention of ecological commitments (score out of 30).
    2. CSR strategy: mention of social responsibility commitments (score out of 30).
    3. CSRD standard: mention of commitments related to the CSRD standard (score out of 40).

    IMPORTANT: Respond STRICTLY in JSON format without any additional explanation. The format must be:

    {{
        "transition_ecologique": {{"score": <score out of 30>, "justification": "<justification>"}},
        "strategie_rse": {{"score": <score out of 30>, "justification": "<justification>"}},
        "mention_csrd": {{"score": <score out of 40>, "justification": "<justification>"}},
        "score_global": <sum of scores>
    }}

    Do not include any text outside this JSON structure.

    Text: {content}
    """

    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-Vision-Free",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1,
            stream=False
        )

        # Vérification de la réponse
        if not hasattr(response, "choices") or not response.choices:
            print("Erreur : Pas de réponse valide reçue de l'API.")
            return {
                "transition_ecologique": {"score": "Erreur", "justification": "Pas de réponse valide de l'API."},
                "strategie_rse": {"score": "Erreur", "justification": "Pas de réponse valide de l'API."},
                "mention_csrd": {"score": "Erreur", "justification": "Pas de réponse valide de l'API."},
                "score_global": "Erreur"
            }

        # Extraction de la réponse brute
        raw_response = response.choices[0].message.content.strip()
        print("Réponse brute :", raw_response)

        # Validation et parsing JSON
        try:
            result = json.loads(raw_response)
            if "transition_ecologique" in result and "strategie_rse" in result and "mention_csrd" in result:
                return result
            else:
                raise ValueError("Le JSON ne contient pas les clés attendues.")
        except json.JSONDecodeError as e:
            print(f"Erreur JSON : {e}. Réponse brute : {raw_response}")
            return {
                "transition_ecologique": {"score": "Erreur", "justification": "Erreur de format JSON."},
                "strategie_rse": {"score": "Erreur", "justification": "Erreur de format JSON."},
                "mention_csrd": {"score": "Erreur", "justification": "Erreur de format JSON."},
                "score_global": "Erreur"
            }
        except ValueError as e:
            print(f"Erreur de validation JSON : {e}. Réponse brute : {raw_response}")
            return {
                "transition_ecologique": {"score": "Erreur", "justification": "JSON invalide."},
                "strategie_rse": {"score": "Erreur", "justification": "JSON invalide."},
                "mention_csrd": {"score": "Erreur", "justification": "JSON invalide."},
                "score_global": "Erreur"
            }

    except requests.exceptions.HTTPError as e:
        print(f"Erreur HTTP : {e}")
        return {
            "transition_ecologique": {"score": "Erreur", "justification": f"Erreur HTTP : {e}"},
            "strategie_rse": {"score": "Erreur", "justification": f"Erreur HTTP : {e}"},
            "mention_csrd": {"score": "Erreur", "justification": f"Erreur HTTP : {e}"},
            "score_global": "Erreur"
        }

    except Exception as e:
        print(f"Erreur lors de l'appel à l'API : {e}")
        return {
            "transition_ecologique": {"score": "Erreur", "justification": f"Erreur API : {e}"},
            "strategie_rse": {"score": "Erreur", "justification": f"Erreur API : {e}"},
            "mention_csrd": {"score": "Erreur", "justification": f"Erreur API : {e}"},
            "score_global": "Erreur"
        }