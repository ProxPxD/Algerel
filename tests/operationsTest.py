from typing import Callable

from parameterized import parameterized

from src.relations import Relation, BinaryRelation
from tests.abstractRelationsTest import AbstractRelationsTest


class OperationsTest(AbstractRelationsTest):
	@classmethod
	def _get_test_name(cls) -> str:
		return 'Operations'

	@parameterized.expand([
		('complement', lambda r: -r,
			['Antek', 'Bartosz', 'Krzysiek'],
			['Kasia', 'Basia', 'Asia'],
			Relation('is_female', 1, space=(('Kasia', ), ('Basia', ), ('Asia', ))),
		),
		('converse', lambda r: ~r,
			[('Karol', 'Aneta'), ('Karol', 'Grzegorz')],
			[('Aneta', 'Karol'), ('Grzegorz', 'Karol'), ('Karol', 'Ania'), ('Karol', 'Iza')],
			BinaryRelation('is_parent_of', space=(('Aneta', 'Karol'), ('Grzegorz', 'Karol'), ('Karol', 'Ania'), ('Karol', 'Iza'))),
		),
		('intersection', lambda r1, r2: r1 & r2,
			['plane'],
			['boat', 'bird'],
			Relation('is_vehicle', 1, space=('car', 'plane', 'train', 'boat')),
			Relation('has_wings', 1, space=('plane', 'bird', 'insect')),
		),
		('union', lambda r1, r2: r1 | r2,
			[(('Matt', 'Alice'), ('Jerry', 'Marry'), ('John', 'Kate'), ('Sean', 'Victoria'))],
			[('Alice', 'Matt'), ('Alice', ), ('Matt', )],
			Relation('is_boyfriend_of', 2, space=(('Matt', 'Alice'), ('Jerry', 'Marry'))),
			Relation('is_husband_of', 2, space=(('John', 'Kate'), ('Sean', 'Victoria'))),
		),
		('composition', lambda r1, r2: r1 * r2,
			[('Grzegorz', 'Ania')],
			[('Grzegorz', 'Karol'), ('Karol', 'Ania')],
			BinaryRelation('is_parent_of_1', space=(('Grzegorz', 'Karol'), ('Karol', 'Ania'))),
			BinaryRelation('is_parent_of_2', space=(('Grzegorz', 'Karol'), ('Karol', 'Ania'))),
		),
	])
	def test_no_args(self, name, operation: Callable[[Relation, ...], Relation], expected_to_match: list, expected_not_to_match, *relations):
		derived = operation(*relations)
		filtered_not_to_match = list(derived.filter(expected_not_to_match))

		for expected in expected_to_match:
			self.assertTrue(derived.is_matched_by(expected), f'{str(expected)} does not match yet should')
		self.assertEqual(len(filtered_not_to_match), 0, "Something that shouldn't match, matches")

	@parameterized.expand([
		('correspondence_in_the_same_relation_by_star', lambda is_parent_of, is_female: is_parent_of(0, '*'), 1,
		 	['Aniela', 'Wiktor'],
		 	['Stefan', 'Patrycja'],
		),
		('correspondence_in_the_same_relation_by_minus_one', lambda is_parent_of, is_female: is_parent_of(0, -1), 1,
		 	['Aniela', 'Wiktor'],
		 	['Stefan', 'Patrycja'],
		),
		('correspondence_in_the_same_relation', lambda is_parent_of, is_female: is_parent_of('A', 'A'), 1,
		 	['God'],
		 	['Stefan', 'Patrycja', 'Wiktor', 'Aniela'],
		),
		('correspondence_of_first', lambda is_parent_of, is_female: is_parent_of('A', 'B') & is_female('A'), 2,
			[('Aniela', 'Stefan'), ('Aniela', 'Patrycja')],
			[('Wiktor', 'Stefan'), ('Wiktor', 'Patrycja')],
		),
		('correspondence_of_second', lambda is_parent_of, is_female: is_parent_of('A', 'B') & is_female('B'), 2,
			[('Wiktor', 'Patrycja'), ('Aniela', 'Patrycja')],
			[('Wiktor', 'Stefan'), ('Aniela', 'Stefan')],
		),
		('corresponding_just_first', lambda is_parent_of, is_female: is_parent_of('A', '*') & is_female('A'), 1,
			['Aniela'],
			['Wiktor', 'Patrycja', 'Stefan'],
		),
		('corresponding_just_second', lambda is_parent_of, is_female: is_parent_of('*', 'B') & is_female('B'), 1,
		 	['Patrycja'],
			['Wiktor', 'Aniela', 'Stefan'],
		),
		('inorder_first_or', lambda is_parent_of, is_female: is_parent_of(0, 1) | is_female(0), 2,
		 	[('Wiktor', 'Stefan'), ('Aniela', 'Stefan'), ('Wiktor', 'Patrycja'), ('Aniela', 'Patrycja'),
			 ('Patrycja', 'Wiktor'), ('Patrycja', 'Aniela'), ('Patrycja', 'Stefan'), ('Patrycja', 'Patrycja'),
			 ('Aniela', 'Wiktor'), ('Aniela', 'Aniela'), ('Aniela', 'Stefan'), ('Aniela', 'Patrycja'),
			],
			[('Wiktor', 'Aniela'), ('Stefan', 'Wiktor'), ('Stefan', 'Aniela'), ('Stefan', 'Patrycja'), ('Wiktor', 'Wiktor'), ('Stefan', 'Stefan')],
		),
		('inorder_second_or', lambda is_parent_of, is_female: is_parent_of(0, 1) | is_female(1), 2,
		 	[('Wiktor', 'Stefan'), ('Aniela', 'Stefan'), ('Wiktor', 'Patrycja'), ('Aniela', 'Patrycja'),
			 ('Wiktor', 'Aniela'), ('Aniela', 'Aniela'), ('Stefan', 'Aniela'), ('Patrycja', 'Aniela'),
			 ('Wiktor', 'Patrycja'), ('Aniela', 'Patrycja'), ('Stefan', 'Patrycja'), ('Patrycja', 'Patrycja'),
			],
			[('Patrycja', 'Stefan'), ('Wiktor', 'Wiktor'), ('Stefan', 'Stefan'), ('Aniela', 'Wiktor'), ('Patrycja', 'Wiktor'), ('Stefan', 'Wiktor')],
		),  # Same as:							 			  is_parent_of(A0,1) & is_female(A0)
		('inorder_first_and', lambda is_parent_of, is_female: is_parent_of(0, 1) & is_female(0), 2,
		 	[('Aniela', 'Patrycja'), ('Aniela', 'Stefan')],
			[('Wiktor', 'Stefan'), ('Wiktor', 'Patrycja'), ('Patrycja', 'Aniela')],
		),   # Same as:							 			   is_parent_of(0,A1) & is_female(A0)
		('inorder_second_and', lambda is_parent_of, is_female: is_parent_of(0, 1) & is_female(1), 2,
		 	[('Wiktor', 'Patrycja'), ('Aniela', 'Patrycja')],
			[('Wiktor', 'Stefan'), ('Aniela', 'Stefan'), ('Patrycja', 'Aniela')],
		),
		('reversed_first_or', lambda is_parent_of, is_female: is_parent_of(1, 0) | is_female(1), 2,
			[('Stefan', 'Wiktor'), ('Stefan', 'Aniela'), ('Patrycja', 'Wiktor'), ('Patrycja', 'Aniela'),
			 ('Wiktor', 'Patrycja'), ('Aniela', 'Patrycja'), ('Stefan', 'Patrycja'), ('Patrycja', 'Patrycja'),
			 ('Wiktor', 'Aniela'), ('Aniela', 'Aniela'), ('Stefan', 'Aniela'), ('Patrycja', 'Aniela'),
			],
			[('Aniela', 'Wiktor'), ('Wiktor', 'Stefan'), ('Aniela', 'Stefan'), ('Patrycja', 'Stefan'), ('Wiktor', 'Wiktor'), ('Stefan', 'Stefan')],
		),
		('reversed_second_or', lambda is_parent_of, is_female: is_parent_of(1, 0) | is_female(0), 2,
			[('Stefan', 'Wiktor'), ('Stefan', 'Aniela'), ('Patrycja', 'Wiktor'), ('Patrycja', 'Aniela'),
			 ('Aniela', 'Wiktor'), ('Aniela', 'Aniela'), ('Aniela', 'Stefan'), ('Aniela', 'Patrycja'),
			 ('Patrycja', 'Wiktor'), ('Patrycja', 'Aniela'), ('Patrycja', 'Stefan'), ('Patrycja', 'Patrycja'),
			],
			[('Stefan', 'Patrycja'), ('Wiktor', 'Wiktor'), ('Stefan', 'Stefan'), ('Wiktor', 'Aniela'), ('Wiktor', 'Patrycja'), ('Wiktor', 'Stefan')],
		),
		('reversed_first_and', lambda is_parent_of, is_female: is_parent_of(1, 0) & is_female(1), 2,
		 	[('Patrycja', 'Aniela'), ('Stefan', 'Aniela')],
			[('Stefan', 'Wiktor'), ('Patrycja', 'Wiktor'), ('Aniela', 'Patrycja')],
		),
		('reversed_second_and', lambda is_parent_of, is_female: is_parent_of(1, 0) & is_female(0), 2,
		 	[('Patrycja', 'Wiktor'), ('Patrycja', 'Aniela')],
			[('Stefan', 'Wiktor'), ('Stefan', 'Aniela'), ('Aniela', 'Patrycja')],
		),  # TODO: tests of mixed order and correspondence
		('reversed_match_both_number_and', lambda is_parent_of, is_female: is_parent_of('A1', 'B0') & is_female('A1'), 2,
		 	[],
		    [],
		),
		('reversed_match_both_number_or', lambda is_parent_of, is_female: is_parent_of('A1', 'B0') | is_female('A1'), 2,
		 	[],
		    [],
		),
		('reversed_match_one_number_and', lambda is_parent_of, is_female: is_parent_of('A1', 'B0') & is_female('A'), 2,
		 	[],
		    [],
		),
		('reversed_match_one_number_or', lambda is_parent_of, is_female: is_parent_of('A1', 'B0') | is_female('A'), 2,
		 	[],
		    [],
		),
		('match_one_implicit', lambda is_parent_of, is_female: is_parent_of('A', 'B0') & is_female('B0'), 2,
		 	[],
		    [],
		),
		('match_zero_implicit', lambda is_parent_of, is_female: is_parent_of('A', 'B1') & is_female('B1'), 2,
		 	[],
		    [],
		),
	])
	def test_args(self, name, create_relation, e_arity, e_to_matches, e_not_to_matches):
		is_parent_of = BinaryRelation('is_parent', space=(('Wiktor', 'Stefan'), ('Aniela', 'Stefan'), ('Wiktor', 'Patrycja'), ('Aniela', 'Patrycja'),
														  ('God', 'God'))
		)
		is_female = Relation('is_female', 1, space=('Aniela', 'Patrycja'))
		derived: Relation = create_relation(is_parent_of, is_female)
		self.assertEqual(e_arity, derived.arity, f'Arity not expected, e{e_arity} != a{derived.arity}')
		for e_to_match in e_to_matches:
			self.assertTrue(e_to_match in derived)

		filtered_not_to_match = list(derived.filter(e_not_to_matches))
		self.assertEqual(0, len(filtered_not_to_match))
