from setuptools import setup, find_packages

setup(name='carbspec',
      version='0.1.0a',
      description='Tools for calculating pH and Alkalinity from spectrophotometric data.',
      url='https://github.com/oscarbranson/carbspec',
      author='Oscar Branson',
      author_email='oscarbranson@gmail.com',
      license='MIT',
      packages=find_packages(),
      keywords=['science', 'chemistry', 'oceanography', 'carbon'],
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: Science/Research',
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 3'],
      install_requires=['numpy', 'scipy', 'matplotlib'],
      include_package_data=True,
      package_data={'swcalc': ['resources/*']},
      zip_safe=True)
