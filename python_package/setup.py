from setuptools import setup, find_packages
from setuptools.dist import Distribution
from wheel.bdist_wheel import bdist_wheel as _bdist_wheel # type: ignore

class bdist_wheel_override(_bdist_wheel):
    def get_tag(self):
        _, _, plat_tag = super().get_tag()
        return "py3", "none", plat_tag
    
class BinaryDistribution(Distribution):
    def has_ext_modules(self):
        return True

setup(
    name="softviterbi",
    version="0.1.0",
    description="Viterbi decoder Python wrapper",
    author="Guy Sharon",
    author_email="g.sharon@proton.me",
    url="https://github.com/guy-sharon/softviterbi",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    distclass=BinaryDistribution,
    cmdclass={"bdist_wheel": bdist_wheel_override}
)
