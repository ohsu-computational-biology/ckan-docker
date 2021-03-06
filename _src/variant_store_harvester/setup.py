from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
        name='ckanext-variantstore',
        version=version,
        description="Variant Store harvester for CKAN",
        long_description="""\
        """,
        classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        keywords='',
        author='Stefan Novak',
        author_email='novast@ohsu.edu',
        license='AGPL',
        packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
        namespace_packages=['ckanext', 'ckanext.variantstore'],
        include_package_data=True,
        zip_safe=False,
        install_requires=[
                # -*- Extra requirements: -*-
        ],
        entry_points=\
        """
            [ckan.plugins]
            variantstore_harvester=ckanext.variantstore.harvesters:VariantStoreHarvester
        """,
)
