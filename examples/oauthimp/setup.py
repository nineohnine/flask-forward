from setuptools import setup, find_packages
setup(
    name = "Flask-Forward",
    version = "0.0.1",
    packages = find_packages(),
    # requirements
    install_requires = [
        'Flask==0.10.0',
        'Flask-Forward'
    ],
    dependency_links=[
        "git+ssh://git@github.com/mwilliamson/mayo.git@0.2.1#egg=Flask-Forward"
    ],
    # metadata for upload to PyPI
    author = "Brent Rotz",
    author_email = "rotzbrent@gmail.com",
    description = "Oauth example of flask-forward.",
)
