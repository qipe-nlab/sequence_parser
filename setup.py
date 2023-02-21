from setuptools import setup, find_packages

setup(
    name="sequence-parser",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "matplotlib",
        "networkx",
    ]
)
