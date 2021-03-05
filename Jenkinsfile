pipeline {
    agent any
    options {
        timestamps()
        skipDefaultCheckout()
        disableConcurrentBuilds()
    }
    environment {
        project = "GastepoApiAutomation"
    }
    stages {
        stage("Set PATH") {
            when {
                environment name: "project", value: "GastepoApiAutomation"
            }
            steps {
                println "Now preparing Job No.${env.BUILD_ID} on ${env.NODE_NAME}"
                println "[Initial]: OS PATH refreshing..."
                sh "export PATH=/usr/lib64/qt-3.3/bin:/usr/kerberos/sbin:/usr/kerberos/bin:/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:/root/bin:/usr/local/python3/bin:/usr/local/git/bin:/root/bin:/usr/local/python3/bin:/backup/package/bin"
            }
        }
        stage("Run Test") {
            when {
                environment name: "project", value: "GastepoApiAutomation"
            }
            steps {
                    println "[Start]: Api Automation Test Running..."
                    sh "cd /automation/GastepoApiAutomation && python3 Run.py"
            }
        }
        stage("Generate Report") {
            when {
                environment name: "project", value: "GastepoApiAutomation"
            }
            steps {
                allure includeProperties: false, jdk: '', results: [[path: 'allure-result']]
                println "[End]: Test Report has been generated."
            }
        }
    }
    post {
        success {
            println "[Done]: Api Automation Test Done"
        }
    }
}