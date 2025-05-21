import carla
import time
import hashlib
import json
from hfc.fabric import Client
from hfc.fabric.user import create_user
from concurrent.futures import ThreadPoolExecutor

# ===== Blockchain Configuration =====
HLF_NETWORK_PROFILE = "network.json"
HLF_CHANNEL = "autochannel"
HLF_CHAINCODE = "autocc"
VEHICLE_REGISTRY_CC = "vehicle-registry"

class AutonomousVehicleSimulator:
    def __init__(self):
        # Initialize Fabric client
        self.hlf_client = Client(net_profile=HLF_NETWORK_PROFILE)
        self.hlf_admin = create_user(name='admin', org='Org1')
        
        # CARLA setup
        self.client = carla.Client('localhost', 2000)
        self.client.set_timeout(10.0)
        self.world = self.client.get_world()
        self.blueprint_lib = self.world.get_blueprint_library()
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        # Vehicle registry
        self.vehicles = {}

    async def init_blockchain(self):
        await self.hlf_client.init_with_discovery()
        
    def _calculate_hash(self, data):
        return hashlib.sha256(json.dumps(data).encode()).hexdigest()

    async def register_vehicle(self, vehicle_id, vehicle_type):
        """Register vehicle on blockchain"""
        args = [vehicle_id, vehicle_type, str(time.time())]
        response = await self.hlf_client.chaincode_invoke(
            requestor=self.hlf_admin,
            channel_name=HLF_CHANNEL,
            peers=['peer0.org1.example.com'],
            cc_name=VEHICLE_REGISTRY_CC,
            fcn='registerVehicle',
            args=args
        )
        return response

    async def record_event(self, event_type, data):
        """Record vehicle event on blockchain"""
        try:
            event_hash = self._calculate_hash(data)
            args = [event_type, json.dumps(data), event_hash]
            
            response = await self.hlf_client.chaincode_invoke(
                requestor=self.hlf_admin,
                channel_name=HLF_CHANNEL,
                peers=['peer0.org1.example.com'],
                cc_name=HLF_CHAINCODE,
                fcn='createEvent',
                args=args
            )
            return response
        except Exception as e:
            print(f"Blockchain error: {str(e)}")

    def sensor_callback(self, sensor_data, vehicle_id):
        """Handle sensor data with off-chain storage"""
        # Save raw data locally (simulated off-chain storage)
        file_path = f'offchain_data/{vehicle_id}_{sensor_data.frame}.data'
        sensor_data.save_to_disk(file_path)
        
        # Record hash on blockchain
        data_hash = self._calculate_hash(sensor_data.raw_data)
        event_data = {
            'vehicle_id': vehicle_id,
            'sensor_type': 'camera',
            'data_hash': data_hash,
            'timestamp': time.time(),
            'offchain_location': file_path
        }
        self.executor.submit(self.record_event, 'SENSOR_DATA', event_data)

    async def cooperative_perception(self, vehicle):
        """Simulate cooperative perception using blockchain"""
        # Get nearby vehicles from blockchain
        nearby_vehicles = await self.get_nearby_vehicles(vehicle.get_location())
        
        # Request perception data hashes
        perception_data = []
        for v_id in nearby_vehicles:
            result = await self.hlf_client.chaincode_query(
                requestor=self.hlf_admin,
                channel_name=HLF_CHANNEL,
                peers=['peer0.org1.example.com'],
                cc_name=HLF_CHAINCODE,
                fcn='getPerceptionData',
                args=[v_id]
            )
            perception_data.extend(json.loads(result))
        
        # Verify data integrity
        valid_data = [d for d in perception_data 
                     if d['hash'] == self._calculate_hash(d['data'])]
        
        # Update local perception (simulated)
        self.update_perception_model(valid_data)

    async def decentralized_decision(self, vehicle, decision_type):
        """Implement blockchain-based decision consensus"""
        proposal = {
            'vehicle_id': vehicle.id,
            'decision_type': decision_type,
            'timestamp': time.time(),
            'proposed_action': vehicle.get_control()
        }
        
        # Submit proposal to blockchain
        await self.record_event('DECISION_PROPOSAL', proposal)
        
        # Wait for consensus (simulated PBFT)
        consensus = await self.reach_consensus(proposal)
        
        if consensus:
            vehicle.apply_control(consensus['approved_action'])
            await self.update_reputation(vehicle.id, 1.0)
        else:
            await self.update_reputation(vehicle.id, -0.5)

    async def run_simulation(self):
        """Main simulation loop"""
        # Initialize blockchain
        await self.init_blockchain()
        
        # Spawn main vehicle
        vehicle_bp = self.blueprint_lib.filter('model3')[0]
        spawn_point = random.choice(self.world.get_map().get_spawn_points())
        vehicle = self.world.spawn_actor(vehicle_bp, spawn_point)
        self.vehicles[vehicle.id] = vehicle
        
        # Register vehicle on blockchain
        await self.register_vehicle(str(vehicle.id), 'Tesla Model 3')
        
        # Add sensors
        camera_bp = self.blueprint_lib.find('sensor.camera.rgb')
        camera = self.world.spawn_actor(camera_bp, 
                                       carla.Transform(carla.Location(x=1.5, z=2.7)),
                                       attach_to=vehicle)
        camera.listen(lambda data: self.sensor_callback(data, vehicle.id))
        
        # Main loop
        while True:
            # Cooperative perception update
            await self.cooperative_perception(vehicle)
            
            # Decentralized decision making at intersections
            if self.approaching_intersection(vehicle):
                await self.decentralized_decision(vehicle, 'INTERSECTION_NAV')
            
            # Update position on blockchain
            location = vehicle.get_location()
            pos_data = {
                'vehicle_id': vehicle.id,
                'position': [location.x, location.y, location.z],
                'timestamp': time.time()
            }
            await self.record_event('POSITION_UPDATE', pos_data)
            
            time.sleep(1)

if __name__ == "__main__":
    simulator = AutonomousVehicleSimulator()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(simulator.run_simulation())