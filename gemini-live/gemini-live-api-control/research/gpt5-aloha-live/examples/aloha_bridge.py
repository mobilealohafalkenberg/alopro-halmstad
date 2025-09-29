#!/usr/bin/env python3
"""
Minimal Python bridge for Mobile ALOHA + Gemini Live API.
Receives tool calls over HTTP and commands Interbotix/ALOHA.
"""

import asyncio
import time
import traceback
from aiohttp import web
from aiohttp_cors import setup, ResourceOptions

# Adjust import path to your environment
try:
    from aloha.real_env import RealEnv  # Provided by your ALOHA/Interbotix setup
except Exception as e:
    raise RuntimeError("Failed to import RealEnv. Ensure your ALOHA env is installed and on PYTHONPATH.") from e

WORKSPACE = {
    'x': (0.15, 0.55),
    'y': (-0.35, 0.35),
    'z': (0.05, 0.45),
}


class Bridge:
    def __init__(self):
        # Initialize robot env; adapt flags per your env
        self.env = RealEnv(init_node=True, setup_robots=True, setup_base=False)

    def _validate(self, x: float, y: float, z: float):
        if not (WORKSPACE['x'][0] <= x <= WORKSPACE['x'][1] and
                WORKSPACE['y'][0] <= y <= WORKSPACE['y'][1] and
                WORKSPACE['z'][0] <= z <= WORKSPACE['z'][1]):
            raise ValueError(f"XYZ outside workspace: {(x,y,z)} limits={WORKSPACE}")

    async def detect_objects(self, args):
        # MVP: rely on Gemini’s visual grounding; return empty map
        return {'objects': {}, 'note': 'stubbed'}

    async def move_to_position(self, args):
        arm = args.get('arm')
        x = float(args['x']); y = float(args['y']); z = float(args['z'])
        self._validate(x, y, z)
        bot = self.env.puppet_bot_left if arm == 'left' else self.env.puppet_bot_right
        ok = bot.arm.set_ee_pose_components(
            x=x, y=y, z=z, roll=0.0, pitch=0.5, yaw=0.0,
            execute=True, moving_time=2.0, accel_time=0.5
        )
        pose = bot.arm.get_ee_pose()
        return {
            'success': bool(ok),
            'target': {'x': x, 'y': y, 'z': z},
            'actual': {'x': float(pose[0, 3]), 'y': float(pose[1, 3]), 'z': float(pose[2, 3])},
        }

    async def control_gripper(self, args):
        arm = args.get('arm'); action = args.get('action')
        grip = (self.env.puppet_bot_left if arm == 'left' else self.env.puppet_bot_right).gripper
        if action == 'open':
            grip.open()
        elif action == 'close':
            grip.close()
        else:
            raise ValueError("action must be 'open' or 'close'")
        await asyncio.sleep(1.0)
        return {'success': True, 'arm': arm, 'action': action}

    async def get_robot_status(self, args):
        status = {}
        for name, bot in [('left', self.env.puppet_bot_left), ('right', self.env.puppet_bot_right)]:
            pose = bot.arm.get_ee_pose()
            status[name] = {
                'end_effector': {'x': float(pose[0, 3]), 'y': float(pose[1, 3]), 'z': float(pose[2, 3])}
            }
        return {'arms': status, 'workspace': WORKSPACE, 'ts': time.time()}


bridge = Bridge()


async def handle(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        name = data.get('name'); args = data.get('args', {})
        if name == 'detect_objects':
            res = await bridge.detect_objects(args)
        elif name == 'move_to_position':
            res = await bridge.move_to_position(args)
        elif name == 'control_gripper':
            res = await bridge.control_gripper(args)
        elif name == 'get_robot_status':
            res = await bridge.get_robot_status(args)
        else:
            raise ValueError(f'unknown tool {name}')
        return web.json_response({'success': True, 'result': res, 'call_id': data.get('id')})
    except Exception as e:
        traceback.print_exc()
        return web.json_response({'success': False, 'error': str(e)}, status=500)


def make_app() -> web.Application:
    app = web.Application()
    setup(app, defaults={
        '*': ResourceOptions(
            allow_credentials=True, expose_headers='*', allow_headers='*', allow_methods='*'
        )
    })
    app.router.add_post('/aloha-tool-call', handle)
    return app


if __name__ == '__main__':
    web.run_app(make_app(), host='0.0.0.0', port=8081)

