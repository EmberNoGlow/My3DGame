
from direct.showbase.ShowBase import ShowBase
from panda3d.core import NodePath, Vec4, Vec3, DirectionalLight, AmbientLight, CollisionNode, CollisionSphere, CollisionTraverser, CollisionHandlerPusher, BitMask32
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.bullet import BulletCharacterControllerNode, BulletWorld, BulletCapsuleShape
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
        self.velocity = Vec3(0.0,0.0,0.0)
        self.gravity = -9.81

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
            # Convert to Panda coordinates. Based on set_position_vec3 you used (x, z, y),
            # convert vec3(x,y,z) -> Panda Vec3(x, z, y). Adjust if your vec3 has different axes.
            panda_move = Vec3(move_dir.x, move_dir.z, move_dir.y) * (self.current_speed * dt * self.delta_speed)
            # setLinearMovement stores movement for the next physics step
            self.controller_node.node().setLinearMovement(panda_move, True)
        else:
            # stop horizontal movement (optional)
            self.controller_node.node().setLinearMovement(Vec3(0, 0, 0), True)

        # Jump (Panda uses Z-up so z component is vertical)
        if self.accepted_keys['jump'] and self.controller_node.node().isOnGround():
            jump_vec = Vec3(0, 0, self.jump_force)
            self.controller_node.node().setLinearMovement(jump_vec, True)

        self.controller_node.node().setGravity(0)
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



class StaticBody:
    def __init__(self, position, size):
        self.position = position
        self.size = size
        
    def get_position(self):
        return self.position
        
    def get_size(self):
        return self.size
