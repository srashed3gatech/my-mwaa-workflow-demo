# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3

cft_client = boto3.client('cloudformation')
ec2_client = boto3.client('ec2')
s3_resource = boto3.resource('s3')

cft_output_stack_structure = {
    "cdk-mwaa-s3": ["datalake_processed_bucket", "datalake_raw_bucket", "emr_logs_bucket", "emr_scripts_bucket",
                    "mwaa_config_bucket"],
    "cdk-mwaa-vpc": ["vpc_id"],
    "cdk-mwaa-iam": ["mwaa_policy_arn"]
}
DRY_RUN = False


def replace_underscore(underscore_string):
    return underscore_string.replace("_", '')


def clean_vpc_sg(vpc_id):
    security_groups_response = ec2_client.describe_security_groups(Filters=[
        {
            'Name': 'vpc-id',
            'Values': [
                vpc_id
            ]
        }
    ])

    ec2_resource = boto3.resource('ec2')

    for security_group in security_groups_response["SecurityGroups"]:

        security_group_name = security_group["GroupName"]
        security_group_id = security_group["GroupId"]

        if security_group_name != "default":
            print(f"Cleaning SG = {security_group_name}, ID: {security_group_id}")

            security_group = ec2_resource.SecurityGroup(security_group_id)

            security_group.revoke_ingress(IpPermissions=security_group.ip_permissions)

            security_group.revoke_egress(IpPermissions=security_group.ip_permissions_egress)

    for security_group in security_groups_response["SecurityGroups"]:

        security_group_name = security_group["GroupName"]
        security_group_id = security_group["GroupId"]

        if security_group_name != "default":
            print(f"Deleting SG = {security_group_name}, ID: {security_group_id}")

            ec2_client.delete_security_group(GroupId=security_group_id, DryRun=DRY_RUN)


def clean_mwaa_buckets(bucket_name):
    bucket = s3_resource.Bucket(bucket_name)

    delete_response = bucket.objects.delete()

    if delete_response:
        print(f"Delete Complete Bucket = {bucket_name}")


def cleanup_mwaa_resources():
    """Enhanced cleanup function for MWAA resources including environment deletion"""
    print("🧹 Starting MWAA resource cleanup...")
    
    # Check for MWAA environment and delete it first
    try:
        # Look for MWAA environment in CloudFormation outputs
        mwaa_stack_name = "cdk-mwaa-environment"
        
        try:
            mwaa_stack_response = cft_client.describe_stacks(StackName=mwaa_stack_name)
            mwaa_outputs = mwaa_stack_response["Stacks"][0]["Outputs"]
            
            environment_name = None
            for output in mwaa_outputs:
                if output["OutputKey"] == "mwaaenvironmentname":
                    environment_name = output["OutputValue"]
                    break
            
            if environment_name:
                print(f"Found MWAA environment: {environment_name}")
                print("⚠️  MWAA environment deletion should be handled by CDK destroy")
            else:
                print("No MWAA environment found in stack outputs")
                
        except Exception as e:
            print(f"MWAA stack not found or error accessing: {e}")
    
    except Exception as e:
        print(f"Error in MWAA cleanup: {e}")
    
    # Continue with existing cleanup logic
    main()
    
    print("✅ MWAA resource cleanup completed")


def main():
    for stack_name in cft_output_stack_structure.keys():

        cft_stack_response = cft_client.describe_stacks(StackName=stack_name)

        if stack_name.split('-')[-1] == "vpc":

            cft_stack_outputs = cft_stack_response["Stacks"][0]["Outputs"]

            for cft_stack_output in cft_stack_outputs:

                if cft_stack_output["OutputKey"] == replace_underscore(cft_output_stack_structure[stack_name][0]):
                    vpc_id_out = cft_stack_output["OutputValue"]

                    clean_vpc_sg(vpc_id_out)

        if stack_name.split('-')[-1] == "s3":

            cft_stack_outputs = cft_stack_response["Stacks"][0]["Outputs"]

            for cft_stack_output in cft_stack_outputs:

                for cft_expected_output in cft_output_stack_structure[stack_name]:

                    if cft_stack_output["OutputKey"] == replace_underscore(cft_expected_output):

                        bucket_name = cft_stack_output["OutputValue"]

                        print(f"Deleting SG = {bucket_name}")

                        if not DRY_RUN:
                            clean_mwaa_buckets(bucket_name)


if __name__ == "__main__":
    main()
