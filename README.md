# GAO Antifraud Resource - Demo Test Site

A Streamlit application for searching the GAO Fraud Ontology (GFO) by fraud activity type.

## Features

- **Fraud Type Search**: Select a fraud activity to find related resources across 5 categories:
  - Fraud Scheme Examples
  - Fraud Awareness Resources
  - Fraud Prevention & Detection Guidance
  - Fraud Risk Management Principles
  - GAO Reports

- **Search Comparison**: Compare results between the Demo Test Site queries and the original AFR site logic to identify discrepancies.

- **Excel Export**: Download comparison results with methodology notes.

## Files

| File | Description |
|------|-------------|
| `app.py` | Main Streamlit application |
| `gfo_turtle.ttl` | GAO Fraud Ontology (auto-loaded) |
| `requirements.txt` | Python dependencies |

## Requirements

```
streamlit
rdflib
pandas
openpyxl
```

## Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment

Deployed on [Streamlit Community Cloud](https://streamlit.io/cloud). Set **Main file path** to `app.py`.

## Usage

1. Select a fraud type from the dropdown
2. Click "Search All Resources"
3. Browse results by tab
4. (Optional) Click "Run Comparison" to compare with original AFR logic
5. (Optional) Export comparison to Excel
