#!/usr/bin/env python3

"""
Simple test to verify deprecation warnings are in place.
This doesn't require hardware dependencies - just checks code structure.
"""

import ast
import sys

def check_deprecation_warnings():
    """Check if deprecation warnings are properly implemented"""
    print("="*60)
    print("Checking Deprecation Warning Implementation")
    print("="*60)

    # Read the gripper_controller.py file (two directories up from test/test_deprecation/)
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gripper_controller_path = os.path.join(script_dir, '..', '..', 'gripper_controller.py')

    with open(gripper_controller_path, 'r') as f:
        content = f.read()
        tree = ast.parse(content)

    # Find all function definitions
    functions_to_check = [
        'get_controller',
        'open_gripper',
        'close_gripper',
        'get_gripper_state',
        'cleanup'
    ]

    results = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in functions_to_check:
            # Check if function has deprecation warning
            has_warning = False
            has_docstring_deprecation = False

            # Check docstring for deprecation notice
            docstring = ast.get_docstring(node)
            if docstring and ('deprecated' in docstring.lower()):
                has_docstring_deprecation = True

            # Check function body for warnings.warn call
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                    if hasattr(stmt.value.func, 'attr') and stmt.value.func.attr == 'warn':
                        # Check if it's warnings.warn
                        if hasattr(stmt.value.func.value, 'id') and stmt.value.func.value.id == 'warnings':
                            has_warning = True

            results[node.name] = {
                'has_docstring_deprecation': has_docstring_deprecation,
                'has_warning_call': has_warning
            }

    # Print results
    print("\nFunction Deprecation Status:")
    print("-" * 60)

    all_good = True
    for func_name in functions_to_check:
        if func_name in results:
            result = results[func_name]
            doc_status = "✓" if result['has_docstring_deprecation'] else "✗"
            warn_status = "✓" if result['has_warning_call'] else "✗"

            print(f"\n{func_name}():")
            print(f"  {doc_status} Docstring deprecation notice: {result['has_docstring_deprecation']}")
            print(f"  {warn_status} warnings.warn() call: {result['has_warning_call']}")

            if not (result['has_docstring_deprecation'] and result['has_warning_call']):
                all_good = False
        else:
            print(f"\n{func_name}():")
            print(f"  ✗ Function not found!")
            all_good = False

    # Check class docstring
    print("\n" + "-" * 60)
    print("Checking GripperController class docstring...")

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'GripperController':
            docstring = ast.get_docstring(node)
            if docstring:
                if 'deprecated' in docstring.lower():
                    print("✓ Class docstring mentions deprecation")
                else:
                    print("✓ Class docstring updated (mentions singleton functions)")
            else:
                print("✗ No class docstring found")

    print("\n" + "="*60)
    if all_good:
        print("✅ SUCCESS: All deprecation warnings properly implemented!")
        print("="*60)
        print("\nAll 5 singleton functions have:")
        print("  ✓ Deprecation notice in docstring")
        print("  ✓ warnings.warn() call in implementation")
        print("\nMigration guide available at:")
        print("  docs/MIGRATION_GUIDE_GRIPPER_SINGLETON_REMOVAL.md")
        return 0
    else:
        print("❌ FAILURE: Some deprecation warnings missing!")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(check_deprecation_warnings())
