from setuptools.command.test import test as TestCommand
from setuptools import setup, find_packages
from pip.req import parse_requirements
import os
import sys
import glob

conf = []

for name in glob.glob('config/plugins.d/*.conf'):
    conf.insert(1, name)

if not os.path.exists('~/.nova/'):
    os.makedirs('~/.nova/')

# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements('requirements.txt', session=False)


class PyTest(TestCommand):

    user_options = [('cov=', None, 'Run coverage'), ('cov-xml=', None, 'Generate junit xml report'), ('cov-html=',
                    None, 'Generate junit html report'), ('junitxml=', None, 'Generate xml of test results')]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.cov = None
        self.cov_xml = False
        self.cov_html = False
        self.junitxml = None

    def finalize_options(self):
        TestCommand.finalize_options(self)
        if self.cov is not None:
            self.cov = ['--cov', self.cov, '--cov-report', 'term-missing']
            if self.cov_xml:
                self.cov.extend(['--cov-report', 'xml'])
            if self.cov_html:
                self.cov.extend(['--cov-report', 'html'])
        if self.junitxml is not None:
            self.junitxml = ['--junitxml', self.junitxml]

    def run_tests(self):
        try:
            import pytest
        except:
            raise RuntimeError('py.test is not installed, run: pip install pytest')
        params = {'args': self.test_args}
        if self.cov:
            params['args'] += self.cov
        if self.junitxml:
            params['args'] += self.junitxml
        params['args'] += ['--doctest-modules', 'nova', '-s', '-vv']
        errno = pytest.main(**params)
        sys.exit(errno)


setup(name='gilt-nova',
      version='11.0.3',
      description="Collection of utilities to easily deploy services to AWS.",
      long_description="Collection of utilities to easily deploy services to AWS.",
      license='MIT',
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',

          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'Topic :: Software Development :: Build Tools',

          'License :: OSI Approved :: MIT License',

          'Operating System :: POSIX :: Linux',

          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',

          'Programming Language :: Python :: Implementation :: CPython',
      ],
      keywords='AWS CodeDeploy Cloudformation Deployment Gilt',
      author='Gilt Groupe',
      author_email='gilt-nova-dev@googlegroups.com',
      url='https://github.com/gilt/nova',
      test_suite='tests',
      packages=find_packages(exclude=['ez_setup', 'contrib', 'docs', 'tests', 'tests.*']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[str(ir.req) for ir in install_reqs],
      cmdclass={'test': PyTest},
      tests_require=['pytest-cov', 'pytest', 'nose', 'mock'],
      command_options={
          'test': {
              'test_suite': ('setup.py', 'tests'), 'cov': ('setup.py', 'nova'),
              'cov_xml': ('setup.py', True),
              'junitxml': ('setup.py', 'junit.xml')
          }
      },
      data_files=[('~/.nova', ['config/nova.conf']), ('~/.nova/plugins.d', conf)],
      setup_requires=['flake8'],
      entry_points="""
          [console_scripts]
          nova = nova.cli.main:main
      """,
      namespace_packages=[])
