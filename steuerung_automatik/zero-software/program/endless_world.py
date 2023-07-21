import time
import debugpy

debugpy.listen(("0.0.0.0", 5678))
print("Debugger is ready to be attached, press F5", flush=True)
# debugpy.wait_for_client()
print("Visual Studio Code debugger is now attached", flush=True)

for i in range(100000):
    print(f"Hello World {i}")
    time.sleep(1)
