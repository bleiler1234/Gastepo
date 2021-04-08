pipeline {
    agent any
    options {
        timestamps()
        skipDefaultCheckout()
        disableConcurrentBuilds()
    }
    environment {
        project = "Gastepo"
    }

    stages {
         stage("Pull From GitLab") {
            when {
                environment name: "project", value: "Gastepo"
            }
            steps {
                println "[Start]: Gastepo Pull From GitLab..."
                git branch: 'develop', credentialsId: '8b8ba582-6559-41aa-860b-e5335d9f54b6', url: 'https://git.qa.com/Gastepo.git'
            }
        }
        stage("Set PATH") {
            when {
                environment name: "project", value: "Gastepo"
            }
            steps {
                println "Now preparing Job No.${env.BUILD_ID} on ${env.NODE_NAME}"
                println "[Initial]: OS PATH refreshing..."
                sh "export PATH=/usr/lib64/qt-3.3/bin:/usr/kerberos/sbin:/usr/kerberos/bin:/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:/root/bin:/usr/local/python3/bin:/usr/local/git/bin:/root/bin:/usr/local/python3/bin:/backup/package/bin"
            }
        }
        stage("Run Test") {
            when {
                environment name: "project", value: "Gastepo"
            }
            steps {
                    println "[Start]: Gastepo Test Running..."
                    sh "cd ${WORKSPACE} && /usr/local/python3/bin/python3 Run.py"
            }
        }
        stage("Generate Report") {
            when {
                environment name: "project", value: "Gastepo"
            }
            steps {
                allure includeProperties: false, jdk: '', results: [[path: 'allure-results']]
                println "[End]: Test Report has been generated."
            }
        }
    }
    post {
        success {
            println "[Done]: Gastepo Test Done"
        }
    }
}