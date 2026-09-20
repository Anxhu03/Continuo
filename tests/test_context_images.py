"""
CONTINUO — Visual / Image Context Tests (Phase 9.4)
Validates secure visual context storage, metadata extraction, magic bytes checking,
dimension extraction, SHA-256 checksums, protected file streaming, path traversal protection,
IDOR defense, association validation, and project deletion cascading.
"""

import io
from pathlib import Path
import pytest
from PIL import Image

from backend.config import settings
from backend.services.storage import get_storage_provider, LocalStorageProvider


def register_user(client, email: str, password: str = "SecurePass123!", name: str = "Test User"):
    resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": name,
    })
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_project(client, headers: dict, name: str = "Visual Context Project"):
    resp = client.post("/api/v1/projects", headers=headers, json={
        "name": name,
        "description": "Project for testing images and visual assets",
        "initial_objective": "Test Visual Context OS features",
    })
    assert resp.status_code == 201
    return resp.json()["id"]


def make_image_bytes(image_format: str = "PNG", size: tuple = (120, 80), color: tuple = (70, 130, 180)) -> bytes:
    """Generate in-memory valid image bytes for tests."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format=image_format)
    return buf.getvalue()


# =============================================================================
# FORMAT & METADATA TESTS
# =============================================================================

def test_1_valid_png_upload(client):
    """1. Valid PNG upload creates record with 201 and correct format."""
    headers = register_user(client, "png_user@continuo.ai")
    proj_id = create_project(client, headers)
    png_data = make_image_bytes("PNG", size=(200, 150))

    files = {"file": ("screenshot.png", png_data, "image/png")}
    data = {
        "image_type": "ui_screenshot",
        "description": "Dashboard main layout reference",
        "visual_tags": "[\"dashboard\", \"dark_mode\", \"navigation\"]",
    }

    resp = client.post(f"/api/v1/projects/{proj_id}/images", headers=headers, files=files, data=data)
    assert resp.status_code == 201
    img = resp.json()
    assert img["image_format"] == "png"
    assert img["mime_type"] == "image/png"
    assert img["width"] == 200
    assert img["height"] == 150
    assert img["image_type"] == "ui_screenshot"
    assert img["visual_tags"] == ["dashboard", "dark_mode", "navigation"]
    assert img["project_id"] == proj_id


def test_2_valid_jpeg_upload(client):
    """2. Valid JPEG upload."""
    headers = register_user(client, "jpeg_user@continuo.ai")
    proj_id = create_project(client, headers)
    jpeg_data = make_image_bytes("JPEG", size=(320, 240))

    files = {"file": ("moodboard.jpg", jpeg_data, "image/jpeg")}
    data = {"image_type": "moodboard", "description": "Color scheme moodboard"}

    resp = client.post(f"/api/v1/projects/{proj_id}/images", headers=headers, files=files, data=data)
    assert resp.status_code == 201
    img = resp.json()
    assert img["image_format"] == "jpeg"
    assert img["mime_type"] == "image/jpeg"
    assert img["width"] == 320
    assert img["height"] == 240


def test_3_valid_webp_upload(client):
    """3. Valid WebP upload."""
    headers = register_user(client, "webp_user@continuo.ai")
    proj_id = create_project(client, headers)
    webp_data = make_image_bytes("WEBP", size=(400, 300))

    files = {"file": ("render.webp", webp_data, "image/webp")}
    data = {"image_type": "blender_render", "description": "3D asset render"}

    resp = client.post(f"/api/v1/projects/{proj_id}/images", headers=headers, files=files, data=data)
    assert resp.status_code == 201
    img = resp.json()
    assert img["image_format"] == "webp"
    assert img["mime_type"] == "image/webp"
    assert img["width"] == 400
    assert img["height"] == 300


def test_4_metadata_extraction(client):
    """4. Check metadata extraction (filename, file_size, file_url)."""
    headers = register_user(client, "metadata_ext_user@continuo.ai")
    proj_id = create_project(client, headers)
    raw_data = make_image_bytes("PNG", size=(64, 64))

    files = {"file": ("icon.png", raw_data, "image/png")}
    resp = client.post(f"/api/v1/projects/{proj_id}/images", headers=headers, files=files)
    assert resp.status_code == 201
    img = resp.json()

    assert img["original_filename"] == "icon.png"
    assert img["file_size"] == len(raw_data)
    assert img["file_url"].endswith(f"/images/{img['id']}/file")


def test_5_dimensions_extraction(client):
    """5. Check dimensions extraction (width, height)."""
    headers = register_user(client, "dimensions_user@continuo.ai")
    proj_id = create_project(client, headers)
    raw_data = make_image_bytes("PNG", size=(180, 95))

    files = {"file": ("dimension_test.png", raw_data, "image/png")}
    resp = client.post(f"/api/v1/projects/{proj_id}/images", headers=headers, files=files)
    assert resp.status_code == 201
    img = resp.json()

    assert img["width"] == 180
    assert img["height"] == 95


def test_6_checksum_generation(client):
    """6. Check SHA-256 checksum generation."""
    import hashlib

    headers = register_user(client, "checksum_user@continuo.ai")
    proj_id = create_project(client, headers)
    raw_data = make_image_bytes("PNG", size=(64, 64))
    expected_hash = hashlib.sha256(raw_data).hexdigest()

    files = {"file": ("checksum_test.png", raw_data, "image/png")}
    resp = client.post(f"/api/v1/projects/{proj_id}/images", headers=headers, files=files)
    assert resp.status_code == 201
    img = resp.json()

    assert img["checksum_sha256"] == expected_hash


# =============================================================================
# RETRIEVAL, FILE STREAMING, UPDATE & DELETION
# =============================================================================

def test_7_image_listing_and_filtering(client):
    """7. List images and filter by image_type."""
    headers = register_user(client, "lister_user@continuo.ai")
    proj_id = create_project(client, headers)

    # Upload 2 screenshot images and 1 diagram image
    for i in range(2):
        client.post(
            f"/api/v1/projects/{proj_id}/images",
            headers=headers,
            files={"file": (f"shot_{i}.png", make_image_bytes("PNG"), "image/png")},
            data={"image_type": "ui_screenshot"}
        )
    client.post(
        f"/api/v1/projects/{proj_id}/images",
        headers=headers,
        files={"file": ("arch.png", make_image_bytes("PNG"), "image/png")},
        data={"image_type": "diagram"}
    )

    # List all
    all_resp = client.get(f"/api/v1/projects/{proj_id}/images", headers=headers)
    assert all_resp.status_code == 200
    assert len(all_resp.json()) == 3

    # Filter by ui_screenshot
    shots_resp = client.get(f"/api/v1/projects/{proj_id}/images?image_type=ui_screenshot", headers=headers)
    assert shots_resp.status_code == 200
    assert len(shots_resp.json()) == 2
    assert all(x["image_type"] == "ui_screenshot" for x in shots_resp.json())

    # Filter by diagram
    diag_resp = client.get(f"/api/v1/projects/{proj_id}/images?image_type=diagram", headers=headers)
    assert diag_resp.status_code == 200
    assert len(diag_resp.json()) == 1


def test_8_image_metadata_retrieval(client):
    """8. Retrieve single image metadata by ID."""
    headers = register_user(client, "metadata_user@continuo.ai")
    proj_id = create_project(client, headers)

    created = client.post(
        f"/api/v1/projects/{proj_id}/images",
        headers=headers,
        files={"file": ("single.png", make_image_bytes("PNG"), "image/png")},
        data={"description": "Detailed inspection"}
    ).json()

    resp = client.get(f"/api/v1/projects/{proj_id}/images/{created['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]
    assert resp.json()["description"] == "Detailed inspection"


def test_9_protected_file_delivery(client):
    """9. Protected file delivery endpoint streams image with correct MIME and bytes."""
    headers = register_user(client, "stream_user@continuo.ai")
    proj_id = create_project(client, headers)
    raw_bytes = make_image_bytes("PNG", size=(80, 80))

    created = client.post(
        f"/api/v1/projects/{proj_id}/images",
        headers=headers,
        files={"file": ("deliverable.png", raw_bytes, "image/png")},
    ).json()

    file_resp = client.get(f"/api/v1/projects/{proj_id}/images/{created['id']}/file", headers=headers)
    assert file_resp.status_code == 200
    assert "image/png" in file_resp.headers["content-type"]
    assert file_resp.content == raw_bytes


def test_10_metadata_update(client):
    """10. Update image metadata (PATCH)."""
    headers = register_user(client, "patch_user@continuo.ai")
    proj_id = create_project(client, headers)

    created = client.post(
        f"/api/v1/projects/{proj_id}/images",
        headers=headers,
        files={"file": ("patchable.png", make_image_bytes("PNG"), "image/png")},
        data={"image_type": "other", "description": "Old description"}
    ).json()

    patch_resp = client.patch(f"/api/v1/projects/{proj_id}/images/{created['id']}", headers=headers, json={
        "image_type": "design_reference",
        "description": "Updated design reference description",
        "visual_tags": ["palette", "typography"],
    })
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["image_type"] == "design_reference"
    assert updated["description"] == "Updated design reference description"
    assert updated["visual_tags"] == ["palette", "typography"]


def test_11_image_deletion(client):
    """11. Delete image via API (204) and ensure subsequent GET returns 404."""
    headers = register_user(client, "delete_api_user@continuo.ai")
    proj_id = create_project(client, headers)

    created = client.post(
        f"/api/v1/projects/{proj_id}/images",
        headers=headers,
        files={"file": ("to_delete.png", make_image_bytes("PNG"), "image/png")},
    ).json()

    del_resp = client.delete(f"/api/v1/projects/{proj_id}/images/{created['id']}", headers=headers)
    assert del_resp.status_code == 204

    assert client.get(f"/api/v1/projects/{proj_id}/images/{created['id']}", headers=headers).status_code == 404


def test_12_local_file_deletion(client):
    """12. Ensure local file is removed from disk upon image deletion."""
    headers = register_user(client, "delete_disk_user@continuo.ai")
    proj_id = create_project(client, headers)

    created = client.post(
        f"/api/v1/projects/{proj_id}/images",
        headers=headers,
        files={"file": ("disk_delete.png", make_image_bytes("PNG"), "image/png")},
    ).json()

    storage = get_storage_provider()
    local_path = storage.get_path(created["storage_key"])
    assert local_path.is_file()

    client.delete(f"/api/v1/projects/{proj_id}/images/{created['id']}", headers=headers)
    assert not local_path.exists()


# =============================================================================
# VALIDATION & ATTACK DEFENSE TESTS
# =============================================================================

def test_13_invalid_magic_bytes(client):
    """13. Text file disguised as PNG is rejected with 422."""
    headers = register_user(client, "spoof_user_1@continuo.ai")
    proj_id = create_project(client, headers)

    fake_png = b"This is not a PNG file, just plain ASCII text."
    files = {"file": ("malicious.png", fake_png, "image/png")}

    resp = client.post(f"/api/v1/projects/{proj_id}/images", headers=headers, files=files)
    assert resp.status_code == 422
    assert "Unsupported or invalid image format" in resp.json()["detail"]


def test_14_mime_spoofing(client):
    """14. Non-image client Content-Type causes rejection."""
    headers = register_user(client, "spoof_user_2@continuo.ai")
    proj_id = create_project(client, headers)

    real_png = make_image_bytes("PNG")
    # Client sends application/x-executable or text/plain
    files = {"file": ("trojan.png", real_png, "application/octet-stream")}

    resp = client.post(f"/api/v1/projects/{proj_id}/images", headers=headers, files=files)
    assert resp.status_code == 422
    assert "does not match" in resp.json()["detail"]


def test_15_unsupported_format(client):
    """15. Unsupported format (e.g. GIF or random binary) rejected."""
    headers = register_user(client, "gif_user@continuo.ai")
    proj_id = create_project(client, headers)

    gif_header = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    files = {"file": ("animation.gif", gif_header, "image/gif")}

    resp = client.post(f"/api/v1/projects/{proj_id}/images", headers=headers, files=files)
    assert resp.status_code == 422
    assert "Unsupported or invalid image format" in resp.json()["detail"]


def test_16_oversized_upload(client, monkeypatch):
    """16. Upload exceeding maximum allowed size is rejected with 413."""
    headers = register_user(client, "oversized_user@continuo.ai")
    proj_id = create_project(client, headers)

    # Artificially set limit to 100 bytes for test
    from backend import config
    monkeypatch.setattr(config.settings, "MAX_UPLOAD_SIZE_BYTES", 100)

    png_data = make_image_bytes("PNG", size=(200, 200))
    assert len(png_data) > 100

    files = {"file": ("big.png", png_data, "image/png")}
    resp = client.post(f"/api/v1/projects/{proj_id}/images", headers=headers, files=files)
    assert resp.status_code == 413
    assert "exceeds maximum allowed size" in resp.json()["detail"]


def test_17_unsafe_filename_handling(client):
    """17. Filename with path traversal sequences is sanitized and never leaks to disk."""
    headers = register_user(client, "traversal_user@continuo.ai")
    proj_id = create_project(client, headers)

    png_data = make_image_bytes("PNG")
    files = {"file": ("../../../../etc/passwd.png", png_data, "image/png")}

    resp = client.post(f"/api/v1/projects/{proj_id}/images", headers=headers, files=files)
    assert resp.status_code == 201
    img = resp.json()
    assert img["original_filename"] == "passwd.png"
    assert ".." not in img["storage_key"]


def test_18_path_traversal_attempt(client):
    """18. Storage key with traversal rejected by StorageProvider."""
    storage = get_storage_provider()
    with pytest.raises(ValueError, match="Path traversal detected"):
        storage.get_path("projects/../etc/passwd")

    with pytest.raises(ValueError, match="Path traversal detected"):
        storage.get_path("projects/123/../../../secret.png")


def test_19_cross_user_access_rejection(client):
    """19. User B cannot read, update, or delete User A's images (403)."""
    headers_a = register_user(client, "owner_a_img@continuo.ai")
    headers_b = register_user(client, "intruder_b_img@continuo.ai")

    proj_a = create_project(client, headers_a)
    created = client.post(
        f"/api/v1/projects/{proj_a}/images",
        headers=headers_a,
        files={"file": ("private.png", make_image_bytes("PNG"), "image/png")}
    ).json()

    # User B GET metadata -> 403
    assert client.get(f"/api/v1/projects/{proj_a}/images/{created['id']}", headers=headers_b).status_code == 403
    # User B GET file -> 403
    assert client.get(f"/api/v1/projects/{proj_a}/images/{created['id']}/file", headers=headers_b).status_code == 403
    # User B PATCH -> 403
    assert client.patch(f"/api/v1/projects/{proj_a}/images/{created['id']}", headers=headers_b, json={"description": "Hacked"}).status_code == 403
    # User B DELETE -> 403
    assert client.delete(f"/api/v1/projects/{proj_a}/images/{created['id']}", headers=headers_b).status_code == 403


