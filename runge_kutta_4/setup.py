from setuptools import Extension, setup

setup(
    ext_modules=[
        Extension(
            "rk4.solver._rk4",
            sources=["src/rk4/solver/_rk4.c"],
        )
    ]
)
