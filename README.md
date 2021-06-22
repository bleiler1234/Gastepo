### Description

> **框架简介：** Gastepo ~ 基于Schema DSL语法规约的接口自动化测试框架

> **测试类型：** 接口自动化测试

***

### Feature

* **开发语言**：*Python 3.7*
* **开发环境**：*PyCharm*
* **开发工具**：
  * 测试框架：*Pytest*
  * 测试报告：*Allure*
  * 数据处理：*Pandas*
  * 请求工具：*Requests*
  * 响应获取：*JsonPath*
  * 断言工具：*Hamcrest*
  * 单元测试：*Unittest*、*Coverage*
  * 代码扫描：*SonarQube*
  * Web服务：*Flask*、*FastApi*
  * 部署方式：*Docker*、*Jenkins*

***

### Framework

<img src="https://i.loli.net/2021/04/26/qsx8IdGPyQKc5fp.png" alt="Framework.png" style="zoom:55%;" />

***


### Schema

- *Dependency Schema*

```json
[
    {
        "GET /v3_0/userInfo/searchContactUsers": {
            "to_path": {},
            "to_header": {},
            "to_param": {},
            "to_data": {
                "$['idCardNo']": {
                  	"GET /v3_0/getCardId": {
                      	"response": {
                          	"data": "$.data.cardId"
                        }
                    }
                }
            }
        }
    }
]
```

- *Assertion Schema*

```json
[
    {
        "actual": "$.data[:].cardId",
        "expect": [
          {
            "${fetchCardId(user)}": {
              "user": {
                "GET /v3_0/getUserName": {
                  	"response": {
                      	"data": "$.userName"
                    }
                }
              }
            }
          }
        ],
        "matcher": "has_item",
        "alert": "未发现指定用户标签ID",
        "multi": false
    }
]
```

***

### Test Runner

```ini
[pytest]
addopts = -s -q --alluredir=./Common/Static/Result/Allure --disable-warnings
testpaths = ./Executor/Mente
python_files = *Runner.py
python_classes = Test*
python_functions = test*
```

- **Automation Runtime**
    - *Step_1*：自动分析指定扫描文件夹中所有Postman接口集合并聚合生成表格用例文件。
    - *Step_2*：自动化测试用例支持用例筛选及BDD方式执行，单条用例支持激活或禁用。
    - *Step_3*：自动化测试用例使用Dependency Schema规约结构的接口请求数据依赖。
    - *Step_4*：自动化测试用例使用Assertion Schema规约结构的接口信息高级断言。
    - *Step_5*：自动化测试运行支持前置清空历史测试数据，包括测试结果、用例结果等。
    - *Step_6*：自动化测试运行的所有接口通过dispatch路由分发，可自动识别请求信息并注入依赖数据。
    - *Step_7*：自动化测试报告使用Allure，并支持表格用例自动更新、接口信息实时录制、报告实时截图。
    - *Step_8*：自动化测试推送通知方式支持传统邮件推送和钉钉机器人消息提醒。
    - *Step_9*：自动化测试部署方式支持Jenkins流水线及Docker容器托管运行方式。

***

### Test Reporter

```shell
allure generate {json测试结果目录} -o {html测试报告目录} --clean
```

- <u>**Allure Test Report**</u>

<img src="https://i.loli.net/2021/04/22/9XmosLQtigcSv34.png" alt="Allure测试报告" style="zoom:40%;" />

***

### Test Deployment

- <u>**Docker Container**</u>

```shell
docker run -itd --name gastepo -p 端口号 -v {配置文件映射卷} -v {数据文件映射卷} automation/gastepo
```

- <u>**Jenkins Pipeline**</u>

```groovy
pipeline {
    agent any
    options {
        可选项配置
    }
    stages {
         stage("Pull From GitLab") {
        		拉取指定Git分支源码
        }
        stage("Set PATH") {
            设置Python3依赖信息
        }
        stage("Run Test") {
            执行自动化测试
        }
        stage("Generate Report") {
            报告生成及结果推送
    }
    post {
        success {
            println "[Done]: Gastepo Test Done"
        }
    }
}
```

***

### Wiki:

Get me on [GitHub](https://github.com/bleiler1234/gastepo)

***

### Measure

[![警报](http://10.16.168.70:9005/api/project_badges/measure?project=TaslyAutoTest&metric=alert_status)](http://10.16.168.70:9005/dashboard?id=TaslyAutoTest)[![SQALE评级](http://10.16.168.70:9005/api/project_badges/measure?project=TaslyAutoTest&metric=sqale_rating)](http://10.16.168.70:9005/dashboard?id=TaslyAutoTest)[![覆盖率](http://10.16.168.70:9005/api/project_badges/measure?project=TaslyAutoTest&metric=coverage)](http://10.16.168.70:9005/dashboard?id=TaslyAutoTest)

[^QA]: 583512498@qq.com

