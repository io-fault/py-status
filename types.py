"""
# Data structures for holding failure, notification, and trace information.

# [ Constructor Versioning ]

# The class methods of the types here are given version numbers. A version consists of
# a set of constructors. If a change is made to a structure that warrants a
# change to the constructors, a new version will be introduced with a new set of
# constructors leaving the old versions to fill in reasonable defaults. If no such
# default is possible, the set of old constructors will be removed entirely.

# The structures here are expected to be stable, so it is unlikely this practice
# will be employed.

# [ Engineering ]

# &Failure, &Report, and &Message are identical structures *except* the field names.
# This separation is inentional in order to make clear semantic distinctions and allow
# possible variations across the classes. Also, it is likely important to discourage
# processing instances using the same pipeline. While reporting endpoints may not
# care so much, the initial recipient of these objects should be expecting a
# particular type.
"""
import typing

# &.core and other local modules are not imported here in order to keep overhead low.
# It is desireable to be able to use these in annotations without importing I/O dependencies.

class EStruct(tuple):
	"""
	# Structure holding a snapshot of core information regarding an event that is likely to be
	# displayed to a user or emitted to a log. While this has been generalized to identify events,
	# it's name was chosen to lend to its suitability for errors.

	# While fields can be omitted, instances should contain as much information as possible.
	# &EStruct instances are snapshots that may be serialized prior to formatting, so
	# instances should be made with the consideration that the final endpoint may not
	# have access to more advanced formatting routines.
	"""
	__slots__ = ()

	def __repr__(self) -> str:
		if str(self.code) != self.identifier:
			return ("<[%s#%s:%d] %s: %r>" % self)
		else:
			return ("<[%s#%s] %s: %r>" % (self[0], self[1], self[3], self[4]))

	@property
	def protocol(self) -> str:
		"""
		# The URI or symbol identifying the set of events that this instance belongs to.
		# The authority specifying the semantics and metadata of the event.

		# If the URI is real, it should contain routing information that will
		# provide aid in properly formatting the event information. If the URI is not real,
		# the application processing the event should have formatting rules available.

		# Symbolic identifiers can be used, but should normally map to a URI
		# prior to serialization.

		# This field *must not* be localized.
		"""
		return self[0]

	@property
	def identifier(self) -> str:
		"""
		# A string unambiguously identifying the event.
		# Also recognized as the preferred string representation of &code that can identify the event.
		# Formally referred to as "String Identifier".

		# This must *not* be the symbolic name assigned to the &code.
		# For instance, the POSIX errno define `'EINTR'` should be considered a &symbol,
		# not an &identifier.

		# For events with integer identifiers, this is normally the decimal representation string.
		# If the &protocol commonly refers to a different representation for the &code,
		# then that string representation should used instead of the decimal string.

		# This field *must not* be localized.
		"""
		return self[1]

	@property
	def code(self) -> int:
		"""
		# The integer form of the &identifier or zero if none exists.
		# Formally referred to as "Integer Code".

		# Often, this is redundant with the &identifier field aside from the data type.

		# However, when the event's integer code is not normally presented or referenced to in
		# decimal form, the redundancy allows the use of the proper form without having
		# knowledge of the routine used to translate between the integer code and the usual
		# string representation. SQL state codes being a notable example where having
		# both forms might have some benefit during reporting.

		# A value of zero *should* indicate that there is no integer form;
		# normally, using the &identifier is the preferred key when
		# resolving additional metadata regarding the event.
		"""
		return self[2]

	@property
	def symbol(self) -> str:
		"""
		# The symbolic name, label, or title used to identify the event.

		# Often, a class name. This is distinct from &identifer and &code in that
		# it is usually how the &identifier was originally selected. For instance,
		# for a POSIX system error, errno, this might be `'EAGAIN'` or `'EINTR'`.

		# In cases where an error is being represented that has a formless &protocol,
		# the symbol may be the only field that can be used to identify the event.

		# This field *must not* be localized.
		"""
		return self[3]

	@property
	def abstract(self) -> str:
		"""
		# Single sentence message describing the event.
		# Often a constant string defined by the &protocol, but potentially
		# overridden by the application.

		# This field may be localized, but it is preferrable to use a consistent
		# language that is common to the majority of the application's users.

		# There is the potential that the &protocol can be used to resolve
		# a formatting routine for the display such that this message will not be shown.

		# This field should *not* contain formatting codes.
		# For high-level descriptions, the adapters implemented by a Reporting Pipeline
		# should be used to create friendlier, human-readable abstracts.
		"""
		return self[-1]

	@classmethod
	def from_fields_v1(Class,
			protocol:str,
			symbol:str='Unspecified',
			abstract:str="event snapshot created without abstract",
			identifier:str='',
			code:int=0,
		):
			return Class((protocol, identifier, code, symbol, abstract))

	@classmethod
	def from_tuple_v1(Class, fields):
		"""
		# Create an instance using &fields; expects five objects in this order:

		# # Protocol as a string.
		# # String Identifier.
		# # Integer Code.
		# # Symbol.
		# # Abstract Paragraph.
		"""
		return Class(fields[:5])

	@classmethod
	def from_arguments_v1(Class, protocol:str, identifier:str, code:int, symbol:str, abstract:str):
		"""
		# Create an instance using the given arguments whose positioning is consistent
		# with where the fields are stored in the tuple.
		"""
		return Class((protocol, identifier, code, symbol, abstract))

