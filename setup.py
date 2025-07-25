from setuptools import setup, find_packages

setup(
    name="pyncraft_server",
    version="0.0.4",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "pyncraft = core.main:start_server",
        ],
    },
    install_requires=[
        "cryptography==45.0.5",
        "nbtlib==2.0.4",
        "requests==2.32.4",
    ] ,
)