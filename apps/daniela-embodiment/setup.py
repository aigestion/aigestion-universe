from setuptools import setup

package_name = "daniela_embodiment"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name, f"{package_name}.nodes"],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="AIGESTION Team",
    maintainer_email="team@aigestion.net",
    description="ROS2 embodiment nodes for Daniela OS",
    license="MIT",
)
