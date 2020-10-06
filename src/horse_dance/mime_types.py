"""File type detection and extension correction via mime."""
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import Optional, Union, Tuple, Set, ClassVar, FrozenSet
import mimetypes
import logging
from enum import Enum, auto

import magic  # type: ignore


@dataclass(frozen=True)
class MimeType:
    type: Optional[str] = None
    format: Optional[str] = None
    compression: Optional[str] = None

    preferred_ext: ClassVar[dict] = {}

    Dir: ClassVar['MimeType']
    Symlink: ClassVar['MimeType']
    Empty: ClassVar['MimeType']
    Unknown: ClassVar['MimeType']
    Binary: ClassVar['MimeType']
    Extensionless: ClassVar['MimeType']
    PlainText: ClassVar['MimeType']

    Inodes: ClassVar[FrozenSet['MimeType']]
    Compressed: ClassVar[dict]
    ExtensionOptional: ClassVar[FrozenSet['MimeType']]

    @classmethod
    def initialize(cls, config: Optional[dict] = None):
        if config is None:
            config = {}  # pragma: no cover

        mime_paths = config.get('paths', [])
        if 'path' in config:
            mime_paths.append(config['path'])
        for path in mime_paths:
            mimetypes.knownfiles.append(path)
        mimetypes.init()

        for extra in config.get('extras', []):
            mimetypes.add_type(extra["mime"], "." + extra["ext"])

        cls.preferred_ext = {
            MimeType.of_str(pref["mime"]): pref["ext"]
            for pref in config.get('preferred_ext', [])
        }

        cls.ExtensionOptional = frozenset({
            MimeType.of_str(exop)
            for exop in config.get('ext_optional', [])
        })

    @staticmethod
    def of_str(mime_str: Optional[str], compression: Optional[str] = None) -> 'MimeType':
        if mime_str is None or mime_str == "":
            return MimeType(compression=compression)

        parts = mime_str.split('/')
        mtype = parts[0]
        mformat = parts[1] if len(parts) > 1 else None
        return MimeType(mtype, mformat, compression)
    
    @classmethod
    def of_file(cls, path: Path, use_name_for_compressed=True) -> 'MimeType':
        if path.is_dir():
            return cls.Dir
        mime = cls.of_str(magic.from_file(str(path), mime=True))
        if not use_name_for_compressed:
            return mime
        compression = mime.extract_compression()
        if compression is None:
            return mime
        return cls.of_name(path)

    @classmethod
    def of_name(cls, path: PurePath) -> 'MimeType':
        if path.suffix == '':
            return cls.Extensionless
        mime = mimetypes.guess_type(str(path), strict=False)
        if mime is None:
            return cls.Unknown
        return cls.of_str(*mime)

    def __str__(self):
        comp_str = "" if self.compression is None else f"!{self.compression}"
        return f"{self.type}/{self.format}{comp_str}"

    def extract_compression(self) -> Optional[str]:
        return _compressed_from_mimes.get(self)

    def extensions(self) -> Set[str]:
        if self == self.Extensionless:
            return set()
        exlist = mimetypes.guess_all_extensions(str(self), strict=False)
        return set(ext[1:] for ext in exlist)

    def extension(self) -> Optional[str]:
        if self in self.preferred_ext:
            return self.preferred_ext[self]

        if self == self.Extensionless:
            return None

        ext = mimetypes.guess_extension(str(self), strict=False)
        return None if ext is None else ext[1:]

    def correct_extension(self, ext: str) -> Optional[str]:
        if self in self.preferred_ext:
            return self.preferred_ext[self]
        
        if ext == '' and (self in self.ExtensionOptional or self in self.Inodes):
            return ''

        if ext in self.extensions():
            return ext

        new_ext = mimetypes.guess_extension(str(self), strict=False)
        return None if new_ext is None else new_ext[1:]


# Filesystem MimeTypes
MimeType.Dir = MimeType("inode", "directory")
MimeType.Symlink = MimeType("inode", "symlink")
MimeType.Empty = MimeType("inode", "x-empty")
MimeType.Inodes = frozenset((MimeType.Dir, MimeType.Symlink, MimeType.Empty))

# Ambiguous MimeTypes
MimeType.Unknown = MimeType()
MimeType.Binary = MimeType("application", "octet-stream")
MimeType.Extensionless = MimeType("_")
MimeType.PlainText = MimeType("text", "plain")

MimeType.Compressed = {
    "xz"   : MimeType("application", "x-xz"),
    "bz2"  : MimeType("application", "x-bzip2"),
    "gzip" : MimeType("application", "gzip"),
}

_compressed_from_mimes = {v: k for k, v in MimeType.Compressed.items()}