class Parameters(object):
	"""
	# A mutable finite-map whose values are associated with the typeform used by transports.

	# [ Properties ]
	# /Specification/
		# Class-level annotation signature for a fully-qualified parameter.
		# A tuple consisting of the necessary information for defining a parameter.

		# # Form, &.core.forms.
		# # Type, &.core.types.
		# # Key, &str identifier used for addressing the parameter.
		# # Value or Representation, &object.

	# [ Engineering ]

	# Currently &Parameters is being implemented with the perception of it being
	# a in-memory database. Aside from storage of simple values, there are, or will be, interfaces
	# for loading and storing fragmented objects such as tables, matrices, and structures.
	"""
	__slots__ = ('_storage',)

	# Form, Type, Key, Value
	Specification = typing.Tuple[str, str, str, str]

	# Mapping for set_parameters and others that detect the Parameter typeform.
	_python_builtins = {
		bool: 'boolean',
		int: 'integer',
		float: 'rational',
		str: 'string',
		bytes: 'octets',
		type(None): 'void',
		dict: 'parameters',
	}

	@classmethod
	def identify_object_typeform(Class, obj:object, type=type) -> str:
		"""
		# Select a form and type for the given object.
		"""

		# Fast Path
		if type(obj) in Class._python_builtins:
			return ('value', Class._python_builtins[type(obj)])

		first = None
		try:
			i = iter(obj)
			first = next(i)
		except StopIteration:
			raise ValueError("empty iterator cannot be used to identify parameter type")
		except Exception:
			# Probably not a collection.
			pass
		else:
			tf = Class.identify_object_typeform(first)
			assert tf[0] in ('value', 'representation',)

			# XXX: Ideally, use an ABC so registrations could be used.
			if isinstance(obj, set):
				return ('v-set', tf[1])
			else:
				return ('v-sequence', tf[1])

		# Cover subclass cases.
		for Type, stype in Class._python_builtins.items():
			if isinstance(obj, Type):
				return ('value', stype)

	def __init__(self, storage):
		self._storage = storage

	def iterspecs(self):
		"""
		# Emit &Specification items for all the contained parameters.
		"""
		for k, (t, v) in self._storage.items():
			yield t[0], t[1], k, v

	def __eq__(self, operand):
		return operand._storage == self._storage

	# Mapping Interfaces
	def __setitem__(self, key, value):
		self.set_parameter(key, value)

	def __getitem__(self, key):
		self.get_parameter(key)

	def update(self, pairiter):
		idtf = self.identify_object_typeform

		for k, v in pairiter:
			tf = idtf(v)
			self._storage[k] = (tf, v)

	def empty(self) -> bool:
		"""
		# Whether the instance has any parameters.
		"""
		return (not bool(self._storage))

	def list_parameters(self) -> typing.Iterable[str]:
		"""
		# The iterator of parameter names stored within the instance.
		"""
		return self._storage.keys()

	def select(self, keys:typing.Iterable[str]) -> typing.Iterable[object]:
		"""
		# Select the parameter values identified by &keys in the order produced.
		"""
		s = self._storage
		return (s[x][-1] for x in keys)

	def get_parameter(self, key:str) -> object:
		"""
		# Get the parameter identified by &key.

		# Represented values are *not* interpreted and only the subject is returned.
		"""
		return self._storage[key][-1]

	def set_parameter(self, key:str, value:object):
		"""
		# Set the parameter identified by &key to &value.
		# If the parameter already exists, it will be overwritten and its
		# typeform-value pair returned.

		# The given &value is checked by &identify_object_typeform in order
		# to select a suitable typeform for the parameter.
		"""
		tf = self.identify_object_typeform(value)

		last = self._storage.pop(key, None)
		self._storage[key] = (tf, value)

		return last

	def set_excluded(self, key:str, value:object):
		"""
		# Store an object in &self that will *not* be included in any transmission
		# of the parameters.

		# [ Engineering ]
		# ! TENTATIVE: subject may be removed.
		"""
		self._storage[key] = (('value', 'excluded'), value)

	def set_reference(self, key:str, target:str) -> str:
		"""
		# Configure the parameter identified with &key to refer to the parameter
		# identified with &target.

		# Returns the resolved target's type.
		"""

		t = self._storage[target][0][1]
		self._storage[key] = (('reference', t), target)
		return t

	def set_identifier(self, key:str, value:str):
		"""
		# Set the parameter as an identifier.
		"""
		self._storage[key] = (('value', 'identifier'), value)

	def set_system_file(self, key:str, value:object):
		"""
		# Set parameter as a system file.
		"""
		self._storage[key] = (('value', 'system-file-path'), value)

	def set_rvalue(self, type:str, key:str, value:str):
		"""
		# Set the parameter &key to &value identified as a
		# represented &type. Retrieving this parameter will always
		# give the represented form, but transports will likely
		# convert it to a value upon reception given that it's a
		# recognized type.

		# Primarily used to circumvent any conversion performed by
		# the serialization side of a transport.
		"""
		last = self._storage.pop(key, None)
		self._storage[key] = (('representation', type), str(value))

		return last

	def set_rset(self, type:str, key:str, strings:typing.Iterable[str], Collection=set):
		"""
		# Set the parameter identified by &key to a new &list
		# constructed from the &strings iteratable.

		# The parameter's type is set from &type and its form
		# constantly `'r-set'` identifying it as a set of
		# representation strings.
		"""
		self._storage[key] = (('r-set', type), Collection(strings))

	def set_rsequence(self, type:str, key:str, strings:typing.Iterable[str], Collection=list):
		"""
		# Set the parameter identified by &key to a new &list
		# constructed from the &strings iteratable.

		# The parameter's type is set from &type and its form
		# constantly `'r-sequence'` identifying it as a set of
		# representation strings.
		"""
		self._storage[key] = (('r-sequence', type), Collection(strings))

	@classmethod
	def from_nothing_v1(Class, Storage=dict):
		"""
		# Create an empty set of Parameters.
		"""
		return Class(Storage())

	@classmethod
	def from_pairs_v1(Class, iterpairs:typing.Iterable[typing.Tuple[str, object]]):
		"""
		# Create from a regular Python objects whose values imply the
		# snapshot type.
		"""

		tf = Class.identify_object_typeform
		return Class({k:(tf(v),v) for k,v in iterpairs})

	@classmethod
	def from_specification_v1(Class, iterspec:typing.Iterable[typing.Tuple[str,str,str,object]]):
		"""
		# Create from an iterable producing the exact storage specifications.
		# Likely used in cases where the present fields are constantly defined.
		"""

		return Class({k:((form,typ),v) for form,typ,k,v in iterspec})

