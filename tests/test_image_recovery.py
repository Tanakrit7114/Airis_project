import pytest
from app.images.generator import LocalImageGenerator


def test_release_after_failed_generation(tmp_path, monkeypatch):
    generator=LocalImageGenerator(output_dir=tmp_path)
    class Broken:
        def generate_image(self, **kwargs):
            raise RuntimeError("out of memory")
    monkeypatch.setattr(generator, "_load_model", lambda: Broken())
    released=[]
    monkeypatch.setattr(generator, "_release_model", lambda: released.append(True))
    with pytest.raises(RuntimeError):
        generator.generate("a cat")
    assert released == [True]


def test_aligned_image_saved(tmp_path, monkeypatch):
    from PIL import Image
    from types import SimpleNamespace
    generator=LocalImageGenerator(output_dir=tmp_path)
    class Fake:
        def generate_image(self, **kwargs):
            assert kwargs['width']==256 and kwargs['height']==272
            return SimpleNamespace(image=Image.new("RGB",(256,272)))
    monkeypatch.setattr(generator, "_load_model", lambda: Fake())
    monkeypatch.setattr(generator, "_release_model", lambda: None)
    result=generator.generate("a cat",width=257,height=279)
    assert result['width']==256 and result['height']==272
    assert (tmp_path/result['filename']).is_file()
