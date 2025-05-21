import glob
import os
import sys
import numpy as np
import time
import json
import asyncio
from hfc.fabric import Client

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

# Hyperledger Fabric Setup
HLF_NETWORK_PROFILE = "path/to/network.json"
HLF_CHANNEL = "mychannel"
HLF_CHAINCODE = "autochain"

async def init_fabric():
    client = Client(net_profile=HLF_NETWORK_PROFILE)
    admin = client.get_user('org1.example.com', 'Admin')
    await client.init_with_discovery()
    return client, admin

async def record_vehicle_event(client, admin, event_type, data):
    try:
        response = await client.chaincode_invoke(
            requestor=admin,
            channel_name=HLF_CHANNEL,
            peers=['peer0.org1.example.com'],
            cc_name=HLF_CHAINCODE,
            fcn='createVehicleEvent',
            args=[event_type, json.dumps(data)]
        )
        print(f"Blockchain Recorded: {event_type}")
        return response
    except Exception as e:
        print(f"Blockchain Error: {str(e)}")

def main():
    # Initialize Fabric client
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    hlf_client, hlf_admin = loop.run_until_complete(init_fabric())

    try:
        # CARLA Setup
        carla_client = carla.Client('localhost', 2000)
        carla_client.set_timeout(2.0)
        world = carla_client.get_world()
        blueprint_library = world.get_blueprint_library()
        
        # Spawn Vehicle
        vehicle_bp = blueprint_library.filter('model3')[0]
        spawn_point = random.choice(world.get_map().get_spawn_points())
        vehicle = world.spawn_actor(vehicle_bp, spawn_point)
        actor_list.append(vehicle)
        
        # Record vehicle creation on blockchain
        vehicle_data = {
            'id': str(vehicle.id),
            'type': 'Model3',
            'position': {
                'x': spawn_point.location.x,
                'y': spawn_point.location.y,
                'z': spawn_point.location.z
            },
            'timestamp': time.time()
        }
        loop.run_until_complete(
            record_vehicle_event(hlf_client, hlf_admin, 'VEHICLE_CREATED', vehicle_data)
        )

        # Enable autopilot
        vehicle.set_autopilot(True)
        vehicle.apply_control(carla.VehicleControl(throttle=0.5, steer=0.0))

        # Add camera sensor
        camera_bp = blueprint_library.find('sensor.camera.rgb')
        camera_bp.set_attribute('image_size_x', '800')
        camera_bp.set_attribute('image_size_y', '600')
        camera_bp.set_attribute('fov', '110')
        camera_transform = carla.Transform(carla.Location(x=1.5, z=2.7))
        camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)
        actor_list.append(camera)

        # Camera callback with blockchain integration
        def camera_callback(image):
            image.save_to_disk('output/%06d.png' % image.frame)
            event_data = {
                'vehicle_id': vehicle.id,
                'frame': image.frame,
                'timestamp': time.time(),
                'image_hash': hash(image.raw_data.tobytes())
            }
            loop.run_until_complete(
                record_vehicle_event(hlf_client, hlf_admin, 'IMAGE_CAPTURED', event_data)
            )

        camera.listen(camera_callback)

        # Simulation loop
        start_time = time.time()
        while time.time() - start_time < 30:  # Run for 30 seconds
            # Record periodic position updates
            vehicle_location = vehicle.get_location()
            position_data = {
                'vehicle_id': vehicle.id,
                'position': {
                    'x': vehicle_location.x,
                    'y': vehicle_location.y,
                    'z': vehicle_location.z
                },
                'speed': vehicle.get_velocity().length(),
                'timestamp': time.time()
            }
            loop.run_until_complete(
                record_vehicle_event(hlf_client, hlf_admin, 'POSITION_UPDATE', position_data)
            )
            time.sleep(5)

    finally:
        # Cleanup
        for actor in actor_list:
            if actor is not None:
                actor.destroy()
        
        # Record vehicle destruction
        destruction_data = {
            'vehicle_id': vehicle.id,
            'timestamp': time.time()
        }
        loop.run_until_complete(
            record_vehicle_event(hlf_client, hlf_admin, 'VEHICLE_DESTROYED', destruction_data)
        )
        print('Simulation cleaned up')

if __name__ == '__main__':
    main()