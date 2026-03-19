conda create -n drone python=3.9
conda activate drone
pip install -r requirements.txt

git clone --branch UE4.27 https://github.com/EpicGamesExt/PixelStreamingInfrastructure.git