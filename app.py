import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    UserMixin,
    current_user,
)
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from sqlalchemy import create_engine, Column, Integer, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
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


class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey("pages.id"))
    content = Column(Text)
    embedding = Column(Text)


class User(Base, UserMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(Text, unique=True)
    password_hash = Column(Text)
    is_admin = Column(Integer, default=0)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

Base.metadata.create_all(engine)


def seed_data():
    """Inserisce alcune pagine di esempio se il DB è vuoto."""
    session = Session()
    if session.query(Page).count() == 0:
        pages = [
            Page(title="Benvenuto", content="Benvenuto su Wikipizza!"),
            Page(title="Come contribuire", content="Modifica liberamente le pagine."),
            Page(title="FAQ", content="Domande frequenti."),
        ]
        session.add_all(pages)
        session.commit()
    session.close()


seed_data()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")

login_manager = LoginManager(app)
login_manager.login_view = "login"


class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin


class SecureAdminIndex(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin


admin = Admin(app, index_view=SecureAdminIndex(), template_mode="bootstrap3")
admin.add_view(SecureModelView(Page, Session()))
admin.add_view(SecureModelView(User, Session()))


@login_manager.user_loader
def load_user(user_id: str):
    session = Session()
    user = session.get(User, int(user_id))
    session.close()
    return user


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


def embed_text(text: str) -> str:
    """Restituisce l'embedding OpenAI come stringa CSV."""
    if not openai.api_key:
        return ""
    resp = openai.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    vec = resp.data[0].embedding
    return ",".join(str(v) for v in vec)


def create_chunks(text: str, page_id: int, session) -> None:
    for chunk in [p.strip() for p in text.split("\n") if p.strip()]:
        emb = embed_text(chunk)
        session.add(Chunk(page_id=page_id, content=chunk, embedding=emb))


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


@app.route("/welcome")
def welcome():
    session = Session()
    page = session.query(Page).filter_by(title="Benvenuto").first()
    session.close()
    if not page:
        return "Benvenuto", 404
    return render_template("page.html", page=page)


@app.route("/add", methods=["POST"])
@login_required
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
    create_chunks(text, page.id, session)
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


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        session = Session()
        user = session.query(User).filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            session.close()
            return redirect(url_for("index"))
        flash("Credenziali non valide")
        session.close()
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        session = Session()
        if session.query(User).filter_by(username=username).first():
            flash("Utente esistente")
            session.close()
            return redirect(url_for("register"))
        user = User(username=username)
        user.set_password(password)
        session.add(user)
        session.commit()
        session.close()
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/edit/<int:page_id>", methods=["GET", "POST"])
@login_required
def edit_page(page_id):
    session = Session()
    page = session.get(Page, page_id)
    if not page:
        session.close()
        return "Page not found", 404
    if request.method == "POST":
        page.title = request.form.get("title")
        page.content = request.form.get("content")
        session.commit()
        session.close()
        return redirect(url_for("view_page", page_id=page.id))
    session.expunge(page)
    session.close()
    return render_template("edit.html", page=page)


if __name__ == "__main__":
    app.run(debug=True)
