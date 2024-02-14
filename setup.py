from setuptools import setup, find_packages

VERSION = '0.7.1'
DESCRIPTION = 'Base model for tortoise-api'
LONG_DESCRIPTION = 'A package that allows to build simple streams of video, audio and camera data.'

# Setting up
setup(
    name="tortoise_api_model",
    version=VERSION,
    author="Mike Artemiev",
    author_email="<mixartemev@gmail.com>",
    description=DESCRIPTION,
    packages=find_packages(),
    install_requires=[
        'tortoise-orm[asyncpg]',
        'passlib[bcrypt]',
        'pydantic'
    ],
    keywords=['tortoise', 'model', 'crud', 'generator', 'api', 'admin'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)