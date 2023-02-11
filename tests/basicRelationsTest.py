from typing import Iterable

from parameterized import parameterized

from src.relations import Relation
from tests.abstractRelationsTest import AbstractRelationsTest


class BasicRelationsTest(AbstractRelationsTest):
	@classmethod
	def _get_test_name(cls) -> str:
		return 'Basic'

	@parameterized.expand([
		('binary', (('dad', 'son'), ('mum', 'son'), ('grandma', 'mum'))),
		('unary_tupled', (('apple', ), ('orange', ), ('kiwi', ))),
	])
	def test_add(self, name, adds):
		arity = len(adds[0]) if isinstance(adds[0], Iterable) else 1
		rel = Relation(name, arity)
		rel.add(*adds)
		self.assertCountEqual(adds, rel.set)

	def test_add_unary_single(self):
		adds = 'apple', 'orange', 'kiwi'
		rel = Relation('unary_sinhle', 1)
		rel.add(*adds)
		self.assertCountEqual(map(lambda a: (a, ), adds), rel.set)

	@parameterized.expand([
		('binary', (('dad', 'son'), ('mum', 'son'), ('grandma', 'mum')), ('mum', 'son')),
		('unary', (('apple', ), ('orange', ), ('kiwi', )), ('kiwi', )),
	])
	def test_match(self, name, to_adds: tuple, to_match: tuple[str]):
		arity = len(to_adds[0])
		rel = Relation(name, arity)
		rel.add(*to_adds)
		self.assertTrue(rel.is_matched_by(*to_match))
		self.assertTrue(to_match in rel)
