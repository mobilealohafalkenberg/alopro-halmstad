/**
 * Joint Movement Tests for Virtual Robot Arm
 *
 * These tests verify that each joint moves correctly and the linkage is properly connected.
 */

export interface JointTest {
  name: string;
  joint: string;
  description: string;
  initialAngles: number[]; // [waist, shoulder, elbow, forearm_roll, wrist_angle, wrist_rotate]
  targetAngles: number[];
  expectedBehavior: string;
}

/**
 * Test suite for individual joint movements
 */
export const jointMovementTests: JointTest[] = [
  {
    name: "Waist Rotation Test",
    joint: "waist",
    description: "Test waist (base) joint rotation - should rotate entire arm around Z-axis",
    initialAngles: [0, 0, 0, 0, 0, 0],
    targetAngles: [Math.PI / 2, 0, 0, 0, 0, 0], // 90 degrees
    expectedBehavior: "Entire arm rotates 90° counterclockwise when viewed from above. All links should move together with no gaps.",
  },
  {
    name: "Shoulder Pitch Test",
    joint: "shoulder",
    description: "Test shoulder joint pitch - should tilt upper arm up/down",
    initialAngles: [0, 0, 0, 0, 0, 0],
    targetAngles: [0, Math.PI / 4, 0, 0, 0, 0], // 45 degrees
    expectedBehavior: "Upper arm tilts 45° upward. Upper forearm, lower forearm, wrist, and gripper should all move together with upper arm.",
  },
  {
    name: "Elbow Bend Test",
    joint: "elbow",
    description: "Test elbow joint - should bend upper forearm relative to upper arm",
    initialAngles: [0, 0, 0, 0, 0, 0],
    targetAngles: [0, 0, -Math.PI / 2, 0, 0, 0], // -90 degrees
    expectedBehavior: "Upper forearm bends 90° downward at elbow. Lower forearm, wrist, and gripper follow upper forearm with no gaps.",
  },
  {
    name: "Forearm Roll Test",
    joint: "forearm_roll",
    description: "Test forearm roll - should rotate lower forearm around its own axis",
    initialAngles: [0, 0, 0, 0, 0, 0],
    targetAngles: [0, 0, 0, Math.PI, 0, 0], // 180 degrees
    expectedBehavior: "Lower forearm rotates 180° around its length axis. Wrist and gripper rotate with it.",
  },
  {
    name: "Wrist Angle Test",
    joint: "wrist_angle",
    description: "Test wrist angle - should bend wrist up/down",
    initialAngles: [0, 0, 0, 0, 0, 0],
    targetAngles: [0, 0, 0, 0, Math.PI / 3, 0], // 60 degrees
    expectedBehavior: "Wrist bends 60° upward. Gripper moves with wrist with no gap between wrist and gripper.",
  },
  {
    name: "Wrist Rotate Test",
    joint: "wrist_rotate",
    description: "Test wrist rotation - should rotate gripper around wrist axis",
    initialAngles: [0, 0, 0, 0, 0, 0],
    targetAngles: [0, 0, 0, 0, 0, Math.PI / 2], // 90 degrees
    expectedBehavior: "Gripper rotates 90° around wrist axis. Fingers should rotate with gripper assembly.",
  },
  {
    name: "Combined Movement Test",
    joint: "all",
    description: "Test combined joint movement - verifies overall kinematics",
    initialAngles: [0, 0, 0, 0, 0, 0],
    targetAngles: [0.5, 0.3, -0.5, 0.2, 0.4, 0.1],
    expectedBehavior: "All joints move smoothly together. No gaps should appear between any links during movement.",
  },
];

/**
 * Gripper movement tests
 */
export const gripperMovementTests = [
  {
    name: "Gripper Open Test",
    description: "Test gripper opening - fingers should move apart symmetrically",
    initialPosition: 0.0, // Closed
    targetPosition: 1.0,  // Open
    expectedBehavior: "Both fingers move outward symmetrically. Finger rotation should be around Z-axis (axis='0 0 -1' in ALOHA XML). Max rotation: 0.041 radians.",
  },
  {
    name: "Gripper Close Test",
    description: "Test gripper closing - fingers should move together symmetrically",
    initialPosition: 1.0, // Open
    targetPosition: 0.0,  // Closed
    expectedBehavior: "Both fingers move inward symmetrically until tips nearly touch at center.",
  },
  {
    name: "Partial Gripper Test",
    description: "Test partial gripper positions - verify linear interpolation",
    initialPosition: 0.0,
    targetPosition: 0.5,
    expectedBehavior: "Fingers move to half-open position. Each finger rotates 0.0205 radians (half of 0.041 max range).",
  },
];

