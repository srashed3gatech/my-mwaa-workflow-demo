# MWAA Workflow Demo

## Quick Setup

```bash
npm install -g aws-cdk
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
export DEV_ACCOUNT_ID=
ada credentials update --account=$DEV_ACCOUNT_ID --provider=isengard --role=Admin --once
cdk bootstrap
cdk deploy --all
```

## Post-Deployment

```bash
cd post_scripts
python3 CreateMWAAVariables.py
```

## Cleanup

```bash
cdk destroy --all
```

## Automated Deployment

Single command deployment with MWAA environment creation, variable loading, and DAG enablement:

```bash
make deploy
```

Cleanup:
```bash
make destroy
```
