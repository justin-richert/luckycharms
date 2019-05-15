"""
An extension of marshmallow for use with Flask apps.

Adds functionality to decorate business logic with schemas and automatically
validate, load, and render data with the defined schema.
"""
from setuptools import setup

setup(
    name='luckycharms',
    version='0.5.2',
    url='https://github.com/justin-richert/luckycharms',
    download_url='https://github.com/justin-richert/luckycharms/archive/0.5.1.zip',
    license='MIT',
    author='Justin Richert',
    author_email='justin.richert@life.church',
    description='An extension of marhsmallow for use with Flask apps.',
    long_description=__doc__,
    packages=['luckycharms'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask',
        'marshmallow==3.0.0b13'
    ],
    extras_require={
        'proto': 'protobuf'
    },
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    keywords=['flask', 'validation', 'marshmallow', 'rendering', 'api'],
    test_suite='tests',
)
