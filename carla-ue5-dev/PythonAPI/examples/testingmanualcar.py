import glob
import os
import sys

try:
    sys.path.append(glob.glob('dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
import random


actor_list = []

try:
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    blueprint_library = world.get_blueprint_library()
   
    vehicle_bp = blueprint_library.filter('model3')[0]
    spawn_point = random.choice(world.get_map().get_spawn_points())
   
finally:
    for actor in actor_list:
        if actor is not None:
            actor.destroy()
    print('All cleaned up')  # noqa: T001