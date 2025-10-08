# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from airflow.providers.amazon.aws.operators.emr import (
    EmrCreateJobFlowOperator,
    EmrAddStepsOperator,
)
from airflow.providers.amazon.aws.sensors.emr import EmrStepSensor
from airflow.providers.amazon.aws.hooks.emr import EmrHook
import time
from botocore.exceptions import ClientError


class CustomEmrCreateJobFlowOperator(EmrCreateJobFlowOperator):
    """
    Custom EMR Create Job Flow Operator that explicitly sets emr_conn_id to None
    to avoid the 'emr_default' connection warning and includes better error handling.
    """
    
    def __init__(self, wait_for_completion=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wait_for_completion = wait_for_completion
    
    def execute(self, context):
        # Create EMR hook with explicit connection configuration
        emr_hook = EmrHook(
            aws_conn_id=self.aws_conn_id,
            emr_conn_id=None  # Explicitly set to None to avoid warning
        )
        
        self.log.info("Creating EMR cluster")
        
        try:
            response = emr_hook.create_job_flow(self.job_flow_overrides)
            
            if not response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200:
                raise RuntimeError(f"Failed to create EMR cluster: {response}")
            
            job_flow_id = response['JobFlowId']
            self.log.info(f"EMR cluster created with JobFlowId: {job_flow_id}")
            
            if self.wait_for_completion:
                self.log.info("Waiting for cluster to be ready...")
                self._wait_for_cluster_ready(emr_hook, job_flow_id)
            
            return job_flow_id
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.log.error(f"AWS ClientError creating EMR cluster: {error_code} - {error_message}")
            raise RuntimeError(f"Failed to create EMR cluster: {error_code} - {error_message}")
        except Exception as e:
            self.log.error(f"Unexpected error creating EMR cluster: {str(e)}")
            raise
    
    def _wait_for_cluster_ready(self, emr_hook, job_flow_id, max_attempts=60, wait_time=30):
        """Wait for cluster to be in WAITING or RUNNING state"""
        for attempt in range(max_attempts):
            try:
                cluster_response = emr_hook.get_conn().describe_cluster(ClusterId=job_flow_id)
                cluster_state = cluster_response['Cluster']['Status']['State']
                state_reason = cluster_response['Cluster']['Status'].get('StateChangeReason', {}).get('Message', '')
                
                self.log.info(f"Cluster {job_flow_id} is in state: {cluster_state}")
                
                if cluster_state in ['WAITING', 'RUNNING']:
                    self.log.info(f"Cluster {job_flow_id} is ready for steps")
                    return
                elif cluster_state in ['TERMINATED', 'TERMINATED_WITH_ERRORS', 'TERMINATING']:
                    raise RuntimeError(f"Cluster {job_flow_id} failed with state: {cluster_state}. Reason: {state_reason}")
                
                if attempt < max_attempts - 1:
                    self.log.info(f"Waiting {wait_time} seconds before next check...")
                    time.sleep(wait_time)
                    
            except ClientError as e:
                self.log.error(f"Error checking cluster state: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(wait_time)
                else:
                    raise
        
        raise RuntimeError(f"Cluster {job_flow_id} did not become ready within {max_attempts * wait_time} seconds")


class CustomEmrAddStepsOperator(EmrAddStepsOperator):
    """
    Custom EMR Add Steps Operator that explicitly sets emr_conn_id to None
    to avoid the 'emr_default' connection warning and validates cluster state with retry logic.
    """
    
    def __init__(self, max_retry_attempts=5, retry_delay=60, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_retry_attempts = max_retry_attempts
        self.retry_delay = retry_delay
    
    def execute(self, context):
        # Create EMR hook with explicit connection configuration
        emr_hook = EmrHook(
            aws_conn_id=self.aws_conn_id,
            emr_conn_id=None  # Explicitly set to None to avoid warning
        )
        
        # Resolve job_flow_id if it's a template
        job_flow_id = self.job_flow_id
        if isinstance(job_flow_id, str) and "{{" in job_flow_id:
            # This is a templated string, render it
            job_flow_id = context['task_instance'].render_template(job_flow_id, context)
        
        # Handle case where job_flow_id might be a list (from XCom)
        if isinstance(job_flow_id, list):
            if len(job_flow_id) > 0:
                job_flow_id = job_flow_id[0]
            else:
                job_flow_id = None
        
        if not job_flow_id:
            raise ValueError("job_flow_id is None or empty. Check if create_emr_cluster task completed successfully.")
        
        self.log.info(f"Adding steps to EMR cluster: {job_flow_id}")
        
        # Wait for cluster to be ready with retry logic
        self._wait_for_cluster_ready(emr_hook, job_flow_id)
        
        try:
            response = emr_hook.add_job_flow_steps(
                job_flow_id=job_flow_id,
                steps=self.steps,
                wait_for_completion=self.wait_for_completion
            )
            
            # Handle both dict and list response formats
            if isinstance(response, dict):
                if not response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200:
                    raise RuntimeError(f"Failed to add steps to EMR cluster: {response}")
                step_ids = response.get('StepIds', [])
            elif isinstance(response, list):
                # If response is a list, it's likely the step IDs directly
                step_ids = response
            else:
                raise RuntimeError(f"Unexpected response format from add_job_flow_steps: {type(response)}")
            
            self.log.info(f"Steps added with StepIds: {step_ids}")
            
            return step_ids
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.log.error(f"AWS ClientError adding steps to EMR cluster: {error_code} - {error_message}")
            raise RuntimeError(f"Failed to add steps to EMR cluster: {error_code} - {error_message}")
        except Exception as e:
            self.log.error(f"Unexpected error adding steps to EMR cluster: {str(e)}")
            raise
    
    def _wait_for_cluster_ready(self, emr_hook, job_flow_id):
        """Wait for cluster to be in WAITING or RUNNING state with retry logic"""
        for attempt in range(self.max_retry_attempts):
            try:
                cluster_response = emr_hook.get_conn().describe_cluster(ClusterId=job_flow_id)
                cluster_state = cluster_response['Cluster']['Status']['State']
                state_reason = cluster_response['Cluster']['Status'].get('StateChangeReason', {}).get('Message', '')
                
                self.log.info(f"Attempt {attempt + 1}/{self.max_retry_attempts}: Cluster {job_flow_id} is in state: {cluster_state}")
                
                if cluster_state in ['WAITING', 'RUNNING']:
                    self.log.info(f"Cluster {job_flow_id} is ready for steps")
                    return
                elif cluster_state in ['TERMINATED', 'TERMINATED_WITH_ERRORS']:
                    raise RuntimeError(f"Cluster {job_flow_id} failed with state: {cluster_state}. Reason: {state_reason}")
                elif cluster_state == 'TERMINATING':
                    raise RuntimeError(f"Cluster {job_flow_id} is terminating. Cannot add steps. Reason: {state_reason}")
                elif cluster_state in ['STARTING', 'BOOTSTRAPPING']:
                    if attempt < self.max_retry_attempts - 1:
                        self.log.info(f"Cluster is still starting up. Waiting {self.retry_delay} seconds before retry...")
                        time.sleep(self.retry_delay)
                    else:
                        raise RuntimeError(f"Cluster {job_flow_id} did not become ready within {self.max_retry_attempts} attempts")
                else:
                    # Unknown state, wait and retry
                    if attempt < self.max_retry_attempts - 1:
                        self.log.warning(f"Unknown cluster state: {cluster_state}. Waiting {self.retry_delay} seconds before retry...")
                        time.sleep(self.retry_delay)
                    else:
                        raise RuntimeError(f"Cluster {job_flow_id} is in unexpected state: {cluster_state}")
                        
            except ClientError as e:
                self.log.error(f"Error checking cluster state on attempt {attempt + 1}: {e}")
                if attempt < self.max_retry_attempts - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise RuntimeError(f"Failed to check cluster state after {self.max_retry_attempts} attempts: {str(e)}")


class CustomEmrStepSensor(EmrStepSensor):
    """
    Custom EMR Step Sensor that explicitly sets emr_conn_id to None
    to avoid the 'emr_default' connection warning.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def poke(self, context):
        # Create EMR hook with explicit connection configuration
        emr_hook = EmrHook(
            aws_conn_id=self.aws_conn_id,
            emr_conn_id=None  # Explicitly set to None to avoid warning
        )
        
        # Resolve job_flow_id if it's a template
        job_flow_id = self.job_flow_id
        if isinstance(job_flow_id, str) and "{{" in job_flow_id:
            job_flow_id = context['task_instance'].render_template(job_flow_id, context)
        
        # Handle case where job_flow_id might be a list (from XCom)
        if isinstance(job_flow_id, list):
            if len(job_flow_id) > 0:
                job_flow_id = job_flow_id[0]
            else:
                job_flow_id = None
        
        # Resolve step_id if it's a template
        step_id = self.step_id
        if isinstance(step_id, str) and "{{" in step_id:
            step_id = context['task_instance'].render_template(step_id, context)
        
        # Handle case where step_id might be a list (from XCom)
        if isinstance(step_id, list):
            if len(step_id) > 0:
                step_id = step_id[0]
            else:
                step_id = None
        
        if not job_flow_id or not step_id:
            raise ValueError(f"job_flow_id ({job_flow_id}) or step_id ({step_id}) is None or empty")
        
        self.log.info(f"Checking step {step_id} on cluster {job_flow_id}")
        
        response = emr_hook.get_conn().describe_step(
            ClusterId=job_flow_id,
            StepId=step_id
        )
        
        step_state = response['Step']['Status']['State']
        self.log.info(f"Step {step_id} is in state: {step_state}")
        
        if step_state in self.target_states:
            return True
        elif step_state in self.failed_states:
            raise RuntimeError(f"Step {step_id} failed with state: {step_state}")
        
        return False
