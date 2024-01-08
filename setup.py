from setuptools import setup, find_namespace_packages


with open("README.md", "r") as fh:
    long_description = fh.read()

with open("VERSION", "r") as fh:
    version = fh.read().strip()


setup(
    name='cltl.g2kmore',
    version=version,
    package_dir={'': 'src'},
    packages=find_namespace_packages(include=['cltl.*', 'cltl_service.*'], where='src'),
    data_files=[('VERSION', ['VERSION'])],
    url="https://github.com/leolani/cltl-g2kmore",
    license='MIT License',
    author='CLTL',
    author_email='t.baier@vu.nl',
    description='Get to know more component',
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires='>=3.8',
    install_requires=[],
    extras_require={
        "impl": ['cltl.brain', 'cltl.reply_generation'],
        "service": [
            "emissor",
            "cltl.combot",
            "cltl.emissor-data",
        ]}
)
