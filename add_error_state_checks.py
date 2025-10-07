#!/usr/bin/env python3
"""
Script to add ERROR state checks to arm_controller.py movement methods.
"""

def add_error_check_after_line(lines, line_num, method_name):
    """
    Add ERROR state check after the specified line number.

    Args:
        lines: List of file lines
        line_num: Line number (0-indexed) after which to insert
        method_name: Name of method for logging
    """
    error_check = [
        "\n",
        "        # Check if system is in ERROR state (e.g., after emergency stop)\n",
        "        with self.state_lock:\n",
        "            if self.current_state == ArmState.ERROR:\n",
        '                return {"success": False, "error": "System in ERROR state. Call resume_after_stop() to recover.", "state": "error"}\n',
    ]

    # Insert the error check lines after line_num
    for i, line in enumerate(error_check):
        lines.insert(line_num + 1 + i, line)

    print(f"Added ERROR check to {method_name} after line {line_num + 1}")
    return len(error_check)


def main():
    file_path = "/home/anu_09/alopro-halmstad/gemini-live/arm_controller.py"

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"Read {len(lines)} lines from {file_path}")

    # Track insertions to adjust line numbers
    total_inserted = 0

    # 1. move_joints - after line 421 (0-indexed: 420)
    # Find: "return {"success": False, "error": "Not initialized", "state": "unknown"}"
    for i, line in enumerate(lines):
        if i == 420 and '"Not initialized"' in line:
            inserted = add_error_check_after_line(lines, i + total_inserted, "move_joints")
            total_inserted += inserted
            break

    # 2. move_to_position - after line 496 (adjusted)
    base_line = 495
    for i, line in enumerate(lines):
        if i == base_line + total_inserted and '"Not initialized"' in line:
            # Verify this is move_to_position by checking nearby context
            if i > 10 and any('move_to_position' in lines[j] for j in range(i-10, i)):
                inserted = add_error_check_after_line(lines, i + total_inserted, "move_to_position")
                total_inserted += inserted
                break

    # 3. move_to_pose - needs initialization check first, then ERROR check
    # First, find move_to_pose and add initialization check if missing
    base_line = 615
    for i, line in enumerate(lines):
        if i >= base_line + total_inserted - 5 and i <= base_line + total_inserted + 5:
            if 'if pose_name not in self.POSES:' in line:
                # Add initialization check before this line
                init_check = [
                    "        if not self.initialized:\n",
                    '            return {"success": False, "error": "Not initialized", "state": "unknown"}\n',
                    "\n",
                ]
                for j, check_line in enumerate(init_check):
                    lines.insert(i + j, check_line)
                total_inserted += len(init_check)

                # Now add ERROR check after initialization check
                inserted = add_error_check_after_line(lines, i + len(init_check) - 1, "move_to_pose")
                total_inserted += inserted
                print(f"Added initialization and ERROR checks to move_to_pose")
                break

    # 4. execute_trajectory - needs initialization check and ERROR check
    base_line = 673
    for i, line in enumerate(lines):
        if i >= base_line + total_inserted - 5 and i <= base_line + total_inserted + 10:
            if 'Returns:' in line and 'trajectory' in lines[i-1]:
                # Found the Returns section, add checks after the docstring
                # Look for the closing """
                for j in range(i, min(i+5, len(lines))):
                    if '"""' in lines[j] and j > i:
                        # Add initialization check after docstring
                        init_check = [
                            "        if not self.initialized:\n",
                            '            return {"success": False, "error": "Not initialized", "state": "unknown"}\n',
                            "\n",
                        ]
                        for k, check_line in enumerate(init_check):
                            lines.insert(j + 1 + k, check_line)
                        total_inserted += len(init_check)

                        # Add ERROR check
                        inserted = add_error_check_after_line(lines, j + len(init_check), "execute_trajectory")
                        total_inserted += inserted
                        print(f"Added initialization and ERROR checks to execute_trajectory")
                        break
                break

    # 5. set_speed - needs initialization check and ERROR check
    base_line = 1119
    for i, line in enumerate(lines):
        if i >= base_line + total_inserted - 5 and i <= base_line + total_inserted + 5:
            if '"""' in line and any('set_speed' in lines[j] for j in range(max(0, i-20), i)):
                # Found end of set_speed docstring
                # Add initialization check
                init_check = [
                    "        if not self.initialized:\n",
                    '            return {"success": False, "error": "Not initialized", "state": "unknown"}\n',
                    "\n",
                ]
                for j, check_line in enumerate(init_check):
                    lines.insert(i + 1 + j, check_line)
                total_inserted += len(init_check)

                # Add ERROR check
                inserted = add_error_check_after_line(lines, i + len(init_check), "set_speed")
                total_inserted += inserted
                print(f"Added initialization and ERROR checks to set_speed")
                break

    # Write file back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"\nSuccessfully wrote {len(lines)} lines to {file_path}")
    print(f"Total lines added: {total_inserted}")


if __name__ == "__main__":
    main()
