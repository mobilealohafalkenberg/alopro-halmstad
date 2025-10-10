/**
 * MJCF (MuJoCo XML) Parser
 *
 * Parses MuJoCo XML files to extract exact joint hierarchy, positions, and rotations.
 * This ensures Three.js visualization matches the MuJoCo model exactly.
 */

import * as THREE from 'three';

export interface MJCFGeometry {
  meshName: string;
  position: THREE.Vector3;
  quaternion: THREE.Quaternion;
}

export interface MJCFBody {
  name: string;
  position: THREE.Vector3;
  quaternion: THREE.Quaternion;
  euler?: THREE.Euler;
  meshName?: string;  // Primary mesh (deprecated, use geometries)
  geometries: MJCFGeometry[];  // All geometries in this body
  jointName?: string;
  jointAxis?: THREE.Vector3;
  jointType?: string;
  jointRange?: [number, number];
  children: MJCFBody[];
}

export interface MJCFModel {
  bodies: MJCFBody[];
  meshes: Map<string, { file: string; scale: THREE.Vector3 }>;
}

/**
 * Parse position attribute "x y z" into Vector3
 */
function parsePosition(posStr: string | null): THREE.Vector3 {
  if (!posStr) return new THREE.Vector3(0, 0, 0);
  const parts = posStr.trim().split(/\s+/).map(parseFloat);
  return new THREE.Vector3(parts[0] || 0, parts[1] || 0, parts[2] || 0);
}

/**
 * Parse quaternion attribute "w x y z" (MuJoCo format) into THREE.Quaternion (x y z w format)
 */
function parseQuaternion(quatStr: string | null): THREE.Quaternion | null {
  if (!quatStr) return null;
  const parts = quatStr.trim().split(/\s+/).map(parseFloat);
  if (parts.length !== 4) return null;
  // MuJoCo uses w,x,y,z but THREE.js uses x,y,z,w
  const quat = new THREE.Quaternion(parts[1], parts[2], parts[3], parts[0]);
  quat.normalize(); // Ensure quaternion is normalized
  return quat;
}

/**
 * Parse euler angles "x y z" (radians) into THREE.Euler
 */
function parseEuler(eulerStr: string | null): THREE.Euler | null {
  if (!eulerStr) return null;
  const parts = eulerStr.trim().split(/\s+/).map(parseFloat);
  if (parts.length !== 3) return null;
  return new THREE.Euler(parts[0], parts[1], parts[2], 'XYZ');
}

/**
 * Parse axis attribute "x y z" into Vector3
 */
function parseAxis(axisStr: string | null): THREE.Vector3 {
  if (!axisStr) return new THREE.Vector3(0, 1, 0); // Default axis
  const parts = axisStr.trim().split(/\s+/).map(parseFloat);
  return new THREE.Vector3(parts[0] || 0, parts[1] || 1, parts[2] || 0);
}

/**
 * Parse joint range "min max" into tuple
 */
function parseRange(rangeStr: string | null): [number, number] | undefined {
  if (!rangeStr) return undefined;
  const parts = rangeStr.trim().split(/\s+/).map(parseFloat);
  if (parts.length !== 2) return undefined;
  return [parts[0], parts[1]];
}

/**
 * Parse scale attribute "x y z" into Vector3
 */
function parseScale(scaleStr: string | null): THREE.Vector3 {
  if (!scaleStr) return new THREE.Vector3(1, 1, 1);
  const parts = scaleStr.trim().split(/\s+/).map(parseFloat);
  return new THREE.Vector3(parts[0] || 1, parts[1] || 1, parts[2] || 1);
}

/**
 * Recursively parse <body> elements from MJCF
 */
