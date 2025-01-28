import * as cdk from "aws-cdk-lib";
import * as ddb from "aws-cdk-lib/aws-dynamodb";
import * as lambda from "aws-cdk-lib/aws-lambda";
import { Construct } from "constructs";

export class TodoInfraStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create DDB table to store the tasks
    const table = new ddb.Table(this, "Tasks", {
      partitionKey: { name: "task_id", type: ddb.AttributeType.STRING },
      billingMode: ddb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: "ttl",
    });

    // Add GSI based on user_id (lets us query data with a different key than main table)
    // Enables finding tasks by specific user, sorting tasks by creation time
    // Speeds up query time
    table.addGlobalSecondaryIndex({
      indexName: "user-index",
      partitionKey: { name: "user_id", type: ddb.AttributeType.STRING },
      sortKey: { name: "created_time", type: ddb.AttributeType.NUMBER },
    });

    // Create Lambda function for API
    const api = new lambda.Function(this, "API", {
      runtime: lambda.Runtime.PYTHON_3_12,
      code: lambda.Code.fromAsset("../api/lambda_function.zip"),
      handler: "todo.handler",
      environment: {
        TABLE_NAME: table.tableName,  // lambda function's environ. var. set to name of dynamoDB table
      },
    });

    // Create a function URL (API endpoint) which triggers the lambda function
    const functionUrl = api.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.NONE,
      cors: {
        allowedOrigins: ["*"],
        allowedMethods: [lambda.HttpMethod.ALL],
        allowedHeaders: ["*"],
      },
    });
    
    // Output the url of API function to terminal
    new cdk.CfnOutput(this, "APIUrl", {
      value: functionUrl.url,
    });

    // Give Lambda permissions to read/write to table
    table.grantReadWriteData(api);
  }
}
