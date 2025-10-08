- Use AWS Sample: https://github.com/aws-samples/amazon-mwaa-workflow-demo?tab=readme-ov-file
- Clone the code: `git clone https://github.com/aws-samples/amazon-mwaa-workflow-demo.git && cd amazon-mwaa-workflow-demo`
```
npm install -g aws-cdk
cd ~/environment/amazon-mwaa-workflow-demo
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
export DEV_ACCOUNT_ID=992382677689
ada credentials update --account=$DEV_ACCOUNT_ID --provider=isengard --role=Admin --once
cdk bootstrap
cdk deploy --all
```
### Step 5 - Run the Post Deployment script to generate a JSON file containing the required Airflow Variables

```
cd /post_scripts
python3 CreateMWAAVariables.py
```
- Check in the "amazon-mwaa-workflow-demo/post_scripts" folder the existence of the "mwaa_demo_variables.json" file


## step 7 - Create a Amazon MWAA Environment

7.1 Search for Amazon MWAA service in the AWS Console.
7.2 Click Create Environment
7.3 On "Environment Details", enter the Name of your preference
7.4 On "DAG code in Amazon S3 > S3 Bucket", click "Browse" and select the Amazon S3 bucket created by the AWS CDK Script with the following pattern *cdk-mwaa-s3-mwaaconfigXXXXXXX*
7.5 On "DAG code in Amazon S3 > DAGs folder", click "Browse" and select the "dags" folder inside the Bucket. Leave the rest of the settings with the defaults values and click "Next"
7.6 On "Networking > Virtual private cloud (VPC)", Select the VPC that matches the VPC-ID provided in the CDK Output
7.7 On "Networking > Subnet 1 and Subbnet 2", Select the Subnets that matches the *cdk-mwaa-vpc.mwaasubnetid1* and *cdk-mwaa-vpc.mwaasubnetid2* respectively provided in the CDK Output
7.8 On "Networking > Web server access", Select "Public network (No additional setup)", and ensure that "Create new security group" is checked.
7.7 Leave the rest of the parameters with the defaults values. Click "Next", and then click "Create Environment"
7.8 Click on the new environment and search for the "Execution Role". Click on the role name, you'll be re-directed to the IAM Role configuration. Click on "Attach Policy", search for the  *mwaa_airflow_policy* policy, select it and click "Attach"
  - arn:aws:iam::992382677689:role/service-role/AmazonMWAA-MyAirflowEnvironment-ANZPOJ
7.9 Return to the Amazon MWAA Service Console. Wait for the deployment to complete, click in the newly created environment name, search and click the Airflow User Interface link

### Step 8 - Load Airflow Variables and Trigger the "mwaa_blogpost_data_pipeline" DAG

8.1 In the Airflow Web Server Interface, Click in the top panel "Admin > Variables", proceed to load the JSON file generated in step 5
8.2 Return to the DAGs pannel, Click on the *mwaa_blogpost_data_pipeline* Dag and proceed to inspect the "Tree View" and "Graph View" of the DAG
8.3 Enable the Dag by clicking on the "Off" icon in the top left. It will transition to "On" and one execution of the dag will be scheduled and executed.
8.4 Inspect the transitions of the Dag, the Amazon S3 Buckets involved in the Data Pipelenie, Amazon EMR service (Cluster Creation and Termination), and AWS Glue Crawler.
8.5 Finaly in the Aamazon S3 Bucket *datalake_processed_bucket/athena_results* you'll find the results of this data pipelinee in a CSV Format.

### Step Cleanup

In order to delete all the components deployed by this solution and avoid additional charges:

1 - Reverse Step 7.8. Click on the new Amazon MWAA environment and search for the "Execution Role". Click on the role name, you'll be re-directed to the IAM Role configuration. Select mwaa_airflow_policy policy, select it and click "Detech Policy"
2 - Delete the Amazon MWAA Environment, wait until the environment is successfully deleted
3 - Run the Post Deployment script in the AWS Cloud9 Terminal to delete the Security Groups created for the Amazon MWAA environment and Amazon EMR Cluster Instances (Master and Core). Monitor the Output of the Script for the successful completion.
    ```
    cd ~/environment/amazon-mwaa-workflow-demo/post_scripts
    python3 CleanUpScript.py
    ```
4 - Delete the AWS CDK Stack. In the AWS Cloud9 Terminal run the following commands. Monitor the terminal and enter "Y" when prompted about deleting the cdk-mwaa-s3, cdk-mwaa-vpc, and cdk-mwaa-iam stacks
    ```
    cd  ~/environment/amazon-mwaa-workflow-demo
    cdk destroy --all
    ```