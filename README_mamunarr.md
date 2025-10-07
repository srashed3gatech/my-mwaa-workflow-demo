- Use AWS Sample: https://github.com/aws-samples/amazon-mwaa-workflow-demo?tab=readme-ov-file

-
- Using Cloud9 IDE
- Clone the code: `git clone https://github.com/aws-samples/amazon-mwaa-workflow-demo.git && cd amazon-mwaa-workflow-demo`
```
npm install -g aws-cdk
cd ~/environment/amazon-mwaa-workflow-demo
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
export DEV_ACCOUNT_ID=992382677689
ada credentials update --account=$DEV_ACCOUNT_ID --provider=isengard --role=Admin --once
cdk bootstrap --context region=us-west-2
cdk deploy --all --context region=us-west-2
```