def test_20_cross_project_access_rejection(client):
    """20. Image from Project 1 requested via Project 2 returns 404."""
    headers = register_user(client, "dual_project_img@continuo.ai")
    proj_1 = create_project(client, headers, "Project 1")
    proj_2 = create_project(client, headers, "Project 2")

    created = client.post(
        f"/api/v1/projects/{proj_1}/images",
        headers=headers,
        files={"file": ("proj1.png", make_image_bytes("PNG"), "image/png")}
    ).json()

    # Query through Project 2
    assert client.get(f"/api/v1/projects/{proj_2}/images/{created['id']}", headers=headers).status_code == 404
    assert client.get(f"/api/v1/projects/{proj_2}/images/{created['id']}/file", headers=headers).status_code == 404
    assert client.patch(f"/api/v1/projects/{proj_2}/images/{created['id']}", headers=headers, json={"description": "X"}).status_code == 404
    assert client.delete(f"/api/v1/projects/{proj_2}/images/{created['id']}", headers=headers).status_code == 404


def test_21_unauthorized_file_delivery(client):
    """21. Unauthenticated file delivery yields 401."""
    resp = client.get("/api/v1/projects/random-proj/images/random-img/file")
    assert resp.status_code == 401


def test_22_invalid_image_type(client):
    """22. Unrecognized image_type rejected with 422."""
    headers = register_user(client, "type_validator@continuo.ai")
    proj_id = create_project(client, headers)

    files = {"file": ("valid.png", make_image_bytes("PNG"), "image/png")}
    resp = client.post(f"/api/v1/projects/{proj_id}/images", headers=headers, files=files, data={"image_type": "alien_format"})
    assert resp.status_code == 422


