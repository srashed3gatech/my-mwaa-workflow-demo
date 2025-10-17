# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    Stack,
    CfnOutput,
    aws_mwaa as mwaa,
    aws_iam as iam,
    aws_ec2 as ec2,
    Duration
)
from constructs import Construct


class MWAAStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc_stack, data_lake_stack, iam_stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Store references to other stacks
        self.vpc_stack = vpc_stack
        self.data_lake_stack = data_lake_stack
        self.iam_stack = iam_stack
        self.s3_buckets = data_lake_stack.buckets
        
        # Get VPC from VPC stack
        self.vpc = self._get_vpc_from_stack()
        
        # Create MWAA execution role
        self.mwaa_execution_role = self._create_mwaa_execution_role()
        
        # Create security group for MWAA
        self.mwaa_security_group = self._create_mwaa_security_group()
        
        # Create MWAA environment
        self.mwaa_environment = self._create_mwaa_environment()
        
        # Add cleanup automation (placeholder for CDK custom resource)
        self.cleanup_automation = True  # This will be enhanced with actual custom resource

        # Outputs
        CfnOutput(self, 'mwaa_environment_name', value=self.mwaa_environment.name)
        CfnOutput(self, 'mwaa_webserver_url', value=self.mwaa_environment.attr_webserver_url)
        CfnOutput(self, 'mwaa_execution_role_arn', value=self.mwaa_execution_role.role_arn)

    def _get_vpc_from_stack(self):
        """Get VPC from the VPC stack"""
        # Look for VPC in the vpc_stack's children
        for child in self.vpc_stack.node.children:
            if isinstance(child, ec2.Vpc):
                return child
        
        # Fallback: use default VPC lookup
        return ec2.Vpc.from_lookup(self, 'DefaultVPC', is_default=False)

    def _create_mwaa_execution_role(self):
        """Create MWAA execution role with necessary permissions"""
        
        # Create MWAA execution role
        mwaa_role = iam.Role(
            self, 'MWAAExecutionRole',
            role_name='AmazonMWAA-ExecutionRole-Demo',
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal('airflow-env.amazonaws.com'),
                iam.ServicePrincipal('airflow.amazonaws.com')
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonMWAAServiceRolePolicy')
            ]
        )

        # Add S3 permissions for MWAA config bucket
        mwaa_s3_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                's3:ListBucket',
                's3:GetObject*',
                's3:GetBucketLocation'
            ],
            resources=[
                self.s3_buckets['mwaa_config'].bucket_arn,
                f"{self.s3_buckets['mwaa_config'].bucket_arn}/*"
            ]
        )

        # Add CloudWatch Logs permissions
        logs_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                'logs:CreateLogGroup',
                'logs:CreateLogStream',
                'logs:PutLogEvents',
                'logs:GetLogEvents',
                'logs:GetLogRecord',
                'logs:GetLogGroupFields',
                'logs:GetQueryResults',
                'logs:DescribeLogGroups'
            ],
            resources=[f'arn:aws:logs:{self.region}:{self.account}:log-group:airflow-*']
        )

        # Try to attach the existing MWAA policy from IAM stack
        try:
            existing_policy = iam.ManagedPolicy.from_managed_policy_name(
                self, 'ExistingMWAAPolicy', 'mwaa_airflow_policy'
            )
            mwaa_role.add_managed_policy(existing_policy)
        except:
            # If policy doesn't exist yet, create inline policies
            mwaa_role.add_to_policy(mwaa_s3_policy)
            mwaa_role.add_to_policy(logs_policy)

        return mwaa_role

    def _create_mwaa_security_group(self):
        """Create security group for MWAA"""
        
        security_group = ec2.SecurityGroup(
            self, 'MWAASecurityGroup',
            vpc=self.vpc,
            description='Security group for Amazon MWAA environment',
            allow_all_outbound=True
        )

        # Add self-referencing rule for MWAA components communication
        security_group.add_ingress_rule(
            peer=security_group,
            connection=ec2.Port.all_traffic(),
            description='Allow all traffic within security group'
        )

        # Add HTTPS access for web server
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description='HTTPS access to MWAA web server'
        )

        return security_group

    def _create_mwaa_environment(self):
        """Create MWAA environment"""
        
        # Get private subnets for MWAA
        private_subnets = self.vpc.private_subnets
        if len(private_subnets) < 2:
            # Fallback to all subnets if not enough private subnets
            private_subnets = self.vpc.isolated_subnets + self.vpc.private_subnets
        
        subnet_ids = [subnet.subnet_id for subnet in private_subnets[:2]]

        # MWAA Environment configuration
        mwaa_environment = mwaa.CfnEnvironment(
            self, 'MWAAEnvironment',
            name='mwaa-demo-environment',
            
            # Airflow configuration
            airflow_version='2.8.1',
            
            # S3 configuration
            source_bucket_arn=self.s3_buckets['mwaa_config'].bucket_arn,
            dag_s3_path='dags',
            
            # Execution role
            execution_role_arn=self.mwaa_execution_role.role_arn,
            
            # Network configuration
            network_configuration=mwaa.CfnEnvironment.NetworkConfigurationProperty(
                subnet_ids=subnet_ids,
                security_group_ids=[self.mwaa_security_group.security_group_id]
            ),
            
            # Web server access
            webserver_access_mode='PUBLIC_ONLY',
            
            # Environment class
            environment_class='mw1.small',
            
            # Logging configuration
            logging_configuration=mwaa.CfnEnvironment.LoggingConfigurationProperty(
                dag_processing_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                    enabled=True,
                    log_level='INFO'
                ),
                scheduler_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                    enabled=True,
                    log_level='INFO'
                ),
                task_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                    enabled=True,
                    log_level='INFO'
                ),
                webserver_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                    enabled=True,
                    log_level='INFO'
                ),
                worker_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                    enabled=True,
                    log_level='INFO'
                )
            ),
            
            # Airflow configuration options
            airflow_configuration_options={
                'core.load_examples': 'False',
                'core.dags_are_paused_at_creation': 'False',
                'webserver.expose_config': 'True'
            }
        )

        return mwaa_environment
