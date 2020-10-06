from horse_dance.mime_types import MimeType
from horse_dance.mime_resolver import MimeResolver
from horse_dance.normalizer import Normalizer
from pathlib import PurePath


config = dict(
    mime_types=dict(
        extras=(dict(mime="text/plain", ext="text"),),
        preferred_ext=(dict(mime="image/jpeg", ext="jpeg"),),
        ext_optional=("text/plain", "text/x-python", "text/x-shellscript"),
    ),

    normalizer=dict(
        ambiguous_stems=(
            dict(stem="image", suffix_digits=2),
            dict(stem="file",  suffix_digits=2),
        ),
        ambiguous_regs=(),
        path_root="/root/of",
    ),
)

def test__is_nondescript():
    normalizer = Normalizer(config.get('normalizer'))
    assert normalizer._is_nondescript("image")
    assert normalizer._is_nondescript("image-1")
    assert normalizer._is_nondescript("image-01")
    assert not normalizer._is_nondescript("image-012")
    assert not normalizer._is_nondescript("image-")
    assert not normalizer._is_nondescript("imager")


def test_slugger():
    norm = Normalizer(config.get('normalizer'))
    assert norm.slugger(PurePath("path/to/This  is. a file.abc")) == "this-is-a-file"
    assert norm.slugger(PurePath("path/--redundant--.abc")) == "redundant"
    assert norm.slugger(PurePath("part/path/image-5.abc")) == "image-5--part-path"
    assert norm.slugger(PurePath("part/path/05.abc")) == "05--part-path"
    assert norm.slugger(PurePath("part/path/re.abc")) == "re--part-path"
    assert norm.slugger(PurePath("/root/of/part/path/re.abc")) == "re--part-path"
    assert norm.slugger(PurePath("/root/of/path/re.abc")) == "re--path"


def test_normalize_name():
    MimeType.initialize(config.get('mime_types'))
    resolver = MimeResolver()
    normalizer = Normalizer(config.get('normalizer'))
    for p, n in (
        ("path/This is.file.jpg", "this-is-file.jpeg"),
        ("path/file-1.txt",       "file-1--path.txt"),
        ("path/image.jpg",        "image--path.jpeg"),
    ):
        path = PurePath(p)
        mimes = resolver.resolve_path(path)
        info = normalizer(path, mimes.resolved.mime)
        assert str(info.normalized_name) == n


def test_normalize_with_mime():
    MimeType.initialize(config.get('mime_types'))
    resolver = MimeResolver()
    normalizer = Normalizer(config.get('normalizer'))
    
    def test_n(p, m, n):
        mime = None if m is None else MimeType.of_str(m)
        fi = normalizer(PurePath(p), mime)
        name = None if fi.normalized_name is None else str(fi.normalized_name)
        assert name == n

    test_n("python-script", "text/x-python", "python-script")
    test_n("my-image.jpeg", "image/jpeg", "my-image.jpeg")
    test_n("my-image.jpg", "image/jpeg", "my-image.jpeg")
    test_n("my-image.gif", "image/jpeg", "my-image.jpeg")
    test_n("my-image", "image/jpeg", "my-image.jpeg")
    test_n("my-text-file.txt", "text/plain", "my-text-file.txt")
    test_n("my-text-file.text", "text/plain", "my-text-file.text")
    test_n("my-text-file.other", "text/plain", "my-text-file.txt")
    test_n("my-text-file", "text/plain", "my-text-file")
    test_n("my-text-file.other", "text/plain", "my-text-file.txt")
    test_n("my-unknown.other", "text/unknown", None)
    test_n("my-unknown.other", None, "my-unknown.other")
