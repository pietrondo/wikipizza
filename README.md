# Wikipizza

Una semplice webapp per gestire note in stile wiki. Permette di caricare testi da PDF o URL, sfrutta le API di OpenAI per riassumerli e creare collegamenti tra i concetti. Include registrazione, login, editor Markdown con SimpleMDE e una piccola interfaccia admin tramite Flask‑Admin. Ogni pagina è modificabile.

All'avvio vengono create alcune pagine d'esempio, tra cui **Benvenuto**, visibile anche all'indirizzo `/welcome`. L'analisi dei PDF è arricchita da un semplice sistema di RAG: il testo viene suddiviso in paragrafi e memorizzato con gli embedding di OpenAI per future ricerche.

L'interfaccia è basata su Bootstrap 5 per offrire un aspetto più gradevole.


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

La prima volta verrà creato il database SQLite `wikipizza.db` con alcune pagine di esempio.
Visita `http://localhost:5000/welcome` per la pagina introduttiva.
Registrati e poi imposta `is_admin` manualmente nel database per abilitare l'accesso all'area admin.
La prima volta verrà creato il database SQLite `wikipizza.db`.

## Test

Sono presenti pochi test di esempio eseguibili con:

```bash
pytest
```