def test_23_invalid_context_association(client):
    """23. Referencing non-existent or foreign context ID rejected with 400."""
    headers = register_user(client, "bad_ctx_user@continuo.ai")
    proj_id = create_project(client, headers)

    files = {"file": ("ctx.png", make_image_bytes("PNG"), "image/png")}
    bad_ctx = client.post(
        f"/api/v1/projects/{proj_id}/images",
        headers=headers,
        files=files,
        data={"associated_context_ids": "[\"00000000-0000-0000-0000-000000000000\"]"}
    )
    assert bad_ctx.status_code == 400
    assert "Context does not exist" in bad_ctx.json()["detail"]


def test_24_invalid_decision_association(client):
    """24. Cross-project decision ID rejected with 400."""
    headers_1 = register_user(client, "assoc_user_1@continuo.ai")
    headers_2 = register_user(client, "assoc_user_2@continuo.ai")
    proj_1 = create_project(client, headers_1, "Proj 1")
    proj_2 = create_project(client, headers_2, "Proj 2")

    dec_proj_2 = client.post(f"/api/v1/projects/{proj_2}/decisions", headers=headers_2, json={"title": "Decision 2"}).json()

    files = {"file": ("assoc.png", make_image_bytes("PNG"), "image/png")}
    bad_dec = client.post(
        f"/api/v1/projects/{proj_1}/images",
        headers=headers_1,
        files=files,
        data={"associated_decision_ids": f"[\"{dec_proj_2['id']}\"]"}
    )
    assert bad_dec.status_code == 400
    assert "Decision does not belong to this project" in bad_dec.json()["detail"]


