from setuptools import setup, find_packages

setup(
    name='notedx-sdk',
    version='1.0.0',
    description='Official Python SDK for NoteDx API.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Your Company or Name',
    author_email='your-email@example.com',
    url='https://github.com/your-repo/notedx-sdk',
    packages=find_packages(),
    install_requires=[
        'requests>=2.20.0',
        'firebase_admin>=6.0.0; python_version>="3.7"',  # If you want integrated Firebase Admin for token management
    ],
    python_requires='>=3.7',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # or appropriate
        'Operating System :: OS Independent',
    ],
)