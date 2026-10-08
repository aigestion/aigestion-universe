"""Temporal test worker for Daniela"""
import asyncio

from temporalio import workflow
from temporalio.client import Client
from temporalio.worker import Worker


@workflow.defn
class TestWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        return f"Hello, {name}!"


async def main():
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue="test-queue",
        workflows=[TestWorkflow],
    )
    print("Worker started, waiting for workflows...")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
