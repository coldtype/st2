from pathlib import Path
from subprocess import run

def run_tests():
    for test in Path("tests").glob("test*.py"):
        output = run(["coldtype", "-p", "b3dlo", "-bcli", ">--factory-startup --no-window-focus", test, "quit=1"], capture_output=True)

        if "AssertionError" in output.stdout.decode("utf-8"):
            print("FAIL", test)
            return
        else:
            print(".", end="", flush=True)
        
    print("\nPASSED!\n")

run_tests()