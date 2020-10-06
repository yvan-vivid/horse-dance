"""Normalizing filenames"""
from dataclasses import dataclass, field
from pathlib import Path, PurePath
from typing import Optional, Tuple, List
import re
import logging
import yaml

from slugify import slugify  # type: ignore

from horse_dance.mime_types import MimeType
from horse_dance.mime_resolver import Mimes, MimeResolver, Matched, Extensionless


def _stem_re_str(common_stem) -> str:
    re_str = common_stem['stem']
    suffix_digits = common_stem.get('suffix_digits')
    if suffix_digits is not None:
        re_str += f"(?:-?\\d{{1,{suffix_digits}}})?$"
    return re_str


@dataclass
class FileName:
    stem: str
    ext: str

    def __str__(self):
        if self.ext == "":
            return self.stem
        return f"{self.stem}.{self.ext}"

    @staticmethod
    def of_path(path: PurePath) -> 'FileName':
        return FileName(path.stem, path.suffix[1:])


@dataclass
class FileInfo:
    path: PurePath
    original_name: FileName
    normalized_name: Optional[FileName] = None
    raw_stem: Optional[str] = None


class Normalizer:
    resolver: MimeResolver
    non_descript_re: Optional[re.Pattern] = None
    path_root: Optional[PurePath] = None

    def __init__(self, config: Optional[dict] = None):
        if config is None:
            config = {}
        amb_regs = tuple(config.get('ambiguous_regs', ()))
        common_stems = tuple(map(_stem_re_str, config.get('ambiguous_stems', ())))
        reg_strs = common_stems + amb_regs
        if len(reg_strs) > 0:
            self.non_descript_re = re.compile("|".join(reg_strs))

        path_root = config.get("path_root")
        if path_root is not None:
            self.path_root = PurePath(path_root)
   
    def _make_slug(self, stem: str) -> str:
        return slugify(stem)

    def _is_nondescript(self, stem: str) -> bool:
        re_term = (
            False if self.non_descript_re is None
            else re.match(self.non_descript_re, stem) is not None
        )
        return len(stem) <= 3 or re_term

    def _disambiguate(self, stem: str, path: PurePath) -> str:
        if not self._is_nondescript(stem):
            return stem
        if self.path_root is not None and self.path_root in path.parents:
            path_to = path.parent.relative_to(self.path_root)
        else:
            path_to = path.parent
        suffix = slugify("-".join(path_to.parts))
        return f"{stem}--{suffix}"

    def slugger(self, path: PurePath) -> str:
        stem = self._make_slug(path.stem)
        return self._disambiguate(stem, path)

    def __call__(self, path: PurePath, mime: Optional[MimeType] = None) -> FileInfo:
        if mime is not None and mime.compression is not None:
            raise NotImplementedError()

        original_name = FileName.of_path(path) 
        raw_stem = self._make_slug(original_name.stem)
        new_stem = self._disambiguate(raw_stem, path)

        if mime is None:
            normalized_name = FileName(new_stem, original_name.ext)
            return FileInfo(path, original_name, normalized_name, raw_stem)

        ext = mime.correct_extension(original_name.ext)
        if ext is None:
            return FileInfo(path, original_name)

        normalized_name = FileName(new_stem, ext)
        return FileInfo(path, original_name, normalized_name, raw_stem)
