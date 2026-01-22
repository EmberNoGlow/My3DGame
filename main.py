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
from src.classes.Bodies import *

player_position = vec3(0.0,0.0,0.0)


class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.set_background_color(0.1, 0.1, 0.1, 1)
        self.win.set_clear_color(Vec4(0.1, 0.2, 0.3, 1))
        
        cube_mesh = mesh(self.loader, "assets/models/boxes/box.obj")
        instance1 = cube_mesh.create_instance(
            parent_node=self.render,
            position= vec3(0,-2.25,0),
            rotation= vec3(0,0,0)
        )
        instance1.set_scale_vec3(vec3(2.5,0.2,2.5))

        # Setup physics world
        self.world = BulletWorld()

        # Create character
        self.character = CharacterBody(
            self.loader.loadModel("assets/models/character/untitled.obj"),
            self.world,
            self
        )

        # Position character
        self.character.set_position_vec3(vec3(0, 2, 0))
        self.character.set_scale_vec3(vec3(2,2,2))


        self.disableMouse()
        self.camera.setPos(0, -10, 2)
        self.camera.lookAt(0, 0, 0)

        self.environment()

        floor = StaticBody( world=self.world, render=self.render, position=vec3(0,-4, 0), 
                           size=vec3(40, 2, 40), # width, depth, height 
                           rotation=vec3(0, 0, 0), shape="box" )



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