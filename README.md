# Serverless Title Parsing

Requirements ::

* Python3.7
* Node.js v6.5.0 or later.

Steps ::

* Install serverless :: ```npm install -g serverless```
* Clone repository and ```cd service```
* Run command to install plugin:: ```sls plugin install -n serverless-python-requirements```
* Set up aws credentials on your AWS account.
* Configure the above credentials for serverless :: ```serverless config credentials --provider aws --key XXXXXXXXXXX --secret XXXXXXXXXXX```
* Deploy application :: ```serveless deploy```
* Run below commands to fetch title of webpage :: 
```
serverless invoke -f async_parse_title -l --data "https://google.com"
serverless invoke -f get_processed_title -l --data "<ID retruned from the first command>"
```
