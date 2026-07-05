"""
Tests for admin blocks CRUD API:
  - GET  /api/pages/{page_id}/blocks
  - PUT  /api/pages/{page_id}/blocks  (replace all blocks)
  - POST /api/blocks/{block_id}/move  (move up/down)

All 10 valid block types: hero, text, image, gallery, video,
table, cards, documents, form, divider
"""
import json
import os
import sys
import tempfile
import pytest
from fastapi.testclient import TestClient

# --- Boot the app with a temp database ---
DB_FD, DB_PATH = tempfile.mkstemp(suffix=".db")
os.close(DB_FD)  # we only need the path
os.environ["ZOLO_DATABASE_PATH"] = DB_PATH
os.environ["ZOLO_SECRET"] = "test-secret-key-for-tests"

sys.path.insert(0, os.path.dirname(__file__))

import config as cfg
cfg.DATABASE_PATH = DB_PATH

from database import init_db, seed_db, get_db

# Create a fresh DB
init_db()
seed_db()

# Replace sha256-based admin user with bcrypt so login works
import bcrypt
conn = get_db()
conn.execute("DELETE FROM users")
pw_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
conn.execute(
    "INSERT INTO users (id, username, password_hash, role) VALUES (1, 'admin', ?, 'admin')",
    (pw_hash,),
)
conn.commit()
conn.close()

from app import app

client = TestClient(app)

# Login once at module level — avoids rate limiter
_login_resp = client.post(
    "/login",
    data={"username": "admin", "password": "admin123"},
    follow_redirects=False,
)
assert _login_resp.status_code == 302, f"Init login failed: {_login_resp.status_code}"
SESSION_COOKIE = _login_resp.cookies.get("session")


# ====== Helpers ======

def auth_headers():
    """Return headers dict with session cookie for API calls."""
    return {"Cookie": f"session={SESSION_COOKIE}"}


def make_unauth_client():
    """Return a client without any cookies for unauth tests."""
    c = TestClient(app)
    return c


SAMPLE_BLOCKS = [
    # hero
    {"id": "b-test-hero", "type": "hero", "name": "Баннер тест",
     "config": {"title": "Заголовок", "subtitle": "Подзаголовок", "btn_text": "Узнать",
                "btn_url": "#", "bg_color": "#1b4332", "bg_image": ""}},
    # text
    {"id": "b-test-text", "type": "text", "name": "Текст",
     "config": {"content": "<p>Тестовый текст</p>"}},
    # image
    {"id": "b-test-image", "type": "image", "name": "Изображение",
     "config": {"src": "https://example.com/img.jpg", "alt": "тест", "caption": "Тест"}},
    # gallery
    {"id": "b-test-gallery", "type": "gallery", "name": "Галерея",
     "config": {"images": ["https://example.com/1.jpg", "https://example.com/2.jpg"], "columns": 3}},
    # video
    {"id": "b-test-video", "type": "video", "name": "Видео",
     "config": {"url": "https://rutube.ru/video/xxx", "title": "Видео тест", "description": "Описание"}},
    # table
    {"id": "b-test-table", "type": "table", "name": "Таблица",
     "config": {"headers": ["Колонка 1", "Колонка 2"], "rows": 3, "cols": 2}},
    # cards
    {"id": "b-test-cards", "type": "cards", "name": "Плитки",
     "config": {"items": [{"title": "Название", "text": "Описание", "link": "#"}], "columns": 3}},
    # documents
    {"id": "b-test-docs", "type": "documents", "name": "Документы",
     "config": {"docs": [{"title": "Документ 1", "url": "#", "description": "Описание"}]}},
    # form
    {"id": "b-test-form", "type": "form", "name": "Форма",
     "config": {"form_type": "suggest", "title": "Форма тест"}},
    # divider
    {"id": "b-test-divider", "type": "divider", "name": "Разделитель",
     "config": {"style": "solid"}},
]


# ====== GET BLOCKS ======

