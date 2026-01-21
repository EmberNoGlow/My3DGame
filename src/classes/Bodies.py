from direct.showbase.ShowBase import ShowBase
from panda3d.core import NodePath, Vec4, DirectionalLight, AmbientLight, CollisionNode, CollisionSphere, CollisionTraverser, CollisionHandlerPusher, BitMask32
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.bullet import BulletCharacterControllerNode, BulletWorld, BulletCapsuleShape
from direct.task import Task
from src.classes.Math import vec3
from src.classes.Nodes import SceneObject

class CharacterBody(SceneObject):
    def __init__(self, node_path: NodePath, world: BulletWorld, base: ShowBase):
        super().__init__(node_path)

        # Physics setup
        self.world = world
        self.base = base

        # Character controller setup
        self.controller = BulletCharacterControllerNode(
            BulletCapsuleShape(0.5, 1.7, 1),  # radius, height, axis
            0.4,  # step height
            "character"
        )
        self.controller_node = self.attachNewNode(self.controller)
        self.controller_node.setPos(0, 0, 5)  # Start above ground
        self.controller_node.setCollideMask(BitMask32.allOn())

        # Add to physics world
        self.world.attachCharacter(self.controller_node.node())

        # Input setup
        self.accepted_keys = {
            'forward': False,
            'backward': False,
            'left': False,
            'right': False,
            'jump': False
        }

        # Movement parameters
        self.walk_speed = 5.0
        self.run_speed = 10.0
        self.jump_force = 8.0
        self.current_speed = self.walk_speed
        self.gravity = -9.81

        # Setup input handling
        self.setup_input()

        # Add update task
        self.base.taskMgr.add(self.update, "character_update")

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
        """Update character state each frame"""
        dt = globalClock.getDt()

        # Calculate movement direction
        move_dir = vec3(0, 0, 0)

        if self.accepted_keys['forward']:
            move_dir.z -= 1
        if self.accepted_keys['backward']:
            move_dir.z += 1
        if self.accepted_keys['left']:
            move_dir.x -= 1
        if self.accepted_keys['right']:
            move_dir.x += 1
            

        # Normalize and apply speed
        if move_dir.length() > 0:
            move_dir.normalize()
            move_dir *= self.current_speed * dt

            # Apply movement to character controller
            self.controller_node.node().setLinearMovement(move_dir.to_panda(), True)

        # Handle jumping
        if self.accepted_keys['jump'] and self.controller_node.node().isOnGround():
            self.controller_node.node().setLinearMovement(vec3(0, 0, self.jump_force).to_panda(), True)

        return Task.cont

    def cleanup(self):
        """Clean up resources"""
        # Remove from physics world
        self.world.removeCharacter(self.controller_node.node())

        # Remove input handlers
        self.base.ignoreAll()

        # Remove update task
        self.base.taskMgr.remove("character_update")

        # Clean up node
        super().cleanup()