# luckycharms
[![Build Status](https://travis-ci.org/justin-richert/luckycharms.svg?branch=master)](https://travis-ci.org/justin-richert/luckycharms)
[![Coverage Status](https://coveralls.io/repos/github/justin-richert/luckycharms/badge.svg)](https://coveralls.io/github/justin-richert/luckycharms)

An extension of marshmallow for Flask

luckycharms is a small wrapper on top of [marshmallow](https://github.com/marshmallow-code/marshmallow) for python. This wrapper extends Schema class instances to give them the ability to decorate "business logic" portions of a web application. Prior to the execution of the function, luckycharms Schemas will validate the incoming request body or querystring based on the request method. Following execution of the function, luckycharms will render responses based on the schema.

luckycharms was built in a way that strives to work with APIs designed following [Google's API Design Guide](https://cloud.google.com/apis/design). Use of the terms **resource** and **collection** throughout documentation and code reflect the use of those terms in the design guide.

### Configuration
Configuration of the behavior of each schema class is controlled by defining a dictionary on the schema called config. luckycharms will respect the following keys in the config dictionary:
- **paged**: [`boolean`] - Whether or not collection responses should be paged. Default setting is True

- **ordering**: [`list`] - A list of 2-tuples where the first item is the field to sort by and the second item is a tuple containing accepted orderings (Ex. (desc, asc)). The first item in the tuple in the list will be used as defaults, where the first item in the accepted orderings list is the default. If not supplied, the querystring will not allow ordering information to be passed.

- **protobuffers**: [`dict`] - A dictionary containing the keys load, dump, load_many, and dump_many. These keys are used to deserialize (load) and serialize (dump) protobuffer data in the event that the Content-Type header is set to application/octet-stream. The keys that end in "many" are used if many=True is supplied when creating an instance of a schema. If not passed, protobuffer loading/rendering of the data will not be available.

- **querystring_schemas**: [`dict`] - A dictionary containing the keys load and load_many. These keys are used to deserialize and validate the querystring on a GET request. If not supplied, these schemas default to QuerystringResource and QuerystringCollection for the keys mentioned, respectively. QuerystringResource accepts and validates the parameter fields only which is used to indicate which fields are desired in the response. QuerystringCollection accepts and validates the parameters fields, page (if paging is set to True), order_by (which accepts any valid field name for the schema), and order (which accepts any valid order for that field, such as asc or desc).
Querystring schemas can be passed into 


### Example Use
```python
import db  # some ORM library
from luckycharms import BaseModelSchema, QuerystringResource, QuerystringCollection
from marshmallow import fields
from protobuffers import examples


class PersonDataModel(db.Model):
    """An ORM Model."""
    id = db.Serial()
    name = db.StringField()
    age = db.IntegerField()
    birthday = db.DateField()


class SpecialQuerystringResource(QuerystringResource):
    """An extension of the default QuerystringResource schema."""
    filter_by = fields.String()


class SpecialQuerystringCollection(QuerystringCollection):
    """An extension of the default QuerystringCollection schema."""
    filter_by = fields.String()


class PersonSchema(BaseModelSchema):
    """A resource model schema."""
    id = fields.Int()
    name = fields.String(required=True)
    age = fields.Int()
    birthday = fields.Date()

    class Meta:
        """Marshmallow Meta schema."""
        dump_only = ('id',)
        load_only = ('age',)

    # luckycharms config
    config = {
        'paged': True,
        'ordering': [
            ('age', ('desc', 'asc')),
            ('birthday', ('asc', 'desc'))
        ],
        'querystring_schemas': {
            'load': SpecialQuerystringResource,
            'load_many': SpecialQuerystringCollection
        },
        'protobuffers': {
            'load': examples.Example(),
            'dump': examples.Example(),
            'load_many': examples.Example(),
            'dump_many': examples.ExampleCollection()
        }
    }


# parameters provided by SpecialQuerystringCollection
@PersonSchema(many=True)  # Schema instantiation accepts all params documented by marshmallow.
def business_logic(page, page_size, order, order_by, fields, filter_by):
    """Example logic; not tested, specific to any ORM library, or intended for real use."""

    # No need to select specific fields in db query. Fields not requested will be removed during
    # rendering. This allows for caching of full models instead of all the combinations possible.
    # Pagination logic in schema is currently designed to receive page_size + 1 objects
    # if there is a following page to be able to inform the client if there is a next page.
    return PersonDataModel\
        .select() \
        .where(**filter_by) \
        .order_by(order_by, order) \
        .limit(page_size + 1) \
        .offset(page * page_size) \
        .execute()
```