class TestGetBlocks:
    def test_get_blocks_existing_page(self):
        """Get blocks for a page that has seed data (school has 3: hero, text, documents)."""
        headers = auth_headers()
        resp = client.get("/api/pages/school/blocks", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 3  # seed data for school page
        for b in data:
            assert "id" in b
            assert "page_id" in b
            assert "type" in b
            assert "config" in b
            assert isinstance(b["config"], dict)

    def test_get_blocks_no_blocks(self):
        """Get blocks for a page that has none (e.g. kindergarten)."""
        headers = auth_headers()
        resp = client.get("/api/pages/kindergarten/blocks", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_blocks_nonexistent_page(self):
        """Get blocks for a page that doesn't exist — returns empty list."""
        headers = auth_headers()
        resp = client.get("/api/pages/nonexistent-page/blocks", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_blocks_parses_config_json(self):
        """Config field should be parsed from JSON string to dict."""
        headers = auth_headers()
        resp = client.get("/api/pages/school/blocks", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        for b in data:
            assert isinstance(b["config"] if isinstance(b.get("config"), dict) else json.loads(b["config"]), dict)

    def test_get_blocks_ordered_by_sort_order(self):
        """Blocks should come back sorted by sort_order ascending."""
        headers = auth_headers()
        resp = client.get("/api/pages/school/blocks", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        orders = [b["sort_order"] for b in data]
        assert orders == sorted(orders), f"Blocks not sorted: {orders}"


# ====== PUT BLOCKS (replace all) ======

class TestPutBlocks:
    TEST_PAGE = "kindergarten"

    def test_save_empty_blocks_clears_page(self):
        """PUT with empty list should clear all blocks for a page."""
        headers = auth_headers()
        # First put blocks on the page
        blocks = SAMPLE_BLOCKS[:2]
        resp = client.put(f"/api/pages/{self.TEST_PAGE}/blocks", json=blocks, headers=headers)
        assert resp.status_code == 200, f"Save failed: {resp.text[:200]}"
        assert len(client.get(f"/api/pages/{self.TEST_PAGE}/blocks", headers=headers).json()) == 2

        # Clear
        resp = client.put(f"/api/pages/{self.TEST_PAGE}/blocks", json=[], headers=headers)
        assert resp.status_code == 200
        assert client.get(f"/api/pages/{self.TEST_PAGE}/blocks", headers=headers).json() == []

    def test_save_all_block_types(self):
        """PUT with all 10 valid block types should save and return them correctly."""
        headers = auth_headers()
        # Clean and save all 10 block types
        client.put(f"/api/pages/{self.TEST_PAGE}/blocks", json=[], headers=headers)
        resp = client.put(f"/api/pages/{self.TEST_PAGE}/blocks", json=SAMPLE_BLOCKS, headers=headers)
        assert resp.status_code == 200

        saved = client.get(f"/api/pages/{self.TEST_PAGE}/blocks", headers=headers).json()
        assert len(saved) == 10, f"Expected 10 blocks, got {len(saved)}"

        saved_types = {b["type"] for b in saved}
        expected_types = {"hero", "text", "image", "gallery", "video",
                          "table", "cards", "documents", "form", "divider"}
        assert saved_types == expected_types, f"Types mismatch: {saved_types} vs {expected_types}"

        saved_map = {b["id"]: b for b in saved}
        assert saved_map["b-test-hero"]["config"]["title"] == "Заголовок"
        assert saved_map["b-test-hero"]["type"] == "hero"
        assert saved_map["b-test-divider"]["config"]["style"] == "solid"
        assert saved_map["b-test-table"]["config"]["rows"] == 3

    def test_save_overwrites_existing_blocks(self):
        """PUT should replace ALL blocks, not append."""
        headers = auth_headers()
        client.put(f"/api/pages/{self.TEST_PAGE}/blocks", json=SAMPLE_BLOCKS[:2], headers=headers)
        assert len(client.get(f"/api/pages/{self.TEST_PAGE}/blocks", headers=headers).json()) == 2

        new_blocks = [{"id": "b-only", "type": "text", "name": "Единственный",
                       "config": {"content": "<p>One</p>"}}]
        resp = client.put(f"/api/pages/{self.TEST_PAGE}/blocks", json=new_blocks, headers=headers)
        assert resp.status_code == 200

        saved = client.get(f"/api/pages/{self.TEST_PAGE}/blocks", headers=headers).json()
        assert len(saved) == 1
        assert saved[0]["id"] == "b-only"

    def test_save_assigns_sort_order(self):
        """PUT should assign sort_order based on array index."""
        headers = auth_headers()
        blocks = [
            {"id": "b-first", "type": "text", "name": "Первый", "config": {"content": "<p>1</p>"}},
            {"id": "b-second", "type": "text", "name": "Второй", "config": {"content": "<p>2</p>"}},
            {"id": "b-third", "type": "text", "name": "Третий", "config": {"content": "<p>3</p>"}},
        ]
        client.put(f"/api/pages/{self.TEST_PAGE}/blocks", json=blocks, headers=headers)
        saved = client.get(f"/api/pages/{self.TEST_PAGE}/blocks", headers=headers).json()
        for i, b in enumerate(saved):
            assert b["sort_order"] == i, f"Block {b['id']} has sort_order {b['sort_order']}, expected {i}"

    def test_save_generates_id_if_missing(self):
        """PUT should auto-generate an ID if block has no 'id' field."""
        headers = auth_headers()
        blocks = [{"type": "text", "name": "Без ID", "config": {"content": "<p>Auto ID</p>"}}]
        resp = client.put(f"/api/pages/{self.TEST_PAGE}/blocks", json=blocks, headers=headers)
        assert resp.status_code == 200

        saved = client.get(f"/api/pages/{self.TEST_PAGE}/blocks", headers=headers).json()
        assert len(saved) == 1
        assert saved[0]["id"].startswith("b"), f"Auto ID doesn't start with 'b': {saved[0]['id']}"

    def test_save_reuses_block_id_same_page(self):
        """PUT with same block IDs should replace them (same page)."""
        headers = auth_headers()
        client.put(f"/api/pages/{self.TEST_PAGE}/blocks", json=[
            {"id": "b-reuse", "type": "text", "name": "Старый", "config": {"content": "<p>Old</p>"}},
        ], headers=headers)

        resp = client.put(f"/api/pages/{self.TEST_PAGE}/blocks", json=[
            {"id": "b-reuse", "type": "hero", "name": "Новый", "config": {"title": "Новый заголовок"}},
        ], headers=headers)
        assert resp.status_code == 200

        saved = client.get(f"/api/pages/{self.TEST_PAGE}/blocks", headers=headers).json()
        assert len(saved) == 1
        assert saved[0]["type"] == "hero"
        assert saved[0]["name"] == "Новый"

    def test_save_generates_new_id_if_id_taken_by_different_page(self):
        """If a block ID already belongs to a different page, auto-generate a new unique ID."""
        headers = auth_headers()
        # Save on school page first
        client.put("/api/pages/school/blocks", json=[
            {"id": "b-conflict", "type": "text", "name": "School block",
             "config": {"content": "<p>School</p>"}}
        ], headers=headers)

        # Same ID on different page — should auto-generate
        resp = client.put(f"/api/pages/{self.TEST_PAGE}/blocks", json=[
            {"id": "b-conflict", "type": "hero", "name": "Different page",
             "config": {"title": "Конфликт"}},
        ], headers=headers)
        assert resp.status_code == 200

        saved = client.get(f"/api/pages/{self.TEST_PAGE}/blocks", headers=headers).json()
        assert len(saved) == 1
        assert saved[0]["id"] != "b-conflict", "Should have generated new ID for cross-page conflict"
        assert saved[0]["type"] == "hero"

    def test_save_nonexistent_page(self):
        """PUT to a non-existent page should fail with 400 (FK constraint)."""
        headers = auth_headers()
        resp = client.put("/api/pages/no-such-page/blocks", json=[
            {"id": "b-orphan", "type": "text", "name": "Orphan", "config": {"content": "<p>Orphan</p>"}}
        ], headers=headers)
        assert resp.status_code == 400, f"Expected 400 for FK violation, got {resp.status_code}: {resp.text[:200]}"

    def test_save_with_extra_fields(self):
        """PUT with extra fields should work (they should be ignored)."""
        headers = auth_headers()
        resp = client.put(f"/api/pages/{self.TEST_PAGE}/blocks", json=[{
            "id": "b-extra",
            "type": "text",
            "name": "С лишними полями",
            "config": {"content": "<p>Extra</p>"},
            "extra_field": "should be ignored",
            "another": 123,
        }], headers=headers)
        assert resp.status_code == 200

        saved = client.get(f"/api/pages/{self.TEST_PAGE}/blocks", headers=headers).json()
        assert len(saved) == 1
        assert saved[0]["type"] == "text"


# ====== MOVE BLOCK ======

class TestMoveBlock:
    def _setup(self):
        """Create 3 text blocks on kindergarten page for move tests. Returns headers."""
        headers = auth_headers()
        client.put("/api/pages/kindergarten/blocks", json=[], headers=headers)
        blocks = [
            {"id": "b-move-first", "type": "text", "name": "Первый", "config": {"content": "<p>First</p>"}},
            {"id": "b-move-second", "type": "text", "name": "Второй", "config": {"content": "<p>Second</p>"}},
            {"id": "b-move-third", "type": "text", "name": "Третий", "config": {"content": "<p>Third</p>"}},
        ]
        resp = client.put("/api/pages/kindergarten/blocks", json=blocks, headers=headers)
        assert resp.status_code == 200
        return headers

    def test_move_block_down(self):
        """Move block down: second block swaps position with third."""
        headers = self._setup()
        resp = client.post("/api/blocks/b-move-second/move?direction=down", headers=headers)
        assert resp.status_code == 200, f"Move failed: {resp.text[:200]}"

        saved = client.get("/api/pages/kindergarten/blocks", headers=headers).json()
        ids = [b["id"] for b in saved]
        assert ids == ["b-move-first", "b-move-third", "b-move-second"], f"Unexpected order: {ids}"

    def test_move_block_up(self):
        """Move block up: second block swaps position with first."""
        headers = self._setup()
        resp = client.post("/api/blocks/b-move-second/move?direction=up", headers=headers)
        assert resp.status_code == 200

        saved = client.get("/api/pages/kindergarten/blocks", headers=headers).json()
        ids = [b["id"] for b in saved]
        assert ids == ["b-move-second", "b-move-first", "b-move-third"], f"Unexpected order: {ids}"

    def test_move_first_block_up_stays(self):
        """Moving first block up should leave order unchanged."""
        headers = self._setup()
        resp = client.post("/api/blocks/b-move-first/move?direction=up", headers=headers)
        assert resp.status_code == 200

        saved = client.get("/api/pages/kindergarten/blocks", headers=headers).json()
        ids = [b["id"] for b in saved]
        assert ids == ["b-move-first", "b-move-second", "b-move-third"], f"Unexpected order: {ids}"

    def test_move_last_block_down_stays(self):
        """Moving last block down should leave order unchanged."""
        headers = self._setup()
        resp = client.post("/api/blocks/b-move-third/move?direction=down", headers=headers)
        assert resp.status_code == 200

        saved = client.get("/api/pages/kindergarten/blocks", headers=headers).json()
        ids = [b["id"] for b in saved]
        assert ids == ["b-move-first", "b-move-second", "b-move-third"], f"Unexpected order: {ids}"

    def test_move_nonexistent_block(self):
        """Moving a non-existent block should return 404."""
        headers = auth_headers()
        resp = client.post("/api/blocks/b-nonexistent/move?direction=up", headers=headers)
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text[:200]}"

    def test_move_without_auth(self):
        """Move without session cookie should return 401."""
        anon = make_unauth_client()
        resp = anon.post("/api/blocks/b-move-first/move?direction=up")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"


# ====== ERROR CASES ======

class TestBlockErrors:
    def test_put_invalid_block_type(self):
        """PUT with invalid block type should be rejected by DB CHECK constraint."""
        headers = auth_headers()
        resp = client.put("/api/pages/kindergarten/blocks", json=[
            {"id": "b-invalid", "type": "invalid_type", "name": "Invalid", "config": {}}
        ], headers=headers)
        assert resp.status_code == 400, f"Expected 400 for invalid type, got {resp.status_code}: {resp.text[:200]}"

    def test_get_blocks_without_auth(self):
        """GET blocks without auth should return 401."""
        anon = make_unauth_client()
        resp = anon.get("/api/pages/school/blocks")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

    def test_put_blocks_without_auth(self):
        """PUT blocks without auth should return 401."""
        anon = make_unauth_client()
        resp = anon.put("/api/pages/school/blocks", json=[])
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"


# ====== CLEANUP ======
def teardown_module(module):
    """Remove temp database and WAL/SHM files."""
    try:
        os.unlink(DB_PATH)
    except OSError:
        pass
    for ext in ("-wal", "-shm"):
        try:
            os.unlink(DB_PATH + ext)
        except OSError:
            pass
