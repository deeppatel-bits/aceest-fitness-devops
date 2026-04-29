pipeline {
    agent any

    environment {
        IMAGE_NAME = "ghcr.io/deeppatel-bits/aceest-fitness"
        GIT_REPO   = "https://github.com/deeppatel-bits/aceest-fitness-devops.git"
    }

    stages {

        stage('Checkout') {
            steps {
                echo '>>> Cloning repository...'
                git branch: 'main', url: "${GIT_REPO}"
            }
        }

        stage('Install & Test') {
            agent {
                docker {
                    image 'python:3.9-slim'
                    reuseNode true
                }
            }
            steps {
                echo '>>> Installing dependencies and running tests...'
                sh '''
                    pip install flask pytest pytest-flask gunicorn --quiet
                    mkdir -p reports
                    pytest tests/ -v --tb=short --junitxml=reports/test-results.xml
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/test-results.xml'
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                echo '>>> Building Docker image...'
                sh """
                    docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} .
                    docker tag ${IMAGE_NAME}:${BUILD_NUMBER} ${IMAGE_NAME}:latest
                """
            }
        }

        stage('Push to Registry') {
            steps {
                echo '>>> Pushing image to GitHub Container Registry...'
                withCredentials([string(credentialsId: 'GITHUB_PAT', variable: 'PAT')]) {
                    sh """
                        echo \$PAT | docker login ghcr.io -u deeppatel-bits --password-stdin
                        docker push ${IMAGE_NAME}:${BUILD_NUMBER}
                        docker push ${IMAGE_NAME}:latest
                    """
                }
            }
        }
    }

    post {
        success {
            echo '>>> Pipeline completed successfully!'
        }
        failure {
            echo '>>> Pipeline failed! Check logs above.'
        }
        always {
            sh 'docker rmi ${IMAGE_NAME}:${BUILD_NUMBER} || true'
        }
    }
}