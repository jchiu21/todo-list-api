import os
import time
from boto3.dynamodb.conditions import Key
import boto3
from uuid import uuid4
from fastapi import FastAPI, HTTPException
from mangum import Mangum
from pydantic import BaseModel
from typing import Optional

app = FastAPI()
# Mangum is an adapter that converts Lambda functionUrl events into ASGI-compatible requests 
# that fastAPI can handle. And converts FastAPI's ASGI responses back into a format Lambda can understand
handler = Mangum(app) 

class PutTaskRequest(BaseModel):
    content: str
    user_id: Optional[str] = None
    task_id: Optional[str] = None
    is_done: bool = False


@app.get("/")
def root():
    return {"message": "Hello World from Todo API"}


@app.put("/create-task")
async def create_task(put_task_request: PutTaskRequest):
    created_time = int(time.time())
    item = {
        "user_id": put_task_request.user_id,
        "content": put_task_request.content,
        "is_done": False,
        "created_time": created_time,
        "task_id": f"task_{uuid4().hex}",
        "ttl": int(created_time + 86400), # Expire after 24 hours
    }
    table = _get_table()
    table.put_item(Item=item)
    return {"task": item}
    

@app.get("/get-task/{task_id}")
async def get_task(task_id: str):
    table = _get_table()
    # response object contains metadata about operation, and the actual item 
    # inside key "Item"
    response = table.get_item(Key={"task_id": task_id})
    item = response.get("Item")
    
    if not item:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return item


@app.get("/list-tasks/{user_id}")
async def create_task(user_id: str):
    table = _get_table()
    response = table.query(
        IndexName="user-index",  # specify index name for GSI query
        KeyConditionExpression=Key("user_id").eq(user_id),
        ScanIndexForward=False,  # items returned in descending order based on sort key
        Limit=10,    # limits items returned to 10
    )
    items = response.get("Items")
    return {"tasks": items}


@app.put("/update-task")
async def update_task(put_task_request: PutTaskRequest):
    table = _get_table()
    table.update_item(
        Key={"task_id": put_task_request.task_id},  # partition key
        # SET keyword to set value of attributes, :content and :is_done are placeholders
        # to be susbstituted from ExpressionAttributeValues
        UpdateExpression="SET content = :content, is_done = :is_done",
        ExpressionAttributeValues={
            ":content": put_task_request.content,
            ":is_done": put_task_request.is_done
        },
        ReturnValues="ALL_NEW", # returns entire updated item
    )    
    return {"updated_task_id": {put_task_request.task_id}}


@app.delete("/delete-task/{task_id}")
async def delete_task(task_id: str):
    table = _get_table()
    table.delete_item(Key={"task_id": task_id})
    return {"deleted_task_id": task_id}


# helper function for getting table resource object
def _get_table():
    table_name = os.environ.get("TABLE_NAME")    # get the table name env. variable
    # Initializes a DynamoDB resource object, fetches the table resource object
    return boto3.resource("dynamodb").Table(table_name) 