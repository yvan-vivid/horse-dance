from pathlib import PurePath, Path

from src.horse_dance.mime_types import MimeType as MT

_mime_file_cases = Path(__file__).parent / "mime_file_cases"

_config = dict(
    extras=(
        dict(mime="text/custom", ext="custom"),
        dict(mime="text/custom", ext="cust"),
    ),
    preferred_ext=(
        dict(mime="image/jpeg", ext="jpeg"),
    ),
    ext_optional=(
        "text/plain",
    ),
)


def test_mime_type():
    MT.initialize(_config)
    assert MT("audio", "wav") == MT.of_str("audio/wav")
    assert MT("audio", "wav", "xz") == MT.of_str("audio/wav", "xz")
    assert MT() == MT.Unknown
    assert MT("_") == MT.Extensionless
    assert MT.PlainText in MT.ExtensionOptional


def test_extract_compression():
    MT.initialize(_config)
    for c in ("xz", "bz2", "gzip"):
        assert MT.Compressed[c].extract_compression() == c
    assert MT.Binary.extract_compression() is None


def test_name_detection():
    MT.initialize(_config)
    assert MT.of_name(PurePath("path/file")) == MT.Extensionless
    assert MT.of_name(PurePath("path/file.probably_unknown")) == MT.Unknown
    assert MT.of_name(PurePath("path/file.txt")) == MT.PlainText
    assert MT.of_name(PurePath("path/file.jpg")) == MT("image", "jpeg")
    assert MT.of_name(PurePath("path/file.py")) == MT("text", "x-python")
    assert MT.of_name(PurePath("file.custom")) == MT("text", "custom")
    assert MT.of_name(PurePath("file.cust")) == MT("text", "custom")
    assert MT.of_name(PurePath("file.other")) == MT.Unknown


def test_extensions():
    MT.initialize(_config)
    assert MT.Extensionless.extensions() == set()
    assert MT.Extensionless.extension() == None
    assert MT.PlainText.extensions() >= set(("txt",))
    assert MT.PlainText.extension() == "txt"
    assert MT("image", "jpeg").extensions() >= set(("jpg", "jpeg"))
    assert MT("image", "jpeg").extension() == "jpeg"
    assert MT("text", "custom").extensions() == set(("custom", "cust"))


def test_correct_extension():
    MT.initialize(_config)
    assert MT("image", "jpeg").correct_extension("abc") == "jpeg"
    assert MT("image", "jpeg").correct_extension("") == "jpeg"
    assert MT("image", "jpeg").correct_extension("jpg") == "jpeg"
    assert MT("text", "custom").correct_extension("txt") == "custom"
    assert MT("text", "custom").correct_extension("cust") == "cust"
    assert MT("text", "plain").correct_extension("txt") == "txt"
    assert MT("text", "plain").correct_extension("data") == "txt"
    assert MT("text", "plain").correct_extension("") == ""


def test_file_detection():
    MT.initialize(_config)
    assert MT.of_file(_mime_file_cases / "sample.jpg") == MT.of_str("image/jpeg")
    assert MT.of_file(_mime_file_cases / "sample.mp3") == MT.of_str("audio/mpeg")
    assert MT.of_file(_mime_file_cases / "sample.pdf") == MT.of_str("application/pdf")
    assert MT.of_file(_mime_file_cases / "sample.txt") == MT.PlainText
    assert MT.of_file(_mime_file_cases / "empty") == MT.Empty
    assert MT.of_file(_mime_file_cases / "text") == MT.PlainText
    assert MT.of_file(_mime_file_cases / "runme") == MT.of_str("text/x-shellscript")
    assert MT.of_file(_mime_file_cases) == MT.Dir
