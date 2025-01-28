#!/bin/bash
set -euxo pipefail

PACKAGE_DIR="package"
ZIP_FILE="lambda_function.zip"

rm -rf $PACKAGE_DIR $ZIP_FILE
mkdir $PACKAGE_DIR

MSYS_NO_PATHCONV=1 docker run --rm --entrypoint /bin/bash \
  -v "$PWD":/var/task \
  -w /var/task \
  public.ecr.aws/lambda/python:3.12 \
  -c "pip install -r requirements.txt -t $PACKAGE_DIR"

cp todo.py $PACKAGE_DIR/
cd $PACKAGE_DIR
zip -r ../$ZIP_FILE .
cd ..
rm -rf $PACKAGE_DIR

echo "Success! Created $ZIP_FILE."