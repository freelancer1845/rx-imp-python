from distutils.core import setup

"""
  python setup.py sdist
  twine upload dist/*

  to push new version
"""

setup(
  name = 'rximp',         # How you named your package folder (MyLib)
  packages = ['rximp'],   # Chose the same as "name"
  version = '0.1.4',      # Start with a small number and increase it with every change you make
  license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'Small library to overcome the "impediment" between RX worlds',   # Give a short description about your library
  author = 'Jascha Riedel',                   # Type in your name
  author_email = 'jaschelite@googlemail.com',      # Type in your E-Mail
  url = 'https://github.com/freelancer1845/rx-imp-python',   # Provide either the link to your github or to your website
  download_url = 'https://github.com/freelancer1845/rx-imp-python/archive/v_02.tar.gz',    # I explain this later on
  keywords = ['Reactive', 'ReactiveX', 'Rx', 'Interface', 'Network'],   # Keywords that define your package best
  install_requires=[            # I get to this in a second
          'rx',
          'uuid',
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
  ],
)

