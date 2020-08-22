# 1. Instalación en linux
Asegurate de hacer lo siguiente para poder correr basemap

```bash
sudo apt-get install libgeos-dev
cd /usr/lib
sudo ln -s libgeos-3.3.3.so libgeos.so
sudo ln -s libgeos-3.3.3.so libgeos.so.1
```

## Anaconda
conda env create -f noche_env.yml
conda activate env

## Virtualenv

```bash
conda deactivate #En caso de que haya un ambiente de anaconda activo
pip install virtualenv 
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

# 2. Demo
Para correr la rutina de la noche ejecute la siguiente linea

```bash
python noche.py
```

más adelante se hará una pequeña demostración.







Luego de ello