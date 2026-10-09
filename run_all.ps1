# run_all.ps1
# Script to run the entire Part A setup at once

$env:SIMULATION_INP_PATH="config/catchments/dummy_test.inp"

Write-Host "Starting Hydrology Worker (Telemetry Broadcaster) in the background..." -ForegroundColor Green
# Start the simulation wrapper as a background process so it doesn't block the terminal
Start-Process python -ArgumentList "-m core.simulation.pyswmm_wrapper"

Write-Host "Starting 2D Visualizer..." -ForegroundColor Green
# Run the visualizer in the foreground (this will open the GUI)
python visualize_2d.py --inp config/catchments/dummy_test.inp

Write-Host "Done! The visualization window should be open." -ForegroundColor Cyan
