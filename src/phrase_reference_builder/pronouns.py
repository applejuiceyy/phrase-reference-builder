import enum

from emoji import UNICODE_EMOJI_ENGLISH
from pydantic import BaseModel
import pydantic


class PronounType(enum.Enum):
    SENTINEL = enum.auto()
    NORMATIVE = enum.auto()
    KIND_OF_NORMATIVE = enum.auto()
    NEO_PRONOUN = enum.auto()
    NO_PRONOUN = enum.auto()
    EMOJI_PRONOUN = enum.auto()
    RUNTIME_PRONOUN = enum.auto()


class Pronoun(BaseModel):
    subject: str
    object: str
    possessive_determiner: str
    possessive_pronoun: str
    reflexive: str

    pronoun_type: PronounType
    person_class: int
    collective: bool

    @pydantic.validator("person_class")
    def validate_field(cls, v):
        if v not in range(1, 4):
            raise ValueError("person_class should be between 1 and 3")

        return v

    def __str__(self):
        if self.pronoun_type in (PronounType.NORMATIVE, PronounType.EMOJI_PRONOUN):
            return f"{self.subject}/{self.object}"

        elif self.pronoun_type == PronounType.NO_PRONOUN:
            return f"{self.subject}/{self.reflexive}"

        else:
            return "/".join(self.to_tuple())

    @classmethod
    def pronounless(cls, name):
        b = f"{name}'s"
        return cls(subject=name,
                   object=name,
                   possessive_determiner=b,
                   possessive_pronoun=b,
                   reflexive=f"{name}self",
                   pronoun_type=PronounType.NO_PRONOUN,
                   person_class=3,
                   collective=False)

    @classmethod
    def get_morpheme_names(cls):
        return "subject", "object", "possessive_determiner", "possessive_pronoun", "reflexive"

    def to_tuple(self):
        return self.subject, self.object, self.possessive_determiner, self.possessive_pronoun, self.reflexive

    @classmethod
    def from_tuple(cls, *args: str, pronoun_type, person_class, collective):
        return cls(subject=args[0],
                   object=args[1],
                   possessive_determiner=args[2],
                   possessive_pronoun=args[3],
                   reflexive=args[4],
                   pronoun_type=pronoun_type,
                   person_class=person_class,
                   collective=collective)

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))


class PronounRepository:
    main_pronouns = {
        Pronoun.from_tuple("he", "him", "his", "his", "himself",
                           pronoun_type=PronounType.NORMATIVE, person_class=3, collective=False),

        Pronoun.from_tuple("she", "her", "her", "hers", "herself",
                           pronoun_type=PronounType.NORMATIVE, person_class=3, collective=False),

        Pronoun.from_tuple("they", "them", "their", "theirs", "themself",
                           pronoun_type=PronounType.NORMATIVE, person_class=3, collective=False),

        Pronoun.from_tuple("they", "them", "their", "theirs", "themselves",
                           pronoun_type=PronounType.NORMATIVE, person_class=3, collective=True),

        Pronoun.from_tuple("it", "it", "it's", "it's", "itself",
                           pronoun_type=PronounType.KIND_OF_NORMATIVE, person_class=3, collective=False),

        Pronoun.from_tuple("I", "me", "my", "mine", "myself",
                           pronoun_type=PronounType.SENTINEL, person_class=1, collective=False),

        Pronoun.from_tuple("we", "us", "our", "ours", "ourselves",
                           pronoun_type=PronounType.SENTINEL, person_class=1, collective=True),

        Pronoun.from_tuple("you", "you", "your", "yours", "yourself",
                           pronoun_type=PronounType.SENTINEL, person_class=2, collective=False),

        Pronoun.from_tuple("you", "you", "your", "yours", "yourself",
                           pronoun_type=PronounType.SENTINEL, person_class=2, collective=True)
    }

    default: Pronoun
    default_collective: Pronoun

    self: Pronoun
    self_collective: Pronoun

    listener: Pronoun
    listener_collective: Pronoun

    def __init__(self):
        self.custom_pronouns = set()

    @classmethod
    def find_main_pronoun(cls, morpheme, *, collective=None, person_class=None):
        for pronoun in cls.main_pronouns:
            if collective is not None and collective != pronoun.collective:
                continue

            if person_class is not None and person_class != pronoun.person_class:
                continue

            if morpheme in pronoun.to_tuple():
                return pronoun

    def find_pronoun(self, morpheme, *, collective=None, person_class=None):
        maybe_pronoun = self.find_main_pronoun(morpheme, collective=None, person_class=None)

        if maybe_pronoun is not None:
            return maybe_pronoun

        for pronoun in self.custom_pronouns:
            if collective is not None and collective != pronoun.collective:
                continue

            if person_class is not None and person_class != pronoun.person_class:
                continue

            if morpheme in pronoun.to_tuple():
                return pronoun

    async def figure_pronoun_from_string(self, name: str, pronoun_str: str):
        if "/" in pronoun_str:
            chunks = [chunk.lower() for chunk in pronoun_str]

            if len(chunks) == 5:
                return Pronoun.from_tuple(*chunks,
                                          pronoun_type=PronounType.NEO_PRONOUN, person_class=3,
                                          collective=False)

            elif len(chunks) == 3:
                return Pronoun.from_tuple(chunks[0], chunks[0], chunks[1], chunks[1], chunks[2],
                                          pronoun_type=PronounType.NEO_PRONOUN, person_class=3,
                                          collective=False)

            elif len(chunks) == 2:
                if chunks[1].endswith("self"):
                    # probably a name of some sort
                    return Pronoun.pronounless(chunks[0])

                elif chunks[0] == chunks[1] and chunks[0] in UNICODE_EMOJI_ENGLISH:
                    # probably an emoji pronoun
                    pronoun = Pronoun.pronounless(chunks[0])
                    pronoun.pronoun_type = PronounType.EMOJI_PRONOUN
                    return pronoun

            # all conventional ways of getting this pronoun have failed
            # go the hard way

            for chunk in chunks:
                pronoun = await self.find_pronoun(chunk)

                if pronoun is not None:
                    return pronoun

        elif pronoun_str in ("nameself", "pronounless"):
            return Pronoun.pronounless(name)


PronounRepository.default = PronounRepository.find_main_pronoun("they", collective=False)
PronounRepository.collective = PronounRepository.find_main_pronoun("they", collective=True)

PronounRepository.self = PronounRepository.find_main_pronoun("I")
PronounRepository.self_collective = PronounRepository.find_main_pronoun("we")

PronounRepository.listener = PronounRepository.find_main_pronoun("you", collective=False)
PronounRepository.listener_collective = PronounRepository.find_main_pronoun("you", collective=True)

default_repository = PronounRepository()
