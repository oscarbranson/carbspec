from setuptools import setup, find_packages

from carbspec import __version__

setup(name='carbspec',
      version=__version__,
      description='Tools for calculating pH and Alkalinity from spectrophotometric data.',
      url='https://github.com/oscarbranson/carbspec',
      author='Oscar Branson',
      author_email='ob266@cam.ac.uk',
      license='MIT',
      packages=find_packages(),
      keywords=['science', 'chemistry', 'oceanography', 'carbon'],
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: Science/Research',
                   'Programming Language :: Python :: 3'],
      install_requires=['numpy',
                        'scipy',
                        'matplotlib',
                        'uncertainties'],
      include_package_data=True,
      package_data={'carbspec': ['resources/*']},
      zip_safe=True)
