# FocusOnYou

Automatic Person Tracking Video Service  
[Project Description](https://omoknooni.tistory.com/78)

## Architecture
![architecture.png](./mdImg/architecture.png)

## Install
```bash
# install package python3-venv
sudo apt install python3-venv

# Setting python virtual env
python3 -m venv focusonyou-env

# Install pip requirements
pip3 install -r requirements.txt

```

## Run
```bash
uvicorn main:app --reload
```


## TODO
- Auth Service
- Service Containerization
- Cloud Service Template (ex. terraform, cloudformation)
- Workload Stabilization