class Trace(tuple):
	"""
	# A sequence of frame events identifying the exact cursor position of an interpreter.
	# Often associated with a &Failure instance's error using &Failure.f_parameters.

	# [ Engineering ]
	# Currently, this only contains the route stack and is essentially an envelope.
	# Future changes may add data fields, but it is unlikely and this will primarily
	# exist for interface purposes.
	"""
	__slots__ = ()

	@property
	def t_route(self) -> [(EStruct, Parameters)]:
		"""
		# The serializeable identification of the error's context.
		# A sequence of &EStruct instances associated with a snapshot of
		# relavent metadata.
		"""
		return self[0]

	@classmethod
	def from_events_v1(Class, events:[(EStruct, Parameters)]):
		"""
		# Typed constructor populating the primary field.
		"""
		return Class((events,))

	@classmethod
	def from_nothing_v1(Class):
		"""
		# Create Trace with no route points.
		"""
		return Class(([],))

class Failure(tuple):
	"""
	# Data structure referencing the &EStruct detailing the error that occurred causing
	# an Identified Operation to fail. The &f_parameters contains additional information
	# regarding the &f_error that occurred.
	"""
	__slots__ = ()

	@property
	def f_context(self) -> Trace:
		"""
		# The serializeable identification of the error's context.
		# A sequence of &EStruct instances associated with a snapshot of
		# relavent metadata.
		"""
		return self[-1]

	@property
	def f_error(self) -> EStruct:
		"""
		# The serializeable identification and information of the cause of the failure.
		"""
		return self[0]

	@property
	def f_parameters(self) -> Parameters:
		"""
		# The relevant parameters involved in the execution of the transaction.
		# Usually, these parameters should be restricted to those that help
		# illuminate the production of the &f_error.
		"""
		return self[1]

	@classmethod
	def from_arguments_v1(Class, errcontext, error:EStruct, **parameters):
		"""
		# Create using context and error positional parameters, and
		# error parameters from the given keywords.

		# Signature is identical to &Failure.from_arguments_v1 and &Message.from_arguments_v1.
		"""
		if errcontext is None:
			errcontext = Trace.from_nothing_v1()
		return Class((error, Parameters.from_pairs_v1(parameters.items()), errcontext))

