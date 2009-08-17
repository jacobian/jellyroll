import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "jellyroll",
    version = "1.0",
    url = 'http://github.com/jacobian/jellyroll',
    license = 'BSD',
    description = "You keep personal data in all sorts of places on the internets. Jellyroll brings them together onto your own site.",
    long_description = read('README.rst'),

    author = 'Jacob Kaplan-Moss',
    author_email = 'jacob@jacobian.org',

    packages = find_packages('src'),
    package_dir = {'': 'src'},
    
    install_requires = [
        'django-tagging==0.3pre',
        'Django>=1.0',
        'PIL',
        'python-dateutil',
        'pytz==2009e',
        'setuptools',
    ],
    dependency_links = ['http://pypi.pinaxproject.com/'],

    classifiers = [
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)