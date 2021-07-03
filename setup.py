import setuptools

setuptools.setup(
    name='romanesco',
    version='0.1.0',
    description='Expenses reporting system',
    url='https://github.com/rubenseyer/romanesco',
    package_dir={'romanesco': 'romanesco'},
    packages=setuptools.find_packages(where='.'),
    python_requires='>=3.9',
    entry_points={'console_scripts': ['romanesco=romanesco:__main__']},
    install_requires=['Flask', 'apsw', 'pdfminer.six']
)
