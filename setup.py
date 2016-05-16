from setuptools import setup, find_packages
from pip.req import parse_requirements
import os
import glob

conf = []

for name in glob.glob('config/plugins.d/*.conf'):
    conf.insert(1, name)

if not os.path.exists('~/.nova/'):
    os.makedirs('~/.nova/')

# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements('requirements.txt', session=False)

setup(name='gilt-nova',
    version='10.7.3',
    description="Collection of utilities to easily deploy services to AWS.",
    long_description="Collection of utilities to easily deploy services to AWS.",
    license='Apache License 2.0',
    classifiers=[
        'Development Status :: 4 - Beta',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        'License :: OSI Approved :: Apache Software License',

        'Operating System :: POSIX :: Linux',

        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='AWS CodeDeploy Cloudformation Deployment Gilt',
    author='Gilt Groupe',
    author_email='grhodes@gilt.com',
    url='https://github.com/gilt/nova',
    packages=find_packages(exclude=['ez_setup', 'contrib', 'docs']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[str(ir.req) for ir in install_reqs],
    data_files=[('~/.nova', ['config/nova.conf']),
                ('~/.nova/plugins.d', conf)],
    setup_requires=[],
    entry_points="""
        [console_scripts]
        nova = nova.cli.main:main
    """,
    namespace_packages=[],
)