def test_25_invalid_source_session(client):
    """25. Invalid or foreign conversation session ID rejected with 400."""
    headers = register_user(client, "bad_sess_user@continuo.ai")
    proj_id = create_project(client, headers)

    files = {"file": ("sess.png", make_image_bytes("PNG"), "image/png")}
    bad_sess = client.post(
        f"/api/v1/projects/{proj_id}/images",
        headers=headers,
        files=files,
        data={"associated_session_id": "00000000-0000-0000-0000-000000000000"}
    )
    assert bad_sess.status_code == 400
    assert "Conversation session does not exist" in bad_sess.json()["detail"]


def test_26_project_deletion_cleanup(client):
    """26. Deleting a project purges its ContextImage records and physical files from storage."""
    headers = register_user(client, "purge_user@continuo.ai")
    proj_id = create_project(client, headers)

    img = client.post(
        f"/api/v1/projects/{proj_id}/images",
        headers=headers,
        files={"file": ("asset.png", make_image_bytes("PNG"), "image/png")}
    ).json()

    storage = get_storage_provider()
    file_path = storage.get_path(img["storage_key"])
    assert file_path.is_file()

    # Delete project
    del_proj = client.delete(f"/api/v1/projects/{proj_id}", headers=headers)
    assert del_proj.status_code == 204

    # File on disk should be removed
    assert not file_path.exists()


