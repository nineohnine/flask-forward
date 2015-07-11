from setuptools import setup, find_packages
setup(
    name = "Flask-Forward",
    version = "0.0.1",
    packages = find_packages(),
    # requirements
    install_requires = [
        'oauthlib==0.6.3',
    ],
    # metadata for upload to PyPI
    author = "Brent Rotz",
    author_email = "rotzbrent@gmail.com",
    description = "Flask extension for token based API development (specifically oauth2).",
)
