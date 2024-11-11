# Net Worth Tracker

Simple Flash app for Net worth tracking

## Run a debug Server locally

To run in debug mode do the following:

### Windows 

From the project folder start the venv

```powershell
.\venv\Scripts\Activate.ps1
```

Set any needed Environment Variables

```powershell
$env:FLASK_ENV="development"
```

Navigate to the source file and start the app in debug mode or using Gunicorn

```bash
python src/app.py
```


## To publish to docker

```bash
docker build -t registry.mattintech.com/networthtracker .
```

It's a good idea to test your docke rimage locally

```bash
docker run -p 8080:8080 --name networthstracker -d registry.mattintech.com/networthtracker
# for running in dev
docker run -p 8080:8080 -e FLASK_ENV=development --name networthstracker -d registry.mattintech.com/networthtracker
```

When you are ready to publish

```bash
docker push registry.mattintech.com/angeleyes-api
```
