# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: proto.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='proto.proto',
  package='luckycharms.proto.remote',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\x0bproto.proto\x12\x18luckycharms.proto.remote\"\'\n\x04Test\x12\t\n\x01\x61\x18\x01 \x01(\x05\x12\t\n\x01\x62\x18\x02 \x01(\t\x12\t\n\x01\x63\x18\x03 \x01(\x08\"e\n\x0eTestCollection\x12-\n\x05tests\x18\x01 \x03(\x0b\x32\x1e.luckycharms.proto.remote.Test\x12\x11\n\tpage_size\x18\x02 \x01(\x05\x12\x11\n\tnext_page\x18\x03 \x01(\x08\x62\x06proto3')
)




_TEST = _descriptor.Descriptor(
  name='Test',
  full_name='luckycharms.proto.remote.Test',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='a', full_name='luckycharms.proto.remote.Test.a', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='b', full_name='luckycharms.proto.remote.Test.b', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='c', full_name='luckycharms.proto.remote.Test.c', index=2,
      number=3, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=41,
  serialized_end=80,
)


_TESTCOLLECTION = _descriptor.Descriptor(
  name='TestCollection',
  full_name='luckycharms.proto.remote.TestCollection',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='tests', full_name='luckycharms.proto.remote.TestCollection.tests', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='page_size', full_name='luckycharms.proto.remote.TestCollection.page_size', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='next_page', full_name='luckycharms.proto.remote.TestCollection.next_page', index=2,
      number=3, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=82,
  serialized_end=183,
)

_TESTCOLLECTION.fields_by_name['tests'].message_type = _TEST
DESCRIPTOR.message_types_by_name['Test'] = _TEST
DESCRIPTOR.message_types_by_name['TestCollection'] = _TESTCOLLECTION
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Test = _reflection.GeneratedProtocolMessageType('Test', (_message.Message,), dict(
  DESCRIPTOR = _TEST,
  __module__ = 'proto_pb2'
  # @@protoc_insertion_point(class_scope:luckycharms.proto.remote.Test)
  ))
_sym_db.RegisterMessage(Test)

TestCollection = _reflection.GeneratedProtocolMessageType('TestCollection', (_message.Message,), dict(
  DESCRIPTOR = _TESTCOLLECTION,
  __module__ = 'proto_pb2'
  # @@protoc_insertion_point(class_scope:luckycharms.proto.remote.TestCollection)
  ))
_sym_db.RegisterMessage(TestCollection)


# @@protoc_insertion_point(module_scope)
