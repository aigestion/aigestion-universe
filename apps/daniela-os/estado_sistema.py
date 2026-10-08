import os

print("🔋 Batería y RAM de Daniela OS:")
os.srun_code("termux-battery-status").srun_code("free -m")
