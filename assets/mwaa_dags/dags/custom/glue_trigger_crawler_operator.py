# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import time
from airflow.models import BaseOperator
from airflow.providers.amazon.aws.hooks.glue import GlueJobHook


class GlueTriggerCrawlerOperator(BaseOperator):
    """
   Operator that triggers a crawler run in AWS Glue.
 
   Parameters
   ----------
   aws_conn_id
       Connection to use for connecting to AWS. Should have the appropriate
       permissions (Glue:StartCrawler and Glue:GetCrawler) in AWS.
   crawler_name
       Name of the crawler to trigger.
   region_name
       Name of the AWS region in which the crawler is located.
   kwargs
       Any kwargs are passed to the BaseOperator.
   """

    def __init__(
            self,
            aws_conn_id: str,
            crawler_name: str,
            region_name: str = None,
            max_wait_time=None,
            **kwargs
    ):
        super().__init__(**kwargs)
        self._aws_conn_id = aws_conn_id
        self._crawler_name = crawler_name
        self._region_name = region_name
        self._max_wait_time = max_wait_time

    def execute(self, context):
        hook = GlueJobHook(aws_conn_id=self._aws_conn_id, region_name=self._region_name)
        glue_client = hook.get_conn()

        self.log.info("Triggering crawler")
        response = glue_client.start_crawler(Name=self._crawler_name)

        if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
            raise RuntimeError(
                "An error occurred while triggering the crawler: %r" % response
            )

        self.log.info("Waiting for crawler to finish")

        current_retries = 0

        while True:

            crawler = glue_client.get_crawler(Name=self._crawler_name)
            crawler_state = crawler["Crawler"]["State"]

            if crawler_state == "READY":
                self.log.info("Crawler finished running")
                return crawler_state
                break

            if self._max_wait_time and current_retries >= self._max_wait_time:
                raise RuntimeError(
                    "An error occurred while triggering the crawler: %r" % response
                )

            current_retries += 1
            time.sleep(1)