/**
 * Linkage connection tests
 */
export const linkageTests = [
  {
    name: "Base-Shoulder Connection",
    description: "Verify shoulder link connects properly to base",
    checkPoints: [
      "Shoulder link origin should be at (0, 0, 0.079) relative to base",
      "Shoulder mesh has offset (0, 0, -0.003) from shoulder origin",
      "No gap should appear between base and shoulder meshes",
    ],
  },
  {
    name: "Shoulder-UpperArm Connection",
    description: "Verify upper arm connects properly to shoulder",
    checkPoints: [
      "Upper arm origin should be at (0, 0, 0.04805) relative to shoulder origin",
      "Upper arm mesh at its origin (no offset)",
      "No gap between shoulder and upper arm",
    ],
  },
  {
    name: "UpperArm-UpperForearm Connection",
    description: "Verify upper forearm connects to upper arm",
    checkPoints: [
      "Upper forearm origin at (0.05955, 0, 0.3) relative to upper arm origin",
      "Upper forearm mesh at its origin",
      "THIS IS WHERE GAPS ARE VISIBLE - check mesh origins in STL files",
    ],
  },
  {
    name: "UpperForearm-LowerForearm Connection",
    description: "Verify lower forearm connects to upper forearm",
    checkPoints: [
      "Lower forearm origin at (0.2, 0, 0) relative to upper forearm",
      "Lower forearm has quaternion rotation (0 1 0 0)",
      "Gap visible here - verify quat and position",
    ],
  },
  {
    name: "LowerForearm-Wrist Connection",
    description: "Verify wrist connects to lower forearm",
    checkPoints: [
      "Wrist origin at (0.1, 0, 0) relative to lower forearm",
      "Wrist mesh at its origin",
      "Gap visible - check connection",
    ],
  },
  {
    name: "Wrist-Gripper Connection",
    description: "Verify gripper connects to wrist",
    checkPoints: [
      "Gripper link origin at (0.069744, 0, 0) relative to wrist",
      "Gripper base has euler rotation (0, 1.57, -1.57) and position (0.035, 0, 0)",
      "Verify this complex transformation",
    ],
  },
];

/**
 * Helper function to run a joint test
 */
export function runJointTest(test: JointTest, robotController: any): Promise<boolean> {
  return new Promise((resolve) => {
    console.log(`\n=== Running Test: ${test.name} ===`);
    console.log(`Description: ${test.description}`);
    console.log(`Initial angles: [${test.initialAngles.map(a => (a * 180 / Math.PI).toFixed(1) + '°').join(', ')}]`);
    console.log(`Target angles: [${test.targetAngles.map(a => (a * 180 / Math.PI).toFixed(1) + '°').join(', ')}]`);
    console.log(`Expected: ${test.expectedBehavior}`);

    // Move to initial position
    robotController.moveToJointAngles(test.initialAngles, 'radians', 1.0);

    setTimeout(() => {
      // Move to target position
      robotController.moveToJointAngles(test.targetAngles, 'radians', 2.0);

      setTimeout(() => {
        console.log(`✓ Test "${test.name}" completed. Please visually verify: ${test.expectedBehavior}`);
        resolve(true);
      }, 3000);
    }, 1500);
  });
}

/**
 * Run all joint tests sequentially
 */
export async function runAllJointTests(robotController: any) {
  console.log('\n🤖 Starting Joint Movement Test Suite\n');
  console.log('=' .repeat(80));

  for (const test of jointMovementTests) {
    await runJointTest(test, robotController);
    await new Promise(resolve => setTimeout(resolve, 500)); // Pause between tests
  }

  console.log('\n✓ All joint movement tests completed!');
  console.log('Please review the visual output and verify no gaps appeared during movements.');
  console.log('=' .repeat(80));
}
