from direct.showbase.ShowBase import ShowBase
from panda3d.core import NodePath, Vec4, Vec3, DirectionalLight, AmbientLight, BitMask32
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.bullet import (
    BulletCharacterControllerNode,
    BulletWorld,
    BulletCapsuleShape,
    BulletRigidBodyNode,
    BulletBoxShape,
    BulletPlaneShape,
)
from direct.task import Task
from src.classes.Math import vec3, lerp_angle
from src.classes.Nodes import SceneObject
import numpy as np

class CharacterBody(SceneObject):
    def __init__(self, node_path: NodePath, world: BulletWorld, base: ShowBase):
        # Initialize the SceneObject wrapper around the model node
        super().__init__(node_path)

        # Save references
        self.world = world
        self.base = base

        self.current_rotation_y = 0
        self.target_rotation_y = 0


        # Character controller (physics) setup:
        # create the Bullet character controller and attach it into the scene graph under base.render
        self.controller = BulletCharacterControllerNode(
            BulletCapsuleShape(0.5, 1.7, 1),  # radius, height, axis
            0.4,  # step height
            "character"
        )

        # IMPORTANT: put the controller node into the scene graph (under render),
        # not as a child of the model. The controller is what the physics world moves.
        self.controller_node = self.base.render.attachNewNode(self.controller)
        self.controller_node.setPos(0, 0, 5)  # Start above ground
        self.controller_node.setCollideMask(BitMask32.allOn())

        # Add the controller to the physics world
        self.world.attachCharacter(self.controller_node.node())

        # Reparent the visual model to the controller node so the visual follows the physics
        # (loader.loadModel returns an unparented NodePath; if it's never parented to render it won't be visible)
        node_path.reparentTo(self.controller_node)
        # make sure the model sits at the controller origin
        node_path.setPos(0, 0, 0)

        # Input handling state
        self.accepted_keys = {
            'forward': False,
            'backward': False,
            'left': False,
            'right': False,
            'jump': False
        }

        # Movement parameters
        self.walk_speed = 5.0
        self.delta_speed = 15.0
        self.run_speed = 10.0
        self.jump_force = 8.0
        self.current_speed = self.walk_speed
        self.velocity = vec3(0.0,0.0,0.0)
        self.gravity = 9.81

        # Setup input handling and update task
        self.setup_input()
        self.base.taskMgr.add(self.update, "character_update")

    # Override set_position_vec3 so callers (e.g. main.py) move the physics controller
    def set_position_vec3(self, pos: vec3):
        # Keep coordinate conversion consistent with SceneObject (X,Y,Z -> Panda X,Z,Y)
        self.controller_node.setPos(pos.x, pos.z, pos.y)
    
    def set_scale_vec3(self, scale: vec3):
        self.controller_node.setScale(scale.x, scale.z, scale.y)

    def setup_input(self):
        """Set up keyboard input handling"""
        # Movement keys
        self.base.accept('w', self.set_key, ['forward', True])
        self.base.accept('w-up', self.set_key, ['forward', False])
        self.base.accept('s', self.set_key, ['backward', True])
        self.base.accept('s-up', self.set_key, ['backward', False])
        self.base.accept('a', self.set_key, ['left', True])
        self.base.accept('a-up', self.set_key, ['left', False])
        self.base.accept('d', self.set_key, ['right', True])
        self.base.accept('d-up', self.set_key, ['right', False])

        # Jump
        self.base.accept('space', self.set_key, ['jump', True])
        self.base.accept('space-up', self.set_key, ['jump', False])

        # Speed toggle
        self.base.accept('shift', self.toggle_run)
        self.base.accept('shift-up', self.toggle_walk)

    def set_key(self, key, value):
        """Update key state"""
        self.accepted_keys[key] = value

    def toggle_run(self):
        """Set movement to run speed"""
        self.current_speed = self.run_speed

    def toggle_walk(self):
        """Set movement to walk speed"""
        self.current_speed = self.walk_speed

    def update(self, task):
        dt = globalClock.getDt()

        # Build move_dir in your vec3 space:
        move_dir = vec3(0, 0, 0)
        if self.accepted_keys['forward']:
            move_dir.z += 1
        if self.accepted_keys['backward']:
            move_dir.z -= 1
        if self.accepted_keys['left']:
            move_dir.x -= 1
        if self.accepted_keys['right']:
            move_dir.x += 1


        smooth_rot = lerp_angle(self.current_rotation_y,self.target_rotation_y,10,dt)
        self.set_rotation_vec3(vec3(90,smooth_rot,0))


        if move_dir.length() > 0:
            self.target_rotation_y = np.rad2deg( np.arctan2(-move_dir.x, move_dir.z) )
            move_dir = move_dir.normalize()
            self.velocity.x = move_dir.x * (self.current_speed)
            self.velocity.z = move_dir.z * (self.current_speed)
        else:
            self.velocity.x = 0
            self.velocity.z = 0

        self.velocity.y -= self.gravity * dt
        # Jump (Panda uses Z-up so z component is vertical)
        if self.accepted_keys['jump'] and self.controller_node.node().isOnGround():
            self.velocity.y = self.jump_force

        vel_vector = Vec3( self.velocity.x, self.velocity.z, self.velocity.y )
        self.controller_node.node().setLinearMovement(vel_vector, True)
        self.world.doPhysics(dt, 10, 1.0/180.0)

        self.current_rotation_y = smooth_rot


        return Task.cont

    def cleanup(self):
        """Clean up resources"""
        # Remove from physics world
        try:
            self.world.removeCharacter(self.controller_node.node())
        except Exception:
            pass

        # Remove input handlers
        self.base.ignoreAll()

        # Remove update task
        self.base.taskMgr.remove("character_update")

        # Detach visuals and controller
        try:
            # unparent model first to avoid orphan NodePaths in case of reuse
            self.detach_node()
        except Exception:
            pass

        try:
            self.controller_node.removeNode()
        except Exception:
            pass

        super().cleanup()



