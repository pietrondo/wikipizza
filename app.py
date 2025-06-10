import os
from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import create_engine, Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import openai
import pdfminer.high_level
import requests
from bs4 import BeautifulSoup
import werkzeug

# Werkzeug 3 non ha più l'attributo __version__, ma Flask lo richiede nei test
if not hasattr(werkzeug, "__version__"):
    werkzeug.__version__ = "3"

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///wikipizza.db")
openai.api_key = os.getenv("OPENAI_API_KEY")

Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class Page(Base):
    __tablename__ = "pages"
    id = Column(Integer, primary_key=True)
    title = Column(Text, unique=True)
    content = Column(Text)

Base.metadata.create_all(engine)

app = Flask(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    return pdfminer.high_level.extract_text(file_path)


def extract_text_from_url(url: str) -> str:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    # remove scripts and styles
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n")


def generate_summary(text: str) -> str:
    if not openai.api_key:
        return text
    prompt = (
        "Riassumi il seguente testo e aggiungi link wiki alle frasi chiave. "
        "Rispondi in Markdown:\n" + text
    )
    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    return completion.choices[0].message.content


@app.route("/")
def index():
    session = Session()
    pages = session.query(Page).all()
    session.close()
    return render_template("index.html", pages=pages)


@app.route("/add", methods=["POST"])
def add_page():
    session = Session()
    title = request.form.get("title")
    pdf_file = request.files.get("pdf")
    url = request.form.get("url")
    text = ""
    if pdf_file and pdf_file.filename:
        path = os.path.join("/tmp", pdf_file.filename)
        pdf_file.save(path)
        text = extract_text_from_pdf(path)
    elif url:
        text = extract_text_from_url(url)
    content = generate_summary(text)
    page = Page(title=title, content=content)
    session.add(page)
    session.commit()
    session.close()
    return redirect(url_for("index"))


@app.route("/page/<int:page_id>")
def view_page(page_id):
    session = Session()
    page = session.query(Page).get(page_id)
    session.close()
    if not page:
        return "Page not found", 404
    return render_template("page.html", page=page)


if __name__ == "__main__":
    app.run(debug=True)
