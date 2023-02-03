from relations import BinaryRelation, Relation, DerivedRelation

piotr = 'piotr'
kita = 'kita'
ania = 'ania'
karol = 'karol'
teresa = 'teresa'
robert = 'robert'
janina = 'janina'
henryk = 'henryk'
zdislaw = 'zdzisław'
lucyna = 'lucyna'

people = [piotr, kita, ania, karol, teresa, robert, janina, henryk, zdislaw, lucyna]
is_human = Relation('is_human', 1)
is_human.add(*people)

is_parent = BinaryRelation('is_parent')
is_parent.add(
	(teresa, piotr), (robert, piotr),
	(teresa, kita), (robert, kita),
	(teresa, ania), (robert, ania),
	(teresa, karol), (robert, karol),

	(janina, teresa), (henryk, teresa),
	(zdislaw, robert), (lucyna, robert),
)

is_female = Relation('is_female', 1)
is_female.add(ania, teresa, janina, lucyna)

# is_male = -is_female
# is_child = ~is_parent
# is_grandparent = is_parent * is_parent
# is_father = is_parent & is_male
#
# print(is_female.name, list(is_female.filter(people)))
# print(is_male.name, list(is_male.filter(people)))
# print()
# print(f'{teresa} is_parent {piotr}:', is_parent.is_matched_by(teresa, piotr))
# print(f'{piotr} is_parent {teresa}:', is_parent.is_matched_by(piotr, teresa))
# print(f'{teresa} is_father {ania}:', is_parent.is_matched_by(teresa, piotr))
# print(f'{robert} is_father {ania}:', is_parent.is_matched_by(robert, piotr))
# print()
# print(f'{piotr} is_child {teresa}:', is_child.is_matched_by(piotr, teresa))
# print(f'{janina} is_grandparent {karol}', is_grandparent.is_matched_by(janina, karol))