def test_27_storage_provider_path_containment(tmp_path):
    """27. LocalStorageProvider enforces containment within root directory."""
    provider = LocalStorageProvider(root_dir=str(tmp_path))

    # Valid save & get
    key = provider.save("proj-test", "file-123", "png", io.BytesIO(b"data"))
    assert provider.exists(key)
    path = provider.get_path(key)
    assert path.is_file()

    # Reject absolute paths
    with pytest.raises(ValueError, match="Absolute paths or drive letters forbidden"):
        provider.get_path("/etc/shadow")

    # Reject traversal
    with pytest.raises(ValueError, match="Path traversal detected"):
        provider.get_path("projects/../root.txt")


def test_28_missing_local_file_handling(client):
    """28. If file is deleted from disk externally, GET /file returns 404 without crashing."""
    headers = register_user(client, "missing_file_user@continuo.ai")
    proj_id = create_project(client, headers)

    created = client.post(
        f"/api/v1/projects/{proj_id}/images",
        headers=headers,
        files={"file": ("ghost.png", make_image_bytes("PNG"), "image/png")}
    ).json()

    storage = get_storage_provider()
    file_path = storage.get_path(created["storage_key"])
    assert file_path.is_file()

    # Remove file from disk directly
    file_path.unlink()
    assert not file_path.exists()

    # Delivery returns 404 cleanly
    resp = client.get(f"/api/v1/projects/{proj_id}/images/{created['id']}/file", headers=headers)
    assert resp.status_code == 404
    assert "not found on disk" in resp.json()["detail"]
