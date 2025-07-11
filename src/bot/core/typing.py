from abc import ABC, abstractmethod

type Id = int
type Url = str


class Mapper[TFrom, TTo](ABC):
    @abstractmethod
    def from_model(self, model: TFrom) -> TTo: ...

    @abstractmethod
    def to_model(self, entity: TTo) -> TFrom: ...
