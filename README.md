# Wikipizza

Una semplice webapp per gestire note in stile wiki. Permette di caricare testi da PDF o URL, sfrutta le API di OpenAI per riassumerli e creare collegamenti tra i concetti. Include registrazione, login, editor Markdown e una piccola interfaccia admin.

## Requisiti

- Python 3.10+
- Dipendenze in `requirements.txt`
- Variabile `OPENAI_API_KEY` impostata per utilizzare le API di OpenAI

## Installazione

```bash
pip install -r requirements.txt
```

## Avvio

```bash
python app.py
```

La prima volta verrà creato il database SQLite `wikipizza.db`.
Registrati e poi imposta `is_admin` manualmente nel database per abilitare l'accesso all'area admin.

## Test

Sono presenti pochi test di esempio eseguibili con:

```bash
pytest
```
