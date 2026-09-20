"""tests/test_kids.py — Testes funcionais e de segurança do módulo DUNO Kids."""
import os
import tempfile
import sqlite3
import pytest
from werkzeug.security import generate_password_hash
from app import create_app
from core.database import get_db


@pytest.fixture
def app_and_db():
    tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tmp_db.name
    tmp_db.close()
    os.environ["DATABASE"] = db_path

    # Inicializa tabela de usuários
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        INSERT INTO users (id, username, password_hash)
        VALUES (1, 'aluno_kids', 'hash123');
    """)
    conn.commit()
    conn.close()

    app = create_app()
    app.config["TESTING"] = True
    app.config["DATABASE"] = db_path
    app.config["WTF_CSRF_ENABLED"] = False

    yield app

    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def client(app_and_db):
    return app_and_db.test_client()


@pytest.fixture
def auth_client(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
    return client


def test_kids_requires_login(client):
    """Garante que usuários anônimos sejam redirecionados ao login."""
    res = client.get("/kids/dashboard")
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]


def test_kids_dashboard_loads_for_authenticated_user(auth_client):
    """Garante que o dashboard renderize a Skill Tree e estatísticas do aluno."""
    res = auth_client.get("/kids/dashboard")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "DUNO" in html
    assert "Kids" in html
    assert "Rede de computadores" in html
    assert "O que é a Internet?" in html


def test_kids_quiz_page_loads(auth_client):
    """Garante que a página de Quiz da Lição 1 renderize as perguntas."""
    res = auth_client.get("/kids/quiz/1")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "O que é a Internet no mundo real?" in html
    assert "quiz-progress-bar" in html
    assert "quiz-lives-count" in html


def test_kids_api_quiz_answer_correct(auth_client):
    """Testa validação segura de resposta correta no backend."""
    # Garante inicialização do banco acessando o dashboard primeiro
    auth_client.get("/kids/dashboard")
    payload = {"quiz_id": 1, "answer": "B"}
    res = auth_client.post("/kids/api/quiz/answer", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["correct"] is True
    assert data["xp_gained"] > 0
    assert "teia mundial de milhões de computadores" in data["explanation"]


def test_kids_api_quiz_answer_wrong_decrements_life(auth_client):
    """Testa se resposta incorreta desconta 1 vida no backend."""
    auth_client.get("/kids/dashboard")
    payload = {"quiz_id": 1, "answer": "A"}  # Opção A é errada
    res = auth_client.post("/kids/api/quiz/answer", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["correct"] is False
    assert data["xp_gained"] == 0
    assert data["lives_remaining"] == 4  # Começa com 5


def test_kids_api_lesson_complete(auth_client):
    """Testa conclusão de lição e concessão de estrelas/XP."""
    auth_client.get("/kids/dashboard")
    payload = {"lesson_id": 1, "correct_count": 3, "total_count": 3}
    res = auth_client.post("/kids/api/lesson/complete", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["stars"] == 3
    assert data["xp_reward"] == 100
    assert data["coins_reward"] == 20


def test_kids_leaderboard_loads(auth_client):
    """Garante que a tela de Ranking e Ligas carregue com o aluno listado."""
    auth_client.get("/kids/dashboard")
    res = auth_client.get("/kids/leaderboard")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Tabela de Líderes" in html
    assert "aluno_kids" in html
    assert "Liga Bronze" in html


def test_kids_quests_loads(auth_client):
    """Garante que a tela de Missões Diárias carregue as missões ativas."""
    auth_client.get("/kids/dashboard")
    res = auth_client.get("/kids/quests")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Missões Diárias" in html
    assert "Cofre de Baús da Aventura" in html


def test_kids_tux_mascot_and_nav_badge(auth_client):
    """Verifica que o Mascote Tux Pixel oficial e a badge NEWS são renderizados."""
    res = auth_client.get("/kids/dashboard")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    # Mascote Tux Pixel oficial e companheiro flutuante
    assert "tux-pixel-mascot-container" in html
    assert "mascot_main.png" in html
    assert "tux-companion-widget" in html
    # Badge NEWS no header/nav
    assert "NEWS" in html


def test_kids_interactive_lab_execution(auth_client):
    """Testa a execução de comandos do mini-laboratório interativo via API."""
    auth_client.get("/kids/dashboard")
    payload = {
        "lesson_id": 1,
        "type": "terminal",
        "command": "ping duno.kids"
    }
    res = auth_client.post("/kids/api/lab/execute", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["completed"] is True
    assert "ping statistics" in data["output"]
    assert "Tux" in data["tux_reaction"] or "milissegundos" in data["tux_reaction"]


def test_kids_curriculum_tracks_and_academy_funnel(auth_client):
    """Garante que as 5 trilhas do currículo possam ser selecionadas e carregadas."""
    tracks = ["os", "networks", "programming", "security", "english"]
    for t in tracks:
        res = auth_client.get(f"/kids/dashboard?module={t}")
        assert res.status_code == 200
        html = res.get_data(as_text=True)
        assert "kids-track-selector" in html
        assert f"module={t}" in html

