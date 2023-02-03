from __future__ import annotations

from abc import ABC
from typing import Iterable, Any, Callable

from more_itertools import unique_everseen


class IName:

	def __init__(self, name: str, **kwargs):
		super().__init__(**kwargs)
		self._name: str = name

	@property
	def name(self) -> str:
		return self._name

	def get_name(self) -> str:
		return self._name


class ISet:
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._set = set()

	@property
	def set(self):
		return set(self._set)


class IArity:
	def __init__(self, arity, **kwargs):
		super().__init__(**kwargs)
		self._arity = arity

	@property
	def arity(self) -> int:
		return self._arity


class IIsMatchedBy(ABC):
	def is_matched_by(self, *elems: Any) -> bool:
		raise NotImplementedError

	def filter(self, elems: Iterable[Any]) -> Iterable[Any]:
		return filter(lambda elem: self.is_matched_by(elem), elems)


class Relation(IName, IIsMatchedBy, ISet, IArity):

	def __init__(self, name: str = '', arity: int = 2,  **kwargs):
		super().__init__(name=name, arity=arity, **kwargs)

	def add(self, *to_adds: Any):
		for to_add in to_adds:
			if not isinstance(to_add, tuple | list):
				to_add = (to_add, )
			self._set.add(to_add)

	def is_matched_by(self, *elems: Any) -> bool:
		if len(elems) != self.arity:
			return False
		if self.arity == 1:
			return tuple(elems) in map(tuple, self._set)
		return elems in self._set

	def get_all_with_value_at(self, value: Any, n: int, from_set=None):
		from_set = from_set or self._set
		return self.get_all_with_value_at_from(value, n, from_set)

	@classmethod
	def get_all_with_value_at_from(cls, value: Any, n: int, from_set):
		return filter(lambda t: t[n] == value, from_set)

	def __getitem__(self, elems):
		return elems in self._set

	def __contains__(self, elems) -> bool:
		return self.is_matched_by(*elems)

	def __call__(self, *args, **kwargs):
		if len(args) == self.arity and not any((isinstance(arg, int) or arg == '*' for arg in args)):
			return self.is_matched_by(*args)
		return DerivedRelation(self, *args)


	# def __or__(self, relation) -> RelationBuilder:
	# 	return UnionRelationBuilder(f'{self.name}_or_{relation.name}', self, relation)
	#
	# def __and__(self, relation) -> RelationBuilder:
	# 	return IntersectionRelation(f'{self.name}_and_{relation.name}', self, relation)
	#
	# def __neg__(self) -> RelationBuilder:
	# 	return ComplementRelation(f'not_{self.name}', self)


class DerivedRelation(Relation, ABC):
	def __init__(self, name, relations: Iterable[Relation], relations_args: list[tuple[int | str]], merge_op: Callable[[Iterable[set[tuple]]], set[tuple]] = None, **kwargs):
		self._relations = tuple(relations)
		self._relations_args: list[tuple[int | str]] = list(relations_args)
		self._param_indices = set(arg for args in self._relations_args for arg in args if isinstance(arg, int))
		self._merge_op = merge_op
		super().__init__(name=name, arity=len(self._param_indices), **kwargs)

	@property
	def set(self):
		if len(self._relations) > 1:
			raise NotImplementedError

		change_count_and_all_elems_pairs = (self._decrease_arity(relation.set, args) for relation, args in zip(self._relations, self._relations_args))
		# for index in self._param_indices:

		# TODO

		reordered = self._reorder_params(with_decreased_arity)
		return reordered

	def _decrease_arity(self, all_elems: Iterable[tuple], args: tuple[int | str, ...]) -> tuple[int, Iterable[tuple]]:
		change_count = 0
		for arg_i, arg in enumerate(args):
			i = arg_i - change_count
			if arg == '*':
				all_elems = self._get_without_ith_elem(all_elems, i)
				change_count += 1
			elif not isinstance(arg, int):
				all_elems = self._get_without_ith_elem_with_no_other_value(all_elems, i, arg)
				change_count += 1
		return change_count, all_elems

	def _get_without_ith_elem(self, all_elems: Iterable[tuple], i) -> Iterable[tuple]:
		return unique_everseen((tuple(elems[:i] + elems[i+1:]) for elems in all_elems))

	def _get_without_ith_elem_with_no_other_value(self, all_elems: Iterable[tuple], i, value) -> Iterable[tuple]:
		return unique_everseen((tuple(elems[:i] + elems[i+1:]) for elems in all_elems if elems[i] == value))

	def _reorder_params(self, all_elems: Iterable[tuple]) -> Iterable[tuple]:
		lacking_count = len(self._param_indices)
		for elems in all_elems:
			reordered = [elems[index] for index in self._param_indices]
			lacking = elems[lacking_count+1:]
			yield tuple(reordered + lacking)

# class UnionRelation(ComplexRelation):
#
# 	def __init__(self):
#
# 	def is_matched_by(self, *elems: Any) -> bool:
# 		return any(map(lambda r: r.is_matched_by(elems), self._relations))

#
# class IntersectionRelation(RelationBuilder):
# 	def is_matched_by(self, *elems: Any) -> bool:
# 		return all(map(lambda r: r.is_matched_by(elems), self._relations))
#
#
# class ComplementRelation(RelationBuilder):
# 	def is_matched_by(self, *elems: Any) -> bool:
# 		relation = self._relations[0]
# 		return elems not in relation.set


class IInduce(ABC):
	def __init__(self, inducive_condition: Callable[[Any, Any, set[tuple]], bool], **kwargs):
		super().__init__(**kwargs)
		self.inducive_condition = inducive_condition

	def induce(self, a, b, domain) -> bool:
		return self.inducive_condition(a, b, domain)


