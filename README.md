# Serverless Title Parsing

Requirements ::

* Python3.7
* Node.js v6.5.0 or later.

Steps ::

* Clone repository
* Install serverless :: ```npm install -g serverless```
* Set up aws credentials on your AWS account.
* Configure them for serverless :: ```serverless config credentials --provider aws --key XXXXXXXXXXX --secret XXXXXXXXXXX```
* Deploy application :: ```serveless deploy```
* Run command to getch title of webpage :: 
```serverless invoke -f async_parse_title -l --data "https://google.com"
serverless invoke -f get_processed_title -l --data "<ID retruned from the first command>"
```
