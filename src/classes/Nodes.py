from direct.showbase.ShowBase import ShowBase
from panda3d.core import NodePath, Vec4, DirectionalLight, AmbientLight
from src.classes.Math import vec3

class SceneObject(NodePath):
    # Base class for any object that exists in the scene graph.
    # Handles common operations like position, rotation, and cleanup.
    def __init__(self, node_path: NodePath):
        super().__init__(node_path)

    def set_position_vec3(self, pos: vec3):
        #Sets position using vec3 (X, Y, Z) -> Panda3D (X, Z, Y)
        self.setPos(pos.x, pos.z, pos.y)

    def get_position_vec3(self) -> vec3:
        # Gets position as vec3 (X, Y, Z)
        p = self.getPos()
        return vec3(p.x, p.y, p.z)

    def set_rotation_vec3(self, rot: vec3):
        # Sets rotation using vec3 (X, Y, Z) -> Panda3D (H, P, R)
        # X = Pitch, Y = Heading, Z = Roll
        self.setHpr(rot.y, rot.x, rot.z)

    def get_rotation_vec3(self) -> vec3:
        # Gets rotation as vec3 (X, Y, Z)
        h, p, r = self.getHpr()
        return vec3(p, h, r)


    def set_scale_vec3(self, scale: vec3):
        self.setScale(scale.x, scale.z, scale.y)

    def get_scale_vec3(self, scale: vec3):
        x,y,z = self.getScale()
        return vec3(x,z,y)


    def cleanup(self):
        # Safely removes the node from the scene graph.
        if not self.isEmpty():
            self.removeNode()

# --- Mesh System ---
class mesh:
    # Represents a reusable mesh asset (model data).
    def __init__(self, loader, model_path: str):
        self.loader = loader
        self.model_data: NodePath = self.loader.loadModel(model_path)

        if not self.model_data:
            raise FileNotFoundError(f"Could not load model from {model_path}")

    def create_instance(self, parent_node: NodePath, position: vec3 = vec3(0, 0, 0), rotation: vec3 = vec3(0, 0, 0)) -> 'MeshInstance':
        # Creates a new instance of this mesh in the scene.
        return MeshInstance(self, parent_node, position, rotation)

class MeshInstance(SceneObject):
    # An instance of a mesh in the scene.
    def __init__(self, mesh_template: mesh, parent_node: NodePath, position: vec3, rotation: vec3):
        # Copy the model data to create a new instance
        instance_np = mesh_template.model_data.copyTo(parent_node)
        super().__init__(instance_np)

        self.mesh_template = mesh_template
        self.set_position_vec3(position)
        self.set_rotation_vec3(rotation)

# --- Light System ---
class Light(SceneObject):
    # Base class for all light types.
    def __init__(self, light_node: NodePath, render: NodePath):
        super().__init__(light_node)
        render.setLight(self)

class DirectLight(Light):
    # A directional light source.
    def __init__(self, render: NodePath, rotation: vec3, color: vec3):
        d_light = DirectionalLight('d_light')
        d_light.setColor(Vec4(color.x, color.y, color.z, 1))

        light_np = render.attachNewNode(d_light)
        light_np.setHpr(rotation.y, rotation.x, rotation.z)  # Y=Heading, X=Pitch, Z=Roll

        super().__init__(light_np, render)

class Ambient(Light):
    # An ambient light source.
    def __init__(self, render: NodePath, color: vec3):
        a_light = AmbientLight('a_light')
        a_light.setColor(Vec4(color.x, color.y, color.z, 1))

        light_np = render.attachNewNode(a_light)
        super().__init__(light_np, render)
