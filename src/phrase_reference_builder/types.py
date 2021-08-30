import typing

from . import pronouns
from .build import _Fragment, _Resolvable, Entity, BuildingContext


class _DeferredReferenceMorpheme(_Fragment, _Resolvable):
    def __init__(self, deferred_reference, morpheme):
        self.deferred_reference = deferred_reference
        self.morpheme = morpheme

    def resolve(self, context: "BuildingContext", self_idx):
        if self.deferred_reference.identifier in context.deferred:
            reference = Reference(context.deferred[self.deferred_reference.identifier])
            return _ReferenceMorpheme(reference, self.morpheme)

        else:
            raise RuntimeError(f"{self.deferred_reference.identifier} has no replacement")


class DeferredReference(_Fragment, _Resolvable):
    def __init__(self, identifier):
        self.identifier = identifier

    def resolve(self, context: "BuildingContext", self_idx):
        if self.identifier in context.deferred:
            return Reference(context.deferred[self.identifier])

        else:
            raise RuntimeError(f"{self.identifier} has no replacement")

    def __getattr__(self, item):
        return _DeferredReferenceMorpheme(self, item)


class _ReferenceMorpheme(_Fragment, _Resolvable):
    def __init__(self, reference, morpheme):
        self.reference: Reference = reference

        available_morphemes = pronouns.Pronoun.get_morpheme_names()
        if morpheme not in available_morphemes:
            for available_morpheme in available_morphemes:
                shorthand = ''.join([c for c in available_morpheme.replace("_", " ").title() if c.isupper()]).lower()
                if morpheme == shorthand:
                    morpheme = available_morpheme
                    break

        self.morpheme: str = morpheme

    def resolve(self, context: "BuildingContext", self_idx):
        person_class = 3

        if self.reference.collective and self.reference.users in context.builder.referenced:
            morpheme = self.morpheme

            if context.author is not None and context.author == self.reference.users and morpheme == "object":
                morpheme = "reflexive"

            pronoun = context.builder.pronoun_repository.collective
            collective = True
            person_class = 3

            if context.listener is not None and all(s in self.reference.users for s in context.listener):
                pronoun = context.builder.pronoun_repository.listener_collective
                person_class = pronoun.person_class

            elif context.speaker is not None and all(s in self.reference.users for s in context.speaker):
                pronoun = context.builder.pronoun_repository.self_collective
                person_class = pronoun.person_class

            baked_morpheme = getattr(pronoun, morpheme)
        else:
            list_baking = []

            for user in self.reference.users:
                person_class = 3

                if context.listener is not None and len(context.listener) == 1 and context.listener[0] == user:
                    pronoun = context.builder.pronoun_repository.listener
                    person_class = pronoun.person_class

                elif context.speaker is not None and len(context.speaker) == 1 and context.speaker[0] == user:
                    pronoun = context.builder.pronoun_repository.self
                    person_class = pronoun.person_class

                elif user in context.builder.referenced:
                    pronoun = user.pronoun

                else:
                    pronoun = user.pronounless
                    context.builder.referenced.append(user)

                morpheme = self.morpheme

                if (context.author is not None and len(context.author) == 1 and context.author[0] == user
                        and morpheme == "object"):
                    morpheme = "reflexive"

                list_baking.append(getattr(pronoun, morpheme))

            collective = False

            if self.reference.collective:
                context.builder.referenced.append(self.reference.users)
                collective = True

            baked_morpheme = human_join_list(list_baking)

        return _BakedPronoun(baked_morpheme, person_class, collective)


class Reference(_Fragment, _Resolvable):
    what = _ReferenceMorpheme

    def __init__(self, users: list):
        if not isinstance(users, list):
            users = [users]

        if len(users) == 0:
            raise ValueError("Empty reference")

        self.users: typing.List[Entity] = users
        self.collective = len(users) > 1

    def __getattr__(self, item):
        return _ReferenceMorpheme(self, item)

    def resolve(self, context: "BuildingContext", self_idx):
        return self.subject


class _BakedPronoun(_Fragment, _Resolvable):
    def __init__(self, morpheme, person_class: int, collective: bool):
        self.collective = collective
        self.person_class = person_class
        self.morpheme = morpheme

    def resolve(self, context: "BuildingContext", self_idx):
        return self.morpheme


class MaybeReflexive(_Fragment, _Resolvable):
    def __init__(self, author, target):
        self.author = author
        self.target = target

    def resolve(self, context: "BuildingContext", self_idx):
        author = self.author
        target = self.target

        while not isinstance(author, (Reference, _ReferenceMorpheme)):
            author = author.resolve(context, None)

        while not isinstance(target, (Reference, _ReferenceMorpheme)):
            target = target.resolve(context, None)

        if isinstance(author, _ReferenceMorpheme):
            author = author.reference

        if isinstance(target, _ReferenceMorpheme):
            target = target.reference

        old = context.author
        context.author = author.users
        ret = target.object.resolve(context, None)
        context.author = old
        return ret


class PersonClassDependent(_Fragment, _Resolvable):
    def __init__(self, *p_class):
        assert len(p_class) == 3

        self.p_class = p_class

    def resolve(self, context: "BuildingContext", self_idx: typing.Optional[int]):
        if self_idx is None:
            raise RuntimeError

        if self_idx == 0:
            raise RuntimeError

        for history in context.building[self_idx - 1]:
            if isinstance(history, _BakedPronoun):
                return self.p_class[history.person_class - 1]

        raise RuntimeError


def human_join_list(input_list: list, *, analyse_contents=False, end_join=" and "):
    if len(input_list) == 0:
        return ""
    elif len(input_list) == 1:
        return input_list[0]
    elif analyse_contents and end_join in input_list[-1]:
        return ", ".join(input_list)
    else:
        return end_join.join((", ".join(input_list[:-1]), input_list[-1]))


was = PersonClassDependent("was", "were", "was")
