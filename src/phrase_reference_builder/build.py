import abc
import typing
from pydantic import BaseModel
from . import pronouns


class _Fragment(abc.ABC):
    """Base class that allows addition for more straightforward templating"""

    @classmethod
    def _compute_add(cls, this, other):
        if not isinstance(this, _FragmentList):
            this = [this]

        if not isinstance(other, _FragmentList):
            other = [other]

        return _FragmentList([*this, *other])

    def __add__(self, other):
        return self._compute_add(self, other)

    def __radd__(self, other):
        return self._compute_add(other, self)


class _FragmentList(_Fragment, list):
    pass


class _Resolvable(abc.ABC):
    """Base class that resolves self to a string or another resolvable"""

    @abc.abstractmethod
    def resolve(self, context: "BuildingContext", self_idx: typing.Optional[int]):
        pass


class Entity(_Fragment, _Resolvable):
    @typing.overload
    def __init__(self, name: str, pronoun: pronouns.Pronoun):
        pass

    @typing.overload
    def __init__(self, id_: typing.Any, name: str, pronoun: pronouns.Pronoun):
        pass

    def __init__(self, *args):
        if len(args) == 2:
            args = [args[0], *args]
        self.id = args[0]

        self.name = args[1]
        self.pronounless = pronouns.Pronoun.pronounless(self.name)
        self.pronoun = args[2]

    def __eq__(self, other):
        return isinstance(other, Entity) and self.id == other.id

    def resolve(self, context: "BuildingContext", self_idx: typing.Optional[int]):
        from .types import Reference
        return Reference([self])

    def __getattr__(self, item):
        from .types import Reference
        return getattr(Reference([self]), item)


conversion_table = {}


class PhraseBuilder:
    def __init__(self, pronoun_repository=pronouns.default_repository):
        self.pronoun_repository = pronoun_repository
        self.referenced = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _identify_deferred_dict(self, dict_list):
        ret = {}

        for defer_name, defer_user in dict_list.items():
            ret[defer_name] = self.convert_to_entity_collection(defer_user)

        return ret

    def convert_to_entity_collection(self, users):
        if not isinstance(users, list):
            users = (users,)

        ret = []
        for user in users:
            if isinstance(user, Entity):
                ret.append(user)

            elif hasattr(user, "__entity__") and callable(user.__entity__):
                ret.append(user.__entity__(self))

            elif type(user) in conversion_table:
                ret.append(conversion_table[type(user)](self, user))

            elif hasattr(user, "name"):
                ret.append(Entity(id(user), user.name, self.pronoun_repository.find_pronoun("it", collective=False)))

            else:
                ret.append(Entity(id(user), str(user), self.pronoun_repository.find_pronoun("they", collective=False)))

        return ret

    def build(self, fragments: list, *, speaker=None, listener=None, author=None, deferred: typing.Dict = None):

        if deferred is None:
            deferred = {}
        else:
            deferred = self._identify_deferred_dict(deferred)

        if speaker is not None:
            speaker = self.convert_to_entity_collection(speaker)

        if listener is not None:
            listener = self.convert_to_entity_collection(listener)

        if author is not None:
            author = self.convert_to_entity_collection(author)

        context = BuildingContext(builder=self,
                                  building=[],
                                  speaker=speaker,
                                  listener=listener,
                                  author=author,
                                  deferred=deferred)

        for fragment in fragments:
            context.building.append([fragment])

        for idx, building_list in enumerate(context.building):
            while isinstance(building_list[-1], _Resolvable):
                building_list.append(building_list[-1].resolve(context, idx))

            if not isinstance(building_list[-1], str):
                raise RuntimeError(f"Bad Resolve: {type(building_list[-1])}")

        return "".join([ret[-1] for ret in context.building])


class BuildingContext(BaseModel):
    builder: PhraseBuilder

    building: typing.List[typing.List[typing.Union[_Resolvable, str]]]

    speaker: typing.Optional[typing.List[Entity]]
    listener: typing.Optional[typing.List[Entity]]
    author: typing.Optional[typing.List[Entity]]
    deferred: typing.Dict[str, typing.List[Entity]]

    class Config:
        arbitrary_types_allowed = True
