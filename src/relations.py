from __future__ import annotations

from abc import ABC, abstractmethod
from functools import reduce
from itertools import repeat, product
from typing import Iterable, Any, Callable

from more_itertools import unique_everseen, bucket
import operator as op

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

	def get_members(self) -> set:
		return self.set


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

	_all_relations: dict[int, list[Relation]] = {}

	def __init__(self, name: str = '', arity: int = 2,  **kwargs):
		super().__init__(name=name, arity=arity, **kwargs)
		self._save_relation(self)

	@classmethod
	def _save_relation(cls, relation: Relation):
		cls._all_relations.setdefault(relation.arity, []).append(relation)

	def add(self, *to_adds: Any):
		for to_add in to_adds:
			if not isinstance(to_add, tuple | list):
				to_add = (to_add, )
			self._set.add(to_add)

	def is_matched_by(self, *elems: Any) -> bool:
		if len(elems) != self.arity:
			return False
		if self.arity == 1:
			elems = tuple(elems)
		return elems in self.set

	def get_all_with_value_at(self, value: Any, n: int, from_set=None):
		from_set = from_set or self.set
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
		return DerivedRelation(self.name, relations=self, params=(args,))

	def __or__(self, relation) -> DerivedRelation:
		return UnionRelation(f'{self.name}_or_{relation.name}', relations=(self, relation))

	def __and__(self, relation) -> DerivedRelation:
		return IntersectionRelation(f'{self.name}_and_{relation.name}', relations=(self, relation))

	def __neg__(self) -> DerivedRelation:
		return ComplementRelation(f'not_{self.name}', relation=self)

	def __eq__(self, other):
		if not isinstance(other, Relation):
			return False
		return self.name == other.name and self.arity == other.arity


class DerivedRelation(Relation, ABC):
	def __init__(self, name, *, relations: Iterable[Relation], params: Iterable[tuple[int | str, ...]] = None, pred: Callable[[Iterable[Relation], Iterable[tuple]], bool] = None, **kwargs):
		self._relations = tuple(relations)
		self._params: list[tuple[str | int, ...]] = list(params or (tuple(range(relation.arity)) for relation in self._relations))
		self._correspondences_with_points = self._get_correspondences_with_point()
		self._pred = pred or self._predicate
		super().__init__(name=name, arity=len(self._correspondences_with_points), **kwargs)

	def _get_correspondences_with_point(self) -> dict[int, tuple[int, int]]:
		result = {}
		for relation_i, params in enumerate(self._params):
			for member_i, correspondence in enumerate(params):
				if isinstance(correspondence, int):
					result.setdefault(correspondence, []).append((relation_i, member_i))
		return result

	@classmethod
	@abstractmethod
	def _predicate(cls, relations: Iterable[Relation], layer: Iterable[tuple]) -> bool:
		raise NotImplementedError

	@property
	def set(self):
		if len(self._relations) > 1:
			raise NotImplementedError

		spaces = map(Relation.get_members, self._relations)
		right_values_spaces = self._filter_wrong_values_out(spaces)
		relations_members_layers = product(*list(right_values_spaces))
		corresponding_relations_members_layers = self._filter_not_corresponding_out(relations_members_layers)
		predicated = filter(self._pred, corresponding_relations_members_layers)
		reordered = self._reorder_params(predicated)
		return reordered

	def _filter_not_corresponding_out(self, relations_members_layers: Iterable[tuple[tuple]]) -> Iterable[tuple[tuple]]:
		return filter(self.has_correspondent_members_the_same, relations_members_layers)

	def has_correspondent_members_the_same(self, relations_members: tuple[tuple]) -> bool:
		for correspondence, points in self._correspondences_with_points.items():
			correspondent_members = map(lambda p: relations_members[p[0]][p[1]], points)
			is_same = len(set(correspondent_members)) == 1
			if not is_same:
				return False
		return True

	def _filter_wrong_values_out(self, spaces: Iterable[Iterable[tuple]]) -> Iterable[Iterable[tuple]]:
		return (self._filter_wrong_values_out_of_space(space, params) for space, params in zip(spaces, self._params))

	def _filter_wrong_values_out_of_space(self, space: Iterable[tuple], params: tuple) -> Iterable[tuple]:
		for param_i, param in enumerate(params):
			if isinstance(param, str) and param != '*':
				space = filter(lambda members: members[param_i] == param, space)
		return space

	def _reorder_params(self, space: Iterable[tuple]) -> Iterable[tuple]:
		lacking_count = len(self._correspondences_with_points)
		for members in space:
			reordered = [members[index] for index in self._correspondences_with_points.keys()]
			lacking = members[lacking_count+1:]
			yield tuple(reordered + lacking)


class UnionRelation(DerivedRelation):
	def __init__(self, name, *, relations: Iterable[Relation], params: Iterable[tuple[int | str, ...]] = None, **kwargs):
		super().__init__(name, relations=relations, params=params, **kwargs)

	@classmethod
	def _predicate(cls, relations: Iterable[Relation], layer: Iterable[tuple]) -> bool:
		return any((relation(members) for relation, members in zip(relations, layer)))


class IntersectionRelation(DerivedRelation):
	def __init__(self, name, *, relations: Iterable[Relation], params: Iterable[tuple[int | str, ...]] = None, **kwargs):
		super().__init__(name, relations=relations, params=params, **kwargs)

	@classmethod
	def _predicate(cls, relations: Iterable[Relation], layer: Iterable[tuple]) -> bool:
		return all((relation(members) for relation, members in zip(relations, layer)))


class ComplementRelation(DerivedRelation):
	def __init__(self, name, *, relation: Relation, params: tuple[int | str, ...] = None, **kwargs):
		super().__init__(name, relations=(relation, ), params=(params,) if params else None, **kwargs)

	@classmethod
	def _predicate(cls, relations: Iterable[Relation], layer: Iterable[tuple]) -> bool:
		relation, members = next(iter(relations)), next(iter(layer))
		return not relation(members)

	def set(self):
		relation = self._relations[0]
		rest = (rel.set for rel in Relation._all_relations[relation.arity] if rel != relation)
		return reduce(op.or_, rest) - relation.set


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

	def __mul__(self, relation):
		return CompositionRelation(f'{self.name}_x_and_x_{relation.name}', relations=(self, relation))

	def __invert__(self):
		return ConverseRelation(name=f'converse_of_{self.name}', relation=self)


class CompositionRelation(DerivedRelation, BinaryRelation):

	def __init__(self, name, *, relations: Iterable[Relation], **kwargs):
		super().__init__(name, relations=relations, params=((0, 1), (1, 2)), **kwargs)

	@classmethod
	def _predicate(cls, relations: Iterable[Relation], layer: Iterable[tuple]) -> bool:
		return all((relation(members) for relation, members in zip(relations, layer)))


class ConverseRelation(DerivedRelation, BinaryRelation):
	def __init__(self, name, *, relation: Relation, **kwargs):
		super().__init__(name, relations=(relation, ), params=(1, 0), **kwargs)

	@classmethod
	def _predicate(cls, relations: Iterable[Relation], layer: Iterable[tuple]) -> bool:
		return next(iter(layer)) in next(iter(relations))


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
