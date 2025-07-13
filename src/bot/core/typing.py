from abc import ABC, abstractmethod

type Id = int
type Url = str


class ToModelMapper[TFrom, TTo](ABC):
    @abstractmethod
    def to_model(self, entity: TTo) -> TFrom: ...


class FromModelMapper[TFrom, TTo](ABC):
    @abstractmethod
    def from_model(self, model: TFrom) -> TTo: ...


class ModelMapper[TFrom, TTo](ToModelMapper[TFrom, TTo], FromModelMapper[TFrom, TTo], ABC):
    pass
