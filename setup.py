import setuptools

setuptools.setup(
    name='pulse',
    version='0.0.1',
    long_description='',
    author='GSA 18F, CDS-SNC',
    author_email='pulse@cio.gov, cds-snc@tbs-sct.gc.ca',
    url='https://github.com/cds-snc/pulse',
    packages=[
        'data',
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
    ],
    install_requires=[
        'cfenv==0.5.3',
        'flask==1.0.0',
        'gunicorn==19.6.0',
        'newrelic==2.100.0.84',
        'pyyaml>=4.2b1',
        'python-slugify==1.2.1',
        'tinydb==3.2.1',
        'ujson==1.35',
        'waitress==1.4.2',
        'flask-compress==1.4.0',
    ],
    extras_require={
        'development': [
            'mypy==0.590',
            'pylint==1.8.4',
            'pytest==3.5.0',
            'pytest-cov==2.5.1',
        ],
    },
)