function parseBody(bodyElement: Element): MJCFBody {
  const name = bodyElement.getAttribute('name') || 'unnamed';
  const position = parsePosition(bodyElement.getAttribute('pos'));
  const quaternion = parseQuaternion(bodyElement.getAttribute('quat'));
  const euler = parseEuler(bodyElement.getAttribute('euler'));

  // Extract ALL visual geometries from this body
  const geometries: MJCFGeometry[] = [];
  const geomElements = bodyElement.querySelectorAll(':scope > geom[class="visual"]');

  geomElements.forEach((geomElement) => {
    const meshName = geomElement.getAttribute('mesh');
    if (meshName) {
      const geomPos = parsePosition(geomElement.getAttribute('pos'));
      const geomQuat = parseQuaternion(geomElement.getAttribute('quat'));
      geometries.push({
        meshName,
        position: geomPos,
        quaternion: geomQuat || new THREE.Quaternion(),
      });
    }
  });

  // For backward compatibility, store first mesh name
  const meshName = geometries.length > 0 ? geometries[0].meshName : undefined;

  // Extract joint information (only direct children, not descendants)
  const jointElement = bodyElement.querySelector(':scope > joint');
  const jointName = jointElement?.getAttribute('name') || undefined;
  const jointAxis = jointElement ? parseAxis(jointElement.getAttribute('axis')) : undefined;
  const jointType = jointElement?.getAttribute('type') || 'hinge';

  const jointRange = jointElement ? parseRange(jointElement.getAttribute('range')) : undefined;

  // Recursively parse child bodies
  const childBodies = Array.from(bodyElement.querySelectorAll(':scope > body')).map(parseBody);

  return {
    name,
    position,
    quaternion: quaternion || (euler ? new THREE.Quaternion().setFromEuler(euler) : new THREE.Quaternion()),
    euler: euler || undefined,
    meshName,
    geometries,
    jointName,
    jointAxis,
    jointType,
    jointRange,
    children: childBodies,
  };
}

/**
 * Parse MJCF XML string and extract robot model
 */
export function parseMJCF(xmlString: string): MJCFModel {
  const parser = new DOMParser();
  const doc = parser.parseFromString(xmlString, 'text/xml');

  // Check for parsing errors
  const parseError = doc.querySelector('parsererror');
  if (parseError) {
    throw new Error(`XML parsing failed: ${parseError.textContent}`);
  }

  // Parse mesh assets
  const meshes = new Map<string, { file: string; scale: THREE.Vector3 }>();
  doc.querySelectorAll('asset > mesh').forEach((meshElement) => {
    const name = meshElement.getAttribute('name');
    const file = meshElement.getAttribute('file');
    const scale = parseScale(meshElement.getAttribute('scale'));

    if (name && file) {
      meshes.set(name, { file, scale });
    }
  });

  // Parse body hierarchy from worldbody
  const worldbody = doc.querySelector('worldbody');
  if (!worldbody) {
    throw new Error('No <worldbody> element found in MJCF');
  }

  const bodies = Array.from(worldbody.querySelectorAll(':scope > body')).map(parseBody);

  return { bodies, meshes };
}

/**
 * Find a body by name in the hierarchy
 */
export function findBody(bodies: MJCFBody[], name: string): MJCFBody | null {
  for (const body of bodies) {
    if (body.name === name) return body;
    const found = findBody(body.children, name);
    if (found) return found;
  }
  return null;
}

/**
 * Print body hierarchy for debugging
 */
export function printBodyHierarchy(bodies: MJCFBody[], indent = 0): void {
  // Disabled to reduce console clutter
  // bodies.forEach((body) => {
  //   const prefix = '  '.repeat(indent);
  //   console.log(`${prefix}Body: ${body.name}`);
  //   if (body.children.length > 0) {
  //     printBodyHierarchy(body.children, indent + 1);
  //   }
  // });
}

/**
 * Count total bodies in hierarchy
 */
export function countBodies(bodies: MJCFBody[]): number {
  let count = bodies.length;
  bodies.forEach((body) => {
    count += countBodies(body.children);
  });
  return count;
}
