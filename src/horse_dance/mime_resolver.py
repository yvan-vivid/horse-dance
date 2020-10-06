"""File type detection and extension correction via mime."""
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import Optional, Union, Tuple, Set, ClassVar
from enum import Enum, auto

from horse_dance.mime_types import MimeType


@dataclass(frozen=True)
class MimeResolution():
    mime: MimeType
    description: ClassVar[str]

    @staticmethod
    def resolve(res: 'MimeResolver', file_mime: MimeType, name_mime: MimeType) -> Optional[MimeType]:
        return NotImplemented

    @classmethod
    def resolution(
        cls, res: 'MimeResolver', file_mime: MimeType, name_mime: MimeType
    ) -> Optional['MimeResolution']:
        resolution = cls.resolve(res, file_mime, name_mime)
        return cls(resolution) if resolution is not None else None


@dataclass(frozen=True)
class NameOnly(MimeResolution):
    description = "using name only {name!s}"
    @staticmethod
    def resolve(res: 'MimeResolver', file_mime: MimeType, name_mime: MimeType) -> Optional[MimeType]:
        return name_mime


@dataclass(frozen=True)
class Matched(MimeResolution):
    description = "matched on {file!s}"
    @staticmethod
    def resolve(res: 'MimeResolver', file_mime: MimeType, name_mime: MimeType) -> Optional[MimeType]:
        return file_mime if file_mime == name_mime else None


@dataclass(frozen=True)
class Inode(MimeResolution):
    description = "determined inode {file!s}"
    @staticmethod
    def resolve(res: 'MimeResolver', file_mime: MimeType, name_mime: MimeType) -> Optional[MimeType]:
        return file_mime if file_mime in MimeType.Inodes else None


@dataclass(frozen=True)
class Extensionless(MimeResolution):
    description = "extensionless {file!s}"
    @staticmethod
    def resolve(res: 'MimeResolver', file_mime: MimeType, name_mime: MimeType) -> Optional[MimeType]:
        pred = file_mime in MimeType.ExtensionOptional and name_mime == MimeType.Extensionless
        return file_mime if pred else None

        
@dataclass(frozen=True)
class CorrectBinary(MimeResolution):
    description = "correcting binary to {name!s}"
    @staticmethod
    def resolve(res: 'MimeResolver', file_mime: MimeType, name_mime: MimeType) -> Optional[MimeType]:
        pred = file_mime == MimeType.Binary and (
            name_mime.type in res.binary_types or name_mime in res.binary_mimes
        )
        return name_mime if pred else None


@dataclass(frozen=True)
class CorrectText(MimeResolution):
    description = "correcting text from {file!s} to {name!s}"
    @staticmethod
    def resolve(res: 'MimeResolver', file_mime: MimeType, name_mime: MimeType) -> Optional[MimeType]:
        pred = name_mime.type == "text" and file_mime.type == "text"
        return name_mime if pred else None


@dataclass(frozen=True)
class Substitute(MimeResolution):
    description = "correcting {file!s} to {name!s} on substitution rule"
    @staticmethod
    def resolve(res: 'MimeResolver', file_mime: MimeType, name_mime: MimeType) -> Optional[MimeType]:
        mime = res.substitutions.get((file_mime, name_mime))
        return mime if mime is not None else None


@dataclass(frozen=True)
class CorrectFormat(MimeResolution):
    description = "correcting format {name!s} to {file!s}"
    @staticmethod
    def resolve(res: 'MimeResolver', file_mime: MimeType, name_mime: MimeType) -> Optional[MimeType]:
        pred = file_mime.type == name_mime.type and file_mime in res.media_correction
        return file_mime if pred else None


@dataclass(frozen=True)
class Mimes:
    file: MimeType
    name: MimeType
    resolved: Optional[MimeResolution] = None

    def describe_resolution(self) -> str:
        if self.resolved is None:
            return f"cannot resolve 'file={self.file}' 'name={self.name}'"
        return self.resolved.description.format(file=self.file, name=self.name)


class MimeResolver():
    resolvers = [
        Matched, Inode, Extensionless, CorrectBinary,
        CorrectText, Substitute, CorrectFormat
    ]

    def __init__(self, config: Optional[dict] = None):
        if config is None:
            config = {}
 
        self.substitutions = {
            tuple(
                map(MimeType.of_str, (subst["file"], subst["name"]))
            ): MimeType.of_str(subst["resolution"])
            for subst in config.get('substitutions', [])
        }

        def _config_set(tag):
            return frozenset(map(MimeType.of_str, config.get(tag, [])))

        self.binary_mimes = _config_set("binary_mimes")
        self.extensionless = _config_set("extensionless")
        self.media_correction = _config_set("media_correction")
        self.binary_types = frozenset(config.get("binary_types", []))

    def resolve(self, file_mime: MimeType, name_mime: MimeType) -> Mimes:
        for res in self.resolvers:
            m = res.resolution(self, file_mime, name_mime)
            if m is not None:
                return Mimes(file_mime, name_mime, m)
        return Mimes(file_mime, name_mime)

    def resolve_path(self, path: PurePath, ignore_file: bool = False) -> Mimes:
        name_mime = MimeType.of_name(path)
        
        if isinstance(path, Path) and not ignore_file:
            file_mime = MimeType.of_file(path)
            return self.resolve(file_mime, name_mime)

        return Mimes(MimeType.Unknown, name_mime, NameOnly(name_mime))
