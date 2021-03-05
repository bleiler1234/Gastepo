### Description

> **框架简介：** Gastepo ~ 基于Schema DSL的E2E接口自动化测试框架

> **测试类型：** E2E接口自动化测试

***

### Feature

* **语言版本**：*Python 3.7*
* **集成IDE**：*PyCharm*
* **主要工具**：
  * 请求工具：*Requests*
  * 用例工具：*Pandas*
  * 测试框架：*Pytest*
  * 测试报告：*Allure*
  * 提取工具：*JsonPath*
  * 断言工具：*Hamcrest*
  * Web服务：*Flask*
  * Mock服务：*FastApi*
  * APM监控：*SkyWalking-H2*
* **部署方式**：*Docker*、*Jenkins Pipeline*、*Ubuntu VM*、*Local*

***

### Schema

- *Dependency Schema*

```json
[
    {
        "/v3_0/userInfo/searchContactUsers": {
            "to_path": {},
            "to_header": {},
            "to_param": {},
            "to_data": {
                "$['idCardNo']": "$.data[?(@.id==2001453)].idCard"
            }
        }
    }
]
```

- *Assert Schema*

```json
[
    {
        "actual": "$.data[:].id",
        "expect": [2001453],
        "matcher": "has_items",
        "alert": "未发现指定ID"
    }
]
```

***

### Test Runner

```ini
[pytest]
addopts = -s -q --alluredir=./Output/Result/Allure --disable-warnings
testpaths = ./TestSuite/TestMain
python_files = *Runner.py
python_classes = Test*
python_functions = test*
```

- **Auto Runtime**
  - *Step_1*：通过爬虫方式获取Swagger及Postman接口信息后自动合并生成测试用例。
  - *Step_2*：自动化测试用例支持全量或分组执行，单条用例支持激活或禁用。
  - *Step_3*：自动化测试用例使用Dependency Schema数据结构的接口间数据依赖。
  - *Step_4*：测试运行前自动清空Allure测试报告历史信息，并支持清空自动化测试用例上次运行痕迹。
  - *Step_5*：测试运行期间所有接口请求支持dispatch路由分发，可自动识别匹配接口请求方式。
  - *Step_6*：测试断言使用Assert Schema数据结构，其为JsonPath结合Hamcrest方式的自定义高级断言。
  - *Step_7*：测试结果统计使用Allure图形化测试报告，并支持自动更新用例执行结果。
  - *Step_8*：测试通知方式支持传统邮件推送和钉钉机器人消息提醒。

***

### Test Reporter

```shell
allure generate {json测试结果目录} -o {html测试报告目录} --clean
```

- <u>**Allure Test Report**</u>

![Allure测试报告](https://git.tasly.com/mente/api_business_automation/raw/develop/Common/Static/Doc/Allure.png)

***

### Test Deployment

- <u>**docker container**</u>

```shell
docker run --name automation -p 5000 -v {配置文件映射卷} -v {数据文件映射卷} qa/api-business-automation
```

***

### Wiki:

[Gastepo Wiki](http://10.6.0.116:11110)

***

### Measure

[![警报](http://10.16.168.61:9005/api/project_badges/measure?project=Gastepo&metric=alert_status)](http://10.16.168.61:9005/dashboard?id=Gastepo)[![SQALE评级](http://10.16.168.61:9005/api/project_badges/measure?project=Gastepo&metric=sqale_rating)](http://10.16.168.61:9005/dashboard?id=Gastepo)[![覆盖率](http://10.16.168.61:9005/api/project_badges/measure?project=Gastepo&metric=coverage)](http://10.16.168.61:9005/dashboard?id=Gastepo)

[^QA]: 583512498@qq.com
