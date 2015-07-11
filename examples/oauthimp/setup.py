from setuptools import setup, find_packages
setup(
    name = "FlaskForward-OAuth",
    version = "0.0.1",
    packages = find_packages(),
    # requirements
    dependency_links=[
        "git+ssh://git@github.com:nineohnine/flask-forward.git@v0.0.1#egg=FlaskForward-0.0.1"
    ],
    install_requires = [
        'Flask==0.10.0',
        'FlaskForward==0.0.1'
    ],
    # metadata for upload to PyPI
    author = "Brent Rotz",
    author_email = "rotzbrent@gmail.com",
    description = "Oauth example of flask-forward.",
)
