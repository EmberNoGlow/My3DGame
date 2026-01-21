# Panda3D
from direct.showbase.ShowBase import ShowBase
from panda3d.bullet import BulletWorld
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import Vec4, Vec3, DirectionalLight, AmbientLight, NodePath

# Math
from src.classes.Math import *
import numpy as np

# Nodes
from src.classes.Nodes import *
from src.classes.Bodies import CharacterBody

player_position = vec3(0.0,0.0,0.0)


class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.set_background_color(0.1, 0.1, 0.1, 1)
        self.win.set_clear_color(Vec4(0.1, 0.2, 0.3, 1))
        
        cube_mesh = mesh(self.loader, "assets/models/boxes/box.obj")
        instance1 = cube_mesh.create_instance(
            parent_node=self.render,
            position= vec3(0,0,0),
            rotation= vec3(0,45,0)
        )


        # Setup physics world
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -9.81))

        # Create character
        self.character = CharacterBody(
            self.loader.loadModel("assets/models/boxes/box.obj"),
            self.world,
            self
        )

        # Position character
        self.character.set_position_vec3(vec3(0, 0, 0))


        self.disableMouse()
        self.camera.setPos(0, -10, 2)
        self.camera.lookAt(0, 0, 0)

        self.environment()

    def environment(self):
        render=self.render
        sun = DirectLight(
            render,
            rotation=vec3(-45, -60, 0),
            color=vec3(0.8, 0.8, 0.8)
        )
        
        ambient = Ambient(
            render,
            vec3(0.2,0.2,0.2)
        )


app = MyApp()
app.run()