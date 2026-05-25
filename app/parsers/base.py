from abc import ABC, abstractmethod

from app.models.ir import Document


class ParseError(Exception):
    pass


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> Document:
        ...
