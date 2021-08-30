# Phrase Reference Builder

---
This is a package that transforms phrase templates with references into phrases with its respective pronouns

```py
from phrase_reference_builder.build import PhraseBuilder, Entity

builder = PhraseBuilder()
applejuice = Entity("Applejuice", builder.pronoun_repository.default)
print(builder.build(applejuice + "likes" + applejuice.pd + "bag"))
```
Output: `Applejuice likes their bag`

## Features:
### Deferring Entities
```python
from phrase_reference_builder.types import PersonClassDependent, DeferredReference
from phrase_reference_builder.build import PhraseBuilder, Entity

schrodinger_like = PersonClassDependent("like", "like", "likes")
victim = DeferredReference("victim")
template = victim + schrodinger_like + victim.possessive_determiner + "bag"


builder = PhraseBuilder()
applejuice = Entity("Applejuice", builder.pronoun_repository.default)
print(builder.build(applejuice + "likes" + applejuice.pd + "bag",
                    deferred={"victim": applejuice}))
```
Output: `Applejuice likes their bag`

### First and Second person pronouns
```py
from phrase_reference_builder.types import PersonClassDependent
from phrase_reference_builder.build import PhraseBuilder, Entity

builder = PhraseBuilder()

applejuice = Entity("Applejuice", builder.pronoun_repository.default)
schrodinger_like = PersonClassDependent("like", "like", "likes")

print(builder.build(applejuice + schrodinger_like + applejuice.pd + "bag"))
print(builder.build(applejuice + schrodinger_like + applejuice.pd + "bag", speaker=applejuice))
print(builder.build(applejuice + schrodinger_like + applejuice.pd + "bag", listener=applejuice))
```
Output:
```
Applejuice likes their bag
I like my bag
you like your bag
```

### Collectivity
```python
from phrase_reference_builder.build import PhraseBuilder, Entity
from phrase_reference_builder.types import Reference

builder = PhraseBuilder()
applejuice = Entity("Applejuice", builder.pronoun_repository.default)
grapejuice = Entity("Grapejuice", builder.pronoun_repository.default)

reference = Reference([applejuice, grapejuice])

print(builder.build(reference + "are fighting for the throne"))
```
Output: `Applejuice and Grapejuice are fighting for the throne`
### Custom Converters
```python
from phrase_reference_builder.build import PhraseBuilder, Entity
from phrase_reference_builder.types import PersonClassDependent, DeferredReference


class ConvertToApplejuicePlease:
    def __entity__(self, builder: PhraseBuilder):
        return Entity("Applejuice", builder.pronoun_repository.default)


builder = PhraseBuilder()

schrodinger_like = PersonClassDependent("like", "like", "likes")
victim = DeferredReference("victim")
template = victim + schrodinger_like + victim.possessive_determiner + "bag"

print(builder.build(template, deferred={"victim": ConvertToApplejuicePlease()}))
```
Output: `Applejuice likes their bag`