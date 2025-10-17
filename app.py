#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import App
from cdk_mwaa_blogpost.VPCStack import VPCStack
from cdk_mwaa_blogpost.DataLakeStack import DataLakeStack
from cdk_mwaa_blogpost.IAMStack import IAMStack
from cdk_mwaa_blogpost.MWAAStack import MWAAStack

app = App()

# Create infrastructure stacks
vpc = VPCStack(app, "cdk-mwaa-vpc")
data_lake = DataLakeStack(app, 'cdk-mwaa-s3')

s3_buckets = data_lake.buckets

iam = IAMStack(app, 'cdk-mwaa-iam', s3_buckets=s3_buckets)

# Create MWAA environment stack
mwaa = MWAAStack(app, 'cdk-mwaa-environment', 
                 vpc_stack=vpc, 
                 data_lake_stack=data_lake, 
                 iam_stack=iam)

# Add dependencies to ensure proper deployment order
mwaa.add_dependency(vpc)
mwaa.add_dependency(data_lake)
mwaa.add_dependency(iam)

app.synth()