class State(ABC):
	def __init__(self, state: bool, **kwargs):
		super().__init__(**kwargs)
		self.state: bool = state

	def is_on(self) -> bool:
		return self.state

	def is_off(self) -> bool:
		return not self.is_on()


class Property(State, ABC):
	def __init__(self, state: bool, **kwargs):
		super().__init__(state=state, **kwargs)


class Reflexivity(Property, IInduce):
	def __init__(self, cond=False, **kwargs):
		super().__init__(state=cond, inducive_condition=lambda a, b, d: a == b, **kwargs)


class Irreflexivity(Property):
	def __init__(self, cond=False, **kwargs):
		super().__init__(state=cond, **kwargs)


class Symmetry(Property, IInduce):
	def __init__(self, cond=False, **kwargs):
		super().__init__(state=cond, inducive_condition=lambda a, b, d: (b, a) in d, **kwargs)


class Asymmetry(Property):
	def __init__(self, cond=False, **kwargs):
		super().__init__(state=cond, **kwargs)


class Transitivity(Property, IInduce):
	def __init__(self, cond=False, **kwargs):
		super().__init__(state=cond, inducive_condition=self.transitivity_condition, **kwargs)

	def transitivity_condition(self, a: Any, c: Any, domain: set[tuple]) -> bool:  # TODO: imlement yielding a similar tree in a relation
		searched = set()
		to_searches = set(map(lambda t: t[1], Relation.get_all_with_value_at_from(a, 0, domain)))
		while to_searches:
			all_further = set()
			for to_search in to_searches:
				further = set(map(lambda t: t[1], Relation.get_all_with_value_at_from(to_search, 0, domain))) & searched & to_searches
				if c in further:
					return True
				all_further |= further
			searched |= to_searches
			to_searches = all_further[:]
		return False


class ICanBeReflexive:
	def __init__(self, is_reflexive: bool = False, **kwargs):
		super().__init__(**kwargs)
		self.reflexivity = Reflexivity(is_reflexive)


class ICanBeIrreflexive:
	def __init__(self, is_irreflexive=False, **kwargs):
		super().__init__(**kwargs)
		self.irreflexivity = Irreflexivity(is_irreflexive)


class ICanBeSymmetric:
	def __init__(self, is_symmetric=False, **kwargs):
		super().__init__(**kwargs)
		self.symmetry = Symmetry(is_symmetric)


class ICanBeAsymmetric:
	def __init__(self, is_asymmetric=False, **kwargs):
		super().__init__(**kwargs)
		self.asymmetry = Asymmetry(is_asymmetric)


class ICanBeTransitive:
	def __init__(self, is_transitive=False, **kwargs):
		super().__init__(**kwargs)
		self.transitivity = Transitivity(is_transitive)


class ICanBeAll(ISet, ICanBeReflexive, ICanBeIrreflexive, ICanBeSymmetric, ICanBeAsymmetric, ICanBeTransitive):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)


class Restrictions(ICanBeAll):
	def can_be_reflexive(self):
		return self.irreflexivity.is_off()

	def can_be_irreflexive(self):
		return self.reflexivity.is_off()

	def can_be_symmetric(self):
		return self.asymmetry.is_off()

	def can_be_asymmetric(self):
		return self.symmetry.is_off()

	def can_be_antisymmetric(self):
		return not any(((b, a) in self._set for a, b in self._set))


class CanAll(ICanBeAll):
	def can_add(self, a, b):
		if self.irreflexivity.is_on():
			return a != b
		if self.asymmetry.is_on():
			return (b, a) not in self._set


class BinaryRelation(Relation, Restrictions, CanAll):
	def __init__(self, name: str = '', **kwargs):
		super().__init__(name=name, arity=2, **kwargs)
		self._inducive_properties: list[IInduce] = [self.reflexivity, self.symmetry, self.transitivity]

	def is_matched_by(self, a, b) -> bool:
		result = super().is_matched_by(a, b)
		if not result:
			result = self._induce(a, b)
		return result

	def _induce(self, a, b) -> bool:
		present_properties = filter(Property.is_on, self._inducive_properties)
		induction = map(lambda p: p.induce(a, b, self._set), present_properties)
		return any(induction)

	# def __mul__(self, relation):
	# 	return CompositionRelation(f'{self.name}_x_and_x_{relation.name}', self, relation)
	#
	# def __invert__(self):
	# 	return ConverseRelation(name=f'converse_of_{self.name}', relation=self)

#
# class CompositionRelation(RelationBuilder, BinaryRelation):
# 	def is_matched_by(self, a, c) -> bool:
# 		relation_1, relation_2 = self._relations
# 		a_bs = Relation.get_all_with_value_at_from(a, 0, relation_1.set)
# 		b_cs = Relation.get_all_with_value_at_from(c, 1, relation_2.set)
# 		return any((a_b[1] == b_c[0] for a_b, b_c in product(a_bs, b_cs)))
#
#
# class ConverseRelation(RelationBuilder, BinaryRelation):
#
# 	def __init__(self, name: str = '', relation=None):
# 		super().__init__(name, relation)
#
# 	def is_matched_by(self, a, b) -> bool:
# 		return self._relations[0].is_matched_by(b, a)


class RelationStorage:
	def __init__(self):
		self._relations: dict = {}

	@property
	def relations(self) -> dict:
		return self._relations

	def get_relation(self, name: str):
		return self.relations[name]

	def get_nary_relations(self, n: int) -> Iterable[Relation]:
		return filter(lambda r: r.arity == n, self._relations.values())
