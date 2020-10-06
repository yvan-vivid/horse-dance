from pathlib import PurePath, Path

from horse_dance.mime_types import MimeType
from horse_dance.mime_resolver import (
    MimeResolver, Matched, Inode, Extensionless, Substitute,
    CorrectText, CorrectBinary, CorrectFormat
)

_mime_file_cases = Path(__file__).parent / "mime_file_cases"

MimeType.initialize(dict(
    ext_optional=("text/plain", "text/x-shellscript"),
))

_config = dict(
    substitutions=(
        dict(file="video/abc", name="video/def", resolution="video/xyz"),
    ),
    binary_types=("image",),
    media_correction=("image/target",),
)


def test_resolve_mimes():
    mime_resolver = MimeResolver(_config)
    for n, f, r, m in (
        ("audio/wav", "audio/wav", "audio/wav", Matched),
        ("text/plain", "inode/directory", "inode/directory", Inode),
        ("image/approx", "image/target", "image/target", CorrectFormat),
        ("text/javascript", "text/plain", "text/javascript", CorrectText),
        ("video/def", "video/abc", "video/xyz", Substitute),
    ):
        mimes = mime_resolver.resolve(MimeType.of_str(f), MimeType.of_str(n))
        assert mimes.resolved == m(MimeType.of_str(r))

    assert (
        mime_resolver.resolve(MimeType.Binary, MimeType.of_str("image/jpeg")).resolved
        == CorrectBinary(MimeType.of_str("image/jpeg"))
    )

    assert (
        mime_resolver.resolve(MimeType.PlainText, MimeType.Extensionless).resolved
        == Extensionless(MimeType.PlainText)
    )

    assert (
        mime_resolver.resolve(MimeType.PlainText, MimeType.Binary).resolved is None
    )


def test_resolve_path():
    mime_resolver = MimeResolver(_config)
    rp = mime_resolver.resolve_path
    assert rp(_mime_file_cases).resolved == Inode(MimeType.Dir)
    assert rp(_mime_file_cases / "empty").resolved == Inode(MimeType.Empty)
    assert (
        rp(_mime_file_cases / "runme").resolved
        == Extensionless(MimeType.of_str("text/x-shellscript"))
    )
    assert (
        rp(_mime_file_cases / "sample.jpg").resolved
        == Matched(MimeType.of_str("image/jpeg"))
    )
    assert (
        rp(_mime_file_cases / "sample.mp3").resolved
        == Matched(MimeType.of_str("audio/mpeg"))
    )
