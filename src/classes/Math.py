import numpy as np
from panda3d.core import Vec3

class vec3:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other):
        return vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float):
        return vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float):
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float):
        return vec3(self.x / scalar, self.y / scalar, self.z / scalar)

    def dot(self, other) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        return vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

    def magnitude(self) -> float:
        return (self.x**2 + self.y**2 + self.z**2)**0.5

    def normalize(self):
        mag = self.magnitude()
        if mag == 0:
            return vec3(0, 0, 0)
        return self / mag
    
    def length(self) -> float:
        return np.linalg.norm([self.x, self.y, self.z])


    def __repr__(self):
        return f"!vec3({self.x}, {self.y}, {self.z})"

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z


    def to_panda(self) -> Vec3:
        return Vec3(self.x,self.y,self.z)