from pathlib import Path


def test_image_intent_detection():
    from app.server.ws_chat import is_image_request
    assert is_image_request("สร้างภาพ แมวบนดวงจันทร์")
    assert is_image_request("generate an image of a campus")
    assert not is_image_request("อธิบาย Machine Learning")


def test_image_generator_sanitizes_prompt(tmp_path: Path):
    from app.images.generator import LocalImageGenerator
    g = LocalImageGenerator(output_dir=str(tmp_path))
    assert g.sanitize_prompt("  hello   world ") == "hello world"
