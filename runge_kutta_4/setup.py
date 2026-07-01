from setuptools import Extension, setup

setup(
    ext_modules=[
        Extension(
            "ode.solver._rk4",
            sources=[
                "src/ode/solver/_rk4.c",
            ],
        )
    ]
)