class Message(tuple):
	"""
	# Message event associated with an origin context and additional parameters.
	"""
	__slots__ = ()

	@property
	def msg_context(self) -> Trace:
		"""
		# The context of the origin of the message.
		"""
		return self[-1]

	@property
	def msg_event(self) -> EStruct:
		"""
		# The event identifying the message.
		"""
		return self[0]

	@property
	def msg_parameters(self) -> Parameters:
		"""
		# Relevant message parameters.
		"""
		return self[1]

	@classmethod
	def from_arguments_v1(Class, msgctx, msgid:EStruct, **parameters):
		"""
		# Create message instance using positional arguments and parameters from keywords.

		# Signature is identical to &Failure.from_arguments_v1 and &Report.from_arguments_v1.
		"""
		if msgctx is None:
			msgctx = Trace.from_nothing_v1()
		return Class((msgid, Parameters.from_pairs_v1(parameters.items()), msgctx))

class Report(tuple):
	"""
	# Data structure referencing the &EStruct detailing the report that has been generated.
	# The report's contents resides within the &r_parameters.
	"""
	__slots__ = ()

	@property
	def r_context(self) -> Trace:
		"""
		# The context of the origin of the message.
		"""
		return self[-1]

	@property
	def r_event(self) -> EStruct:
		"""
		# The event identifying the message.
		"""
		return self[0]

	@property
	def r_parameters(self) -> Parameters:
		"""
		# Relevant message parameters.
		"""
		return self[1]

	@classmethod
	def from_arguments_v1(Class, re_ctx, report_id:EStruct, **parameters):
		"""
		# Create report instance from arguments.
		# Signature is identical to &Failure.from_arguments_v1 and &Message.from_arguments_v1.
		"""
		if re_ctx is None:
			re_ctx = Trace.from_nothing_v1()
		return Class((report_id, Parameters.from_pairs_v1(parameters.items()), re_ctx))