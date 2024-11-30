import pandas as pd

REQUIRED_COLUMNS = ["NOM", "PRÉNOM", "SITE_WEB"]

def validate_and_process_file(file_path):
    try:
        file_extension = file_path.split('.')[-1]
        if file_extension == 'csv':
            data = pd.read_csv(file_path)
        elif file_extension == 'xlsx':
            data = pd.read_excel(file_path)
        else:
            return {"error": "Unsupported file format. Please upload a CSV or XLSX file."}

        # Convert all columns to uppercase
        data.columns = [col.upper() for col in data.columns]

        missing_columns = [col for col in REQUIRED_COLUMNS if col not in data.columns]
        if missing_columns:
            return {"error": f"Missing required columns: {', '.join(missing_columns)}"}

        # Return the data for further processing
        return {"data": data[REQUIRED_COLUMNS].to_dict(orient='records')}
    except Exception as e:
        return {"error": f"Error processing file: {e}"}