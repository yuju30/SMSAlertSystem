from setuptools import setup

setup(
    name='SMSAlertSystem',
    version='0.1.0',
    packages=['system'],
    include_package_data=True,
    install_requires=[
        'click',
        'pytest',
        'pytest-mock',
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'system-producer = system.producer.__main__:main',
            'system-sender = system.sender.__main__:main',
            'system-monitor = system.monitor.__main__:main',
        ]
    },
)
