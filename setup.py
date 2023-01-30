import os
from setuptools import setup, find_packages


NAME = 'djangae'
PACKAGES = find_packages()
DESCRIPTION = 'Django integration with Google App Engine'
URL = "https://github.com/potatolondon/djangae"
LONG_DESCRIPTION = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()
AUTHOR = 'Potato London Ltd.'

EXTRAS = {
    "test": ["beautifulsoup4"],
}

setup(
    name=NAME,
    version='2.0.0rc2',
    packages=PACKAGES,

    # metadata for upload to PyPI
    author=AUTHOR,
    author_email='mail@p.ota.to',
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    keywords=["django", "Google App Engine", "GAE"],
    url=URL,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.0',
        'Framework :: Django :: 3.1',
        'Framework :: Django :: 3.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],

    include_package_data=True,
    # dependencies
    install_requires=[
        'django>=2.2,<=3.3.0',
        'django-gcloud-connectors>=0.3.4',
        'google-api-python-client>=1.7.11',
        'google-cloud-tasks>=1.5.0,<2.0.0',
        'psutil>=5.7.3',
        # requests required by cloud storage file backend
        'requests>=2.22.0',
        # required for iap backend
        'cryptography==3.4.6',
        'python-jose[cryptography]==3.2.0',
    ],
    extras_require=EXTRAS,
    tests_require=EXTRAS['test'],
)
