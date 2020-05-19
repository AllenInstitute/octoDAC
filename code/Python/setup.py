from setuptools import setup

setup(
    name='octoDAC',
    version='0.1.0',
    author='Rusty Nicovich',
    author_email='rustyn@alleninstitute.org',
    packages=['octoDAC', 'octoDAC.driver', 'octoDAC.validation'],
    license='LICENSE.txt',
    description='PC-side drivers for octoDAC Arduino shield',
    long_description=open('README.txt').read(),
    install_requires=[
        "serial",
    ],
)