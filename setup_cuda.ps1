$ErrorActionPreference = "Stop"
Write-Host "Activating venv_cuda..."
.\venv_cuda\Scripts\activate

Write-Host "Installing PyTorch with CUDA 12.1..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

Write-Host "Installing other dependencies..."
pip install ultralytics flask opencv-python pandas scikit-learn

Write-Host "Installation Complete! Starting the server..."
python app.py
