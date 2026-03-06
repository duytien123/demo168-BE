from typing import TypeVar, Generic, Type

T = TypeVar("T")

class Singleton(Generic[T]):
    """
    参考:
    https://betterprogramming.pub/singleton-in-python-5eaa66618e3d
    """

    def __init__(self, cls: Type[T]) -> None:
        self._cls = cls

    def Instance(self):
        try:
            return self._instance
        except AttributeError:
            self._instance = self._cls()
            return self._instance

    def __call__(self):
        raise TypeError("Singleton Class は Instance() メソッドで呼び出してください")

    def __instancecheck__(self, __instance) -> bool:
        return isinstance(__instance, self._cls)
