#!/usr/bin/env python3
"""
Mock bridge for developing on a Mac without the robot.
Implements the same /aloha-tool-call API as the real bridge,
but returns canned data and echoes inputs.
"""

import asyncio
import time
from aiohttp import web
from aiohttp_cors import setup, ResourceOptions

WORKSPACE = {'x': (0.15, 0.55), 'y': (-0.35, 0.35), 'z': (0.05, 0.45)}


async def handle(request: web.Request) -> web.Response:
    data = await request.json()
    name = data.get('name')
    args = data.get('args', {})

    if name == 'detect_objects':
        res = {
            'objects': {
                'red_cup': {'position': {'x': 0.32, 'y': 0.08, 'z': 0.12}, 'confidence': 0.9},
                'blue_bowl': {'position': {'x': 0.40, 'y': -0.14, 'z': 0.08}, 'confidence': 0.92},
                'banana': {'position': {'x': 0.28, 'y': 0.00, 'z': 0.10}, 'confidence': 0.8},
            },
            'workspace': WORKSPACE,
            'ts': time.time(),
        }
    elif name == 'move_to_position':
        x = float(args.get('x', 0)); y = float(args.get('y', 0)); z = float(args.get('z', 0))
        res = {
            'success': True,
            'arm': args.get('arm'),
            'target': {'x': x, 'y': y, 'z': z},
            'actual': {'x': x, 'y': y, 'z': z},
            'note': 'mocked movement (no hardware)'
        }
    elif name == 'control_gripper':
        res = {'success': True, 'arm': args.get('arm'), 'action': args.get('action'), 'note': 'mocked'}
    elif name == 'get_robot_status':
        res = {
            'arms': {
                'left': {'end_effector': {'x': 0.25, 'y': 0.15, 'z': 0.20}},
                'right': {'end_effector': {'x': 0.30, 'y': -0.05, 'z': 0.18}},
            },
            'workspace': WORKSPACE,
            'ts': time.time(),
        }
    else:
        return web.json_response({'success': False, 'error': f'unknown tool {name}'}, status=400)

    return web.json_response({'success': True, 'result': res, 'call_id': data.get('id')})


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