class StaticBody(SceneObject):
    def __init__(
        self,
        world: BulletWorld,
        render: NodePath,
        position: vec3,
        size: vec3 = vec3(1, 1, 1),
        rotation: vec3 = vec3(0, 0, 0),
        shape: str = "box",
        collide_mask: BitMask32 = BitMask32.allOn(),
    ):
        # Create the Bullet node depending on shape
        if shape == "box":
            # Convert size (full extents) from project vec3 to Panda half-extents
            half_extents = Vec3(size.x / 2.0, size.z / 2.0, size.y / 2.0)
            bullet_shape = BulletBoxShape(half_extents)
            node = BulletRigidBodyNode("static_box")
            node.setMass(0.0)  # mass 0 -> static
            node.addShape(bullet_shape)
        elif shape == "plane":
            # plane shape: orientation depends on rotation; plane normal is +Z by default in BulletPlaneShape
            # For flexibility we still attach a rigid node and keep it static.
            bullet_shape = BulletPlaneShape(Vec3(0, 0, 1), 0)  # default horizontal plane at origin
            node = BulletRigidBodyNode("static_plane")
            node.setMass(0.0)
            node.addShape(bullet_shape)
        else:
            raise ValueError("Unsupported shape for StaticBody: must be 'box' or 'plane'")

        # Attach node into scene graph under render so transforms can be applied
        node_path = render.attachNewNode(node)
        # Set position using the same converter used elsewhere: (x, z, y)
        node_path.setPos(position.x, position.z, position.y)
        # set HPR: SceneObject.set_rotation_vec3 expects rot vec3 where .y -> H, .x -> P, .z -> R
        # We can use the SceneObject method after calling super().__init__
        super().__init__(node_path)
        self.set_rotation_vec3(rotation)

        # collision mask
        node_path.setCollideMask(collide_mask)

        # store references
        self.world = world
        self.bullet_node = node
        self.node_path = node_path
        self.shape = shape
        self.size = size

        # add to physics world
        self.world.attachRigidBody(self.bullet_node)

    def cleanup(self):
        # Remove from physics world and scenegraph
        try:
            self.world.removeRigidBody(self.bullet_node)
        except Exception:
            pass

        try:
            if not self.isEmpty():
                self.removeNode()
        except Exception:
            pass

    def get_position(self) -> vec3:
        p = self.node_path.getPos()
        # Convert back to project vec3: Panda (x,y,z) -> project (x, z, y)
        return vec3(p.x, p.z, p.y)

    def get_size(self) -> vec3:
        return self